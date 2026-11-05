"""Generate clearly synthetic offline UI fixtures, never service evidence."""

import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def main() -> None:
    source = (HERE / "shared-task.md").read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)\n```", source, re.DOTALL)
    if not match:
        raise ValueError("shared-task.md must contain a text fence.")
    public = HERE / "public"
    recordings = public / "recordings"
    recordings.mkdir(parents=True, exist_ok=True)
    (public / "task.json").write_text(json.dumps({"prompt": match.group(1)}), encoding="utf-8")
    for lane in ["default", "copilot", "hosted-sdk", "hosted-maf"]:
        result = {
            "mode": "synthetic",
            "text": (
                "Synthetic interface example. No model was called and no notebook was generated.\n\n"
                "A live author would draft a notebook, check JSON and Python syntax, and report "
                "which checks actually ran. This fixture illustrates the chat layout only."
            ),
            "elapsed_ms": 0,
            "usage": {},
            "cost_usd": None,
            "events": [],
            "files": [],
            "transport": "synthetic",
            "usage_note": "No measured latency, tokens, cost, tools, or artifacts.",
            "raw": {"status": "illustration", "synthetic": True, "lane": lane},
        }
        (recordings / f"{lane}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
