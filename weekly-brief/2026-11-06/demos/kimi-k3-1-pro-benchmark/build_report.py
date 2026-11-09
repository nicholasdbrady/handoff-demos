"""Build a self-contained slide visual from observed, automatically graded trials."""

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parents[1] / "public" / "demos" / "kimi-k3-1-pro-benchmark"
BASE = "/demos/kimi-k3-1-pro-benchmark/"

CAVEATS = [
    "This is a bespoke functional benchmark, not a standard leaderboard evaluation. Three seeded tasks are a small sample; the common public code corpus is shared.",
    "Every route has a complete valid text chain. The image alone reveals route capacities, risks, and the active epoch; stale records must be excluded.",
    "The source corpus is real committed public Azure SDK code. The routing/dispatch/change/release records are explicitly fictional planted fixtures, not Azure facts.",
    "Input size is measured by the service, not inferred from file length. The local cl100k estimate is not Kimi's tokenizer.",
    "No tools, repository search, code execution, retries, answer repair, or recorded fallback were available to the model.",
    "The 11 answers are exact value-and-type graded. Extra JSON keys fail a trial. Source facts are independently derived with Python AST and Markdown parsing.",
    "Latency includes Entra credential setup, upload, generation, and grading. Calls are sequential, not a throughput test. No baseline model was tested.",
    "Costs are conservative uncached estimates at Nov 5 USD announcement prices ($2.30/M input and $11.50/M output), not an invoice. Reasoning is included in output tokens.",
    "Nov 9 catalog and Learn label K3.1 Pro GA. The supplied weekly draft said preview; lifecycle status by the Nov 6 12:01 PST cutoff remains unverified.",
    "The management deployment is Kimi-K3.1-Pro version 2026-11-04; the inference response calls itself Kimi-K3.1. Both identities are preserved.",
]
SOURCES = [
    {"url": "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292", "date": "2026-11-05", "retrieved": "2026-11-09", "quote": "text and image understanding and a context window of up to 1 million tokens"},
    {"url": "https://ai.azure.com/catalog/models/Kimi-K3.1-Pro", "retrieved": "2026-11-09", "quote": "Lifecycle Generally available (GA); Context window 1048.576k"},
    {"url": "https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule#foundry-models-sold-by-azure", "retrieved": "2026-11-09", "quote": "Kimi-K3.1-Pro | 2026-11-04 | GA | 2027-11-04"},
]


def build() -> dict:
    """Do not inflate the pass denominator by dropping failed attempts."""
    trials = [
        json.loads((PUBLIC / f"trial-{i}.json").read_text(encoding="utf-8"))
        for i in [1, 2, 3]
    ]
    passes = sum(r["ok"] and r["correct"] for r in trials)
    size_met = all(r.get("minimum_200k_input_met") for r in trials)
    successful = [r for r in trials if r["ok"]]
    items_correct = sum(r.get("grading", {}).get("correct_count", 0) for r in trials)
    known_costs = [r["estimated_cost_usd"] for r in trials if r.get("estimated_cost_usd") is not None]
    metrics = {
        "attempts": len(trials), "passes": passes, "pass_rate": passes / len(trials),
        "items_correct": items_correct, "items_total": len(trials) * 11,
        "input_tokens_each": [r["input_tokens"] for r in trials],
        "total_tokens_each": [r["total_tokens"] for r in trials],
        "latency_ms_each": [r["latency_ms"] for r in trials],
        "median_latency_ms": statistics.median(r["latency_ms"] for r in successful) if successful else None,
        "estimated_cost_usd": round(sum(known_costs), 6) if len(known_costs) == len(trials) else None,
        "known_cost_estimate_subtotal_usd": round(sum(known_costs), 6),
        "trials_without_cost_usage": len(trials) - len(known_costs),
        "minimum_200k_input_met_all_trials": size_met,
    }
    report = {
        "captured_at": max(r["captured_at"] for r in trials),
        "trials": trials, "metrics": metrics,
        "caveats": CAVEATS, "sources": SOURCES,
        "parameters": {"reasoning_effort": "high", "max_completion_tokens": 4096, "timeout_seconds": 180, "retries": 0},
    }
    (PUBLIC / "recorded-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    assets = [
        {"path": BASE + "recorded-results.json", "kind": "json", "caption": "All three attempted calls and exact grading", "alt": "Pass counts, tokens, latency, raw answers and expected values."},
        {"path": BASE + "benchmark.html", "kind": "text", "caption": "Self-contained slide-ready benchmark visual", "alt": "Large code, image routing, distributed joins, and exact graded outcomes."},
    ]
    for i in [1, 2, 3]:
        assets.extend([
            {"path": BASE + f"input-{i}.png", "kind": "image", "caption": f"Actual image input, trial {i}", "alt": "Three routes with capacities, risks, dispatch tickets, and active epoch."},
            {"path": BASE + f"provenance-{i}.json", "kind": "json", "caption": f"Pinned public source and fixture positions, trial {i}", "alt": "Source commit, corpus hash, and distributed fixture offsets."},
        ])
    for name, kind, caption, alt in [
        ("overview.png", "image", "Verified 1280 x 720 toolbar-safe benchmark overview", "Actual browser capture with essential content and evidence controls above 620px."),
        ("browser-validation.json", "json", "Recorded browser layout and sandbox checks", "Desktop fit, mobile width, 24px labels, and opaque-origin sandbox behavior."),
    ]:
        if (PUBLIC / name).is_file():
            assets.append({"path": BASE + name, "kind": kind, "caption": caption, "alt": alt})
    manifest = {
        "slug": "kimi-k3-1-pro-benchmark",
        "title": "Kimi K3.1 Pro: 373K-token visual and code benchmark",
        "status": "ready" if passes == len(trials) and size_met else "partial",
        "captured_at": report["captured_at"],
        "environment": {
            "region": "eastus",
            "models/deployments": [{"model": "Kimi-K3.1-Pro", "version": "2026-11-04", "deployment": "kimi-k3-1-pro", "sku": "GlobalStandard", "capacity": 1000}],
            "tool_versions": {"azure_cli": "2.92.0", "uv": "0.12.0", "ibm_plex_sans": "5.3.0"},
        },
        "assets": assets, "metrics": metrics,
        "live": {"supported": bool(successful), "command": "uv run demos/kimi-k3-1-pro-benchmark/run.py --json --trial 1 --effort high --max-tokens 4096", "typical_seconds": metrics["median_latency_ms"] / 1000 if successful else None},
        "preview": BASE + "benchmark.html",
        "sandbox": "Self-contained authored HTML; can be embedded with sandbox=allow-scripts. No fetch, external fonts, credentials, or model access.",
        "caveats": CAVEATS, "sources": SOURCES,
    }
    (PUBLIC / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    template = (ROOT / "visual-template.html").read_text(encoding="utf-8")
    regular = base64.b64encode((PUBLIC / "fonts" / "ibm-plex-sans-latin-400-normal.woff2").read_bytes()).decode()
    bold = base64.b64encode((PUBLIC / "fonts" / "ibm-plex-sans-latin-700-normal.woff2").read_bytes()).decode()
    image = base64.b64encode((PUBLIC / "input-1.png").read_bytes()).decode()
    oracle = json.loads((ROOT / "oracle-1.json").read_text(encoding="utf-8"))
    if oracle["expected"] != trials[0].get("expected"):
        raise ValueError("The current input fixture does not match the recorded first trial.")
    display = {
        "metrics": metrics,
        "trials": [{key: r.get(key) for key in ["trial", "ok", "correct", "input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "latency_ms", "estimated_cost_usd", "grading", "answer", "expected", "error"]} for r in trials],
        "prompt": trials[0]["question"],
        "routing_example": {
            "epoch": oracle["expected"]["epoch"],
            "minimum_capacity": oracle["minimum_capacity"],
            "routes": oracle["route_table"],
        },
    }
    html = (
        template.replace("__FONT_REGULAR__", regular).replace("__FONT_BOLD__", bold)
        .replace("__INPUT_IMAGE__", image)
        .replace("__REPORT__", json.dumps(display).replace("</", "<\\/"))
    )
    (PUBLIC / "benchmark.html").write_text(html, encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "metrics": metrics}))
    return report


if __name__ == "__main__":
    build()
