"""Create and rehearse the two prompt agents in the approved livestream project."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from collections.abc import Iterator

from azure.ai.projects.models import (
    MicrosoftCopilotHarness,
    PromptAgentDefinition,
    Reasoning,
    SkillInlineContent,
    SkillReference,
)
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")


def get_project_client(*, allow_preview: bool = False) -> AIProjectClient:
    """Create the local demo client using the developer's Entra credentials."""
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "").strip()
    if not endpoint or "<" in endpoint or "your-resource" in endpoint:
        raise ValueError("Set AZURE_AI_PROJECT_ENDPOINT in copilot-harness/.env to your Foundry project URL.")
    if not endpoint.startswith("https://") or "/api/projects/" not in endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT must be an HTTPS Foundry project URL containing /api/projects/.")
    return AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=allow_preview)

MODEL = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-6-luna")
AGENTS = {
    "default": os.environ.get("DEFAULT_AGENT_NAME", "livestream-recipe-default-1102"),
    "copilot": os.environ.get("COPILOT_AGENT_NAME", "livestream-recipe-copilot-1102"),
}
SKILL_NAME = "livestream-cookbook-review-1102"
INSTRUCTIONS = (
    "You author concise Microsoft Foundry recipe notebooks. Follow the user's task "
    "and report only checks actually performed. Never execute generated notebook "
    "cloud calls, install packages, create resources, or open a pull request. "
    "If you have workspace tools, write requested artifacts, validate their JSON and "
    "Python syntax, and use an independent reviewer if available. Use the published "
    "cookbook-review skill when available. Fetch the official Learn guidance at "
    "https://learn.microsoft.com/azure/foundry/openai/how-to/responses before "
    "authoring if web fetching is available. If no file tools exist, return the "
    "notebook and review content as text and disclose that no file or syntax check ran. "
    "When file output is available, return the notebook and review as downloadable files."
)


def shared_task() -> str:
    """Return the unchanged fenced task shared with the hosted implementations."""
    source = (HERE / "shared-task.md").read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)\n```", source, re.DOTALL)
    if not match:
        raise ValueError("shared-task.md must contain one text fence.")
    return match.group(1)


def create_agent(client: Any) -> dict[str, Any]:
    """Create only the new livestream agents and their immutable review skill."""
    skill = client.beta.skills.create(
        name=SKILL_NAME,
        inline_content=SkillInlineContent(
            description="Review a Foundry recipe against the eleven-axis rubric.",
            instructions=(HERE / "skills" / "cookbook-review" / "SKILL.md").read_text(),
        ),
    )
    created = {}
    for lane, name in AGENTS.items():
        extra = {}
        if lane == "copilot":
            extra = {
                "harness": MicrosoftCopilotHarness(),
                "skills": [SkillReference(name=SKILL_NAME, version=skill.version)],
            }
        agent = client.agents.create_version(
            agent_name=name,
            definition=PromptAgentDefinition(model=MODEL, instructions=INSTRUCTIONS,
                                             reasoning=Reasoning(summary="auto"), **extra),
            description="Livestream recipe comparison; isolated demo agent.",
        )
        created[lane] = {"name": agent.name, "version": agent.version}
    return created


def setup_continuous_evaluation(client: Any) -> list[dict[str, Any]]:
    """Return standard evaluator intent; do not silently create cloud evaluations."""
    return [
        {"type": "azure_ai_evaluator", "name": name, "evaluator_name": f"builtin.{name}",
         "data_mapping": {"response": "{{item.response}}", "query": "{{item.query}}"},
         "initialization_parameters": {"deployment_name": MODEL}}
        for name in ["coherence", "relevance", "task_adherence"]
    ]


class HarnessRateLimitError(RuntimeError):
    """Keep the conversation key when a real run hits the model token quota."""

    def __init__(self, conversation_id: str, message: str) -> None:
        super().__init__(message)
        self.conversation_id = conversation_id


def _stream_agent_once(client: Any, lane: str, query: str, conversation_id: str | None = None) -> Iterator[dict[str, Any]]:
    """Yield real tool/text events and the final measured Responses result."""
    with client.get_openai_client(agent_name=AGENTS[lane], timeout=580, max_retries=0) as openai:
        conversation_id = conversation_id or openai.conversations.create().id
        started = time.monotonic()
        yield {"type": "start", "lane": lane, "conversation_id": conversation_id}
        events: list[str] = []
        final = None
        with openai.responses.create(input=query, conversation=conversation_id, stream=True) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    yield {"type": "delta", "text": event.delta}
                elif event.type == "response.created":
                    yield {"type": "step", "name": "response_created", "detail": "Response created."}
                elif event.type == "response.reasoning_summary_part.added":
                    yield {"type": "reasoning", "state": "start"}
                elif event.type == "response.reasoning_summary_text.delta":
                    yield {"type": "reasoning", "state": "delta", "text": event.delta}
                elif event.type == "response.reasoning_summary_text.done":
                    yield {"type": "reasoning", "state": "done"}
                elif event.type in ("response.output_item.added", "response.output_item.done"):
                    item = event.item.model_dump(mode="json")
                    if item.get("type") == "reasoning" and event.type.endswith(".added"):
                        yield {"type": "reasoning", "state": "start"}
                    elif item.get("type") not in ("message", "reasoning"):
                        name = str(item.get("name") or item.get("type"))
                        phase = "completed" if event.type.endswith(".done") else "started"
                        if phase == "completed":
                            events.append(name)
                        yield {"type": "tool", "name": name, "detail": phase}
                elif event.type == "response.completed":
                    final = event.response
                elif event.type in ("response.failed", "response.incomplete", "error"):
                    detail = getattr(getattr(event, "response", None), "error", None)
                    if getattr(detail, "code", None) == "rate_limit_exceeded":
                        raise HarnessRateLimitError(conversation_id, "The model deployment token quota was exceeded.")
                    raise RuntimeError(
                        f"Agent stream did not complete: {event.type}; "
                        f"code={getattr(detail, 'code', None)}; "
                        f"message={getattr(detail, 'message', None)}"
                    )
        if final is None:
            raise RuntimeError("The stream ended without a completed response.")
        raw = final.model_dump(mode="json")
        for item in raw.get("output", []):
            if item.get("type") == "reasoning":
                item.pop("encrypted_content", None)
                item.pop("content", None)
        text = "\n\n".join(
            part.get("text", "")
            for item in raw.get("output", [])
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        )
        files: list[dict[str, str]] = []
        for item in raw.get("output", []):
            for part in item.get("content", []):
                for annotation in part.get("annotations", []):
                    if annotation.get("file_id"):
                        files.append({
                            "id": annotation["file_id"],
                            "name": Path(annotation.get("filename") or annotation["file_id"]).name,
                        })
        known_ids = {file["id"] for file in files}
        for file_id in dict.fromkeys(re.findall(r"\bassistant-[A-Za-z0-9]+\b", text)):
            if file_id not in known_ids:
                with client.get_openai_client(timeout=30, max_retries=0) as file_client:
                    metadata = file_client.files.retrieve(file_id)
                files.append({"id": file_id, "name": Path(metadata.filename).name})
                known_ids.add(file_id)
        usage = raw.get("usage") or {}
        input_rate = os.environ.get("INPUT_USD_PER_MILLION")
        output_rate = os.environ.get("OUTPUT_USD_PER_MILLION")
        cost = None
        if input_rate and output_rate:
            cost = (usage.get("input_tokens", 0) * float(input_rate)
                    + usage.get("output_tokens", 0) * float(output_rate)) / 1_000_000
        yield {"type": "result", "result": {
            "mode": "live", "text": text, "raw": raw,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "usage": usage, "cost_usd": cost, "events": events,
            "files": files, "conversation_id": conversation_id,
        }}


def stream_agent(client: Any, lane: str, query: str, conversation_id: str | None = None) -> Iterator[dict[str, Any]]:
    """Pace at most two quota recoveries, visibly continuing the same workspace."""
    started = time.monotonic()
    first_text_ms = None
    for attempt in range(3):
        try:
            for event in _stream_agent_once(client, lane, query, conversation_id):
                event["at_ms"] = round((time.monotonic() - started) * 1000)
                if event["type"] == "delta" and first_text_ms is None:
                    first_text_ms = event["at_ms"]
                if event["type"] == "result":
                    event["result"]["elapsed_ms"] = round((time.monotonic() - started) * 1000)
                    event["result"]["quota_retries"] = attempt
                    event["result"]["first_text_ms"] = first_text_ms
                    event["result"]["usage_note"] = (
                        "Final response usage only; failed-attempt usage is unavailable."
                        if attempt else "Completed response usage."
                    )
                yield event
            return
        except HarnessRateLimitError as error:
            if attempt == 2:
                raise
            yield {"type": "step", "name": "quota_wait",
                   "detail": "Rate limit reached. Waiting 65 seconds, then continuing the same conversation. No recording substituted."}
            time.sleep(65)
            conversation_id = error.conversation_id
            query = "Continue the original user request from the existing conversation workspace. Do not start over. Report only work actually performed and return only the requested output."


def query_agent(client: Any, lane: str, query: str, conversation_id: str | None = None) -> dict[str, Any]:
    """Consume the same streaming path for CLI and recording capture."""
    for event in stream_agent(client, lane, query, conversation_id):
        if event["type"] == "result":
            return event["result"]
    raise RuntimeError("The agent ended without a final result.")


def save_recording(client: Any, lane: str, result: dict[str, Any]) -> None:
    """Persist only a real completed response and its returned files."""
    for file in result["files"]:
        with client.get_openai_client() as openai:
            content = openai.files.content(file["id"]).read()
        target = HERE / "public" / "recordings" / "files" / file["name"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    target = HERE / "public" / "recordings" / f"{lane}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({**result, "mode": "recorded"}, indent=2), encoding="utf-8")


def main() -> None:
    """Create agents, run a compatibility probe, or capture a real recording."""
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create", "probe", "record"])
    parser.add_argument("--lane", choices=list(AGENTS), default="copilot")
    args = parser.parse_args()
    with get_project_client(allow_preview=True) as client:
        if args.action == "create":
            print(json.dumps(create_agent(client)))
        else:
            result = query_agent(client, args.lane, "Reply with HARNESS_OK only." if args.action == "probe" else shared_task())
            if args.action == "record":
                save_recording(client, args.lane, result)
            print(json.dumps({"text": result["text"], "events": result["events"], "files": result["files"]}))


if __name__ == "__main__":
    main()
