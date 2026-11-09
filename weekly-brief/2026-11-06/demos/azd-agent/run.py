# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "azure-ai-projects>=2.4.0,<3",
#   "azure-identity>=1.25.0,<2",
#   "python-dotenv>=1.2.0,<2",
# ]
# ///
"""Invoke a deployed Microsoft Foundry hosted agent; never replay captures."""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential
from dotenv import dotenv_values

DEFAULT_PROMPT = "Write a haiku about deploying cloud applications."


def redact(text: str) -> str:
    """Remove credential-shaped and personal identifiers from diagnostics."""
    text = re.sub(r"(?i)\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", "<redacted-id>", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "<redacted-email>", text)
    return re.sub(r"(?i)Bearer\s+[A-Za-z0-9._-]+", "Bearer <redacted-token>", text)


def main() -> int:
    """Resolve deployment configuration, invoke once, and report elapsed time."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print exactly one JSON object.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    args = parser.parse_args()
    start = time.perf_counter()
    result = {
        "ok": False,
        "prompt": args.prompt,
        "output_text": "",
        "latency_ms": 0,
        "agent": "",
        "endpoint_host": "",
    }
    try:
        demo_root = Path(__file__).resolve().parent
        values = {
            **dotenv_values(demo_root / ".env"),
            **dotenv_values(demo_root.parents[1] / ".env"),
            **os.environ,
        }
        endpoint = values.get("AZD_AGENT_PROJECT_ENDPOINT", "")
        agent = values.get("AZD_AGENT_NAME", "")
        result["agent"] = agent or ""
        if not endpoint or not agent:
            raise ValueError(
                "Set AZD_AGENT_PROJECT_ENDPOINT and AZD_AGENT_NAME in the process "
                "environment, deck .env, or demos/azd-agent/.env."
            )
        parsed = urlparse(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith(".services.ai.azure.com")
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith("/api/projects/")
        ):
            raise ValueError("AZD_AGENT_PROJECT_ENDPOINT must be a public Foundry project HTTPS endpoint.")
        result["endpoint_host"] = parsed.hostname
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", agent):
            raise ValueError("AZD_AGENT_NAME must be a lowercase kebab-case agent name.")
        if not args.prompt.strip():
            raise ValueError("The prompt must not be empty.")
        with AzureCliCredential(process_timeout=30) as credential:
            with AIProjectClient(endpoint=endpoint, credential=credential) as project:
                with project.get_openai_client(
                    base_url=f"{endpoint.rstrip('/')}/agents/{agent}/endpoint/protocols/openai",
                    default_query={"api-version": "v1"},
                    max_retries=0,
                ) as client:
                    completed = False
                    with client.responses.create(
                        input=args.prompt,
                        stream=True,
                        timeout=90,
                    ) as events:
                        for event in events:
                            if event.type == "response.output_text.delta":
                                result["output_text"] += event.delta
                            elif event.type == "response.failed":
                                raise RuntimeError(f"Hosted response failed: {event.response.error}")
                            elif event.type == "error":
                                raise RuntimeError(f"Hosted response error: {event.message}")
                            elif event.type == "response.completed":
                                completed = True
                            elif event.type == "response.incomplete":
                                raise RuntimeError("The hosted response was incomplete.")
                    if not completed:
                        raise RuntimeError("The hosted response stream ended before completion.")
        if not result["output_text"]:
            raise RuntimeError("The deployed agent returned no text.")
        result["ok"] = True
    except Exception as exc:
        result["error"] = redact(f"{type(exc).__name__}: {exc}")
    result["latency_ms"] = round((time.perf_counter() - start) * 1000)
    if args.json:
        print(json.dumps(result, ensure_ascii=True))
    elif result["ok"]:
        print(result["output_text"])
        print(f"\n{result['agent']} | {result['latency_ms']} ms", file=sys.stderr)
    else:
        print(result["error"], file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
