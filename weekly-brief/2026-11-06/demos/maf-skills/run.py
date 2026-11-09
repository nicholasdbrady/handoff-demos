# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "agent-framework-foundry==1.16.1",
#   "agent-framework-core==1.25.0",
#   "azure-identity==1.27.0",
#   "python-dotenv==1.2.4",
# ]
# ///
"""Run the generated function-tool example with a JSON result."""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from generated_app import add as generated_add

PROMPT = "Use your tool to add 19 and 23."


async def run() -> dict:
    """Call the Foundry model and record calls to the generated tool."""
    load_dotenv(Path.cwd() / ".env", override=False)
    model = os.environ.get("FOUNDRY_MODEL", "")
    started = time.monotonic()
    calls = []

    def add(a: int, b: int) -> int:
        """Return the sum of two integers."""
        result = generated_add(a, b)
        calls.append({"name": "add", "arguments": {"a": a, "b": b}, "result": result})
        return result

    try:
        if not os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or not model:
            raise ValueError("Set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL.")
        async with AzureCliCredential() as credential:
            async with FoundryChatClient(credential=credential) as client:
                agent = Agent(
                    client=client,
                    name="AdditionAgent",
                    instructions="Use the add tool for addition. Keep your answer brief.",
                    tools=[add],
                    default_options={"store": False},
                )
                response = await agent.run(PROMPT)
        if not calls:
            raise RuntimeError("The model did not call the add tool.")
        return {
            "ok": True,
            "prompt": PROMPT,
            "output_text": str(response),
            "tool_calls": calls,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "model": model,
        }
    except Exception as exc:
        print(f"Live run failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return {
            "ok": False,
            "prompt": PROMPT,
            "output_text": "",
            "tool_calls": calls,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "model": model,
            "error": type(exc).__name__,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print one JSON object.")
    args = parser.parse_args()
    result = asyncio.run(run())
    if args.json:
        print(json.dumps(result, ensure_ascii=True))
    elif result["ok"]:
        print(result["output_text"])
    else:
        print(f"Live run failed: {result['error']}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
