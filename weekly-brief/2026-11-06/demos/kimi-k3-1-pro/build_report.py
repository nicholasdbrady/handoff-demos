"""Combine real call records into the deck's manifest contract."""

from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parents[1] / "public" / "demos" / "kimi-k3-1-pro"
SCENES = ["none-final.json", "comparison-low.json", "comparison-high.json"]
CAVEATS = [
    "Three generated scenes use the identical prompt and a 12,000 completion-token cap. One sample per setting, not a benchmark or causal quality ranking.",
    "reasoning_effort none, low, and high were accepted by the live API. Reasoning tokens are included in output_tokens, not additional tokens.",
    "The service reports model Kimi-K3.1; management-plane deployment is MoonshotAI Kimi-K3.1-Pro version 2026-11-04. Do not hide this naming difference.",
    "Some real calls returned an endpoint-not-found error; an early scene hit its token cap and another lacked a complete HTML document. Live runner has no retries or recorded fallback.",
    "Current Nov 9 catalog labels GA; the supplied weekly draft said preview. No historical catalog snapshot establishes the lifecycle label by Nov 6 12:01 PST.",
    "Catalog lists 1,048,576 context tokens; Learn describes 1,000,000 input tokens and 262,144 output tokens. Use 'roughly one million' in narration.",
    "Long-context check is a bounded public changelog corpus, not a million-token capacity or attention benchmark.",
    "Generated scene code is unedited and runs inside an opaque-origin, allow-scripts-only iframe with network, forms, and navigation blocked by CSP/sandbox.",
    "The three.js runtime is pinned and vendored with its MIT license. Recorded scenes require WebGL but no model access or network dependency.",
    "USD announcement prices are $2.30 input, $0.23 cached input, $11.50 output per million tokens. Actual agreement pricing can differ.",
]
SOURCES = [
    {
        "url": "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/moonshot-ai%E2%80%99s-kimi-k3-1-pro-comes-to-microsoft-foundry/4570292",
        "date": "2026-11-05",
        "retrieved": "2026-11-09",
        "quote": "It is an open-weight model built for agentic work, with text and image understanding and a context window of up to 1 million tokens.",
        "note": "Announcement is on Microsoft Tech Community, not the Foundry devblog.",
    },
    {
        "url": "https://ai.azure.com/catalog/models/Kimi-K3.1-Pro",
        "retrieved": "2026-11-09",
        "quote": "Lifecycle Generally available (GA); Input type text, image; Context window 1048.576k; Token limits 262.144k output",
        "note": "Current catalog, not an archived reporting-window snapshot.",
    },
    {
        "url": "https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#moonshot-ai-models-sold-by-azure",
        "retrieved": "2026-11-09",
        "quote": "Input: text and image (1,000,000 tokens); Output: text (262,144 tokens); Tool calling: Yes",
    },
    {
        "url": "https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule#foundry-models-sold-by-azure",
        "retrieved": "2026-11-09",
        "quote": "Kimi-K3.1-Pro | 2026-11-04 | GA | 2027-11-04",
    },
    {
        "url": "https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability",
        "retrieved": "2026-11-09",
        "note": "Consult current region guidance. Actual East US availability was verified by a successful deployment and calls; not an exhaustive region survey.",
    },
]


def build() -> None:
    """Require successful live records before declaring the scene collection ready."""
    scenes = [json.loads((PUBLIC / p).read_text(encoding="utf-8")) for p in SCENES]
    if not all(r["ok"] for r in scenes):
        raise ValueError("A scene record is incomplete.")
    if len({r["question"] for r in scenes}) != 1:
        raise ValueError("Scene prompts differ.")
    image = json.loads((PUBLIC / "image-result-final.json").read_text(encoding="utf-8"))
    long = json.loads((PUBLIC / "long-final.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "corpus-index.json").read_text(encoding="utf-8"))
    index.pop("question")
    (PUBLIC / "corpus-provenance.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    captured = datetime.fromtimestamp(
        max((PUBLIC / p).stat().st_mtime for p in SCENES), timezone.utc
    ).isoformat()
    report = {
        "captured_at": captured,
        "scenes": scenes,
        "image": image,
        "long_context": long,
        "parameters": {"max_completion_tokens": 12000, "retries": 0, "stream": False},
        "attempts": [
            {"file": name, "record": json.loads((PUBLIC / name).read_text(encoding="utf-8"))}
            for name in [
                "scene-low.json", "result-low.json", "result-high.json",
                "scene-low-final.json", "scene-high-final.json", "image-result.json",
                "image-none.json", "long-result.json", "result-none.json",
                "probe-low.json", "probe-high.json", "probe-none.json",
            ]
            if (PUBLIC / name).exists()
        ],
        "caveats": CAVEATS,
        "sources": SOURCES,
    }
    (PUBLIC / "recorded-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    assets = [
        {"path": "/demos/kimi-k3-1-pro/input.png", "kind": "image", "caption": "Authored particle-allocation chart sent to Kimi", "alt": "Copper has 240 particles, cobalt 180, and silver 120."},
        {"path": "/demos/kimi-k3-1-pro/recorded-results.json", "kind": "json", "caption": "Real calls, exact prompt, token usage, and latency", "alt": "Same-prompt reasoning comparison, image answer, and bounded corpus answer."},
        {"path": "/demos/kimi-k3-1-pro/corpus-provenance.json", "kind": "json", "caption": "Public corpus commit, source links, and hashes", "alt": "Rebuildable first-party source provenance."},
    ]
    for name in SCENES:
        effort = json.loads((PUBLIC / name).read_text(encoding="utf-8"))["requested_reasoning_effort"]
        assets.append({"path": "/demos/kimi-k3-1-pro/" + name.replace(".json", ".txt"), "kind": "text", "caption": f"Unedited {effort}-effort generated HTML source; load through viewer.html", "alt": f"Kimi {effort} effort kinetic sculpture."})
    for effort in ["none", "low", "high"]:
        assets.append({
            "path": f"/demos/kimi-k3-1-pro/scene-{effort}.png",
            "kind": "image",
            "caption": f"Actual browser render of the {effort}-effort output",
            "alt": f"Kinetic sculpture generated by Kimi at {effort} effort, paused with controls visible.",
        })
    assets.append({
        "path": "/demos/kimi-k3-1-pro/render-validation.json",
        "kind": "json", "caption": "Observed browser rendering and control checks",
        "alt": "All three scenes animated and their pause, reset, and speed controls responded.",
    })
    manifest = {
        "slug": "kimi-k3-1-pro",
        "title": "Kimi K3.1 Pro: one prompt, three reasoning settings",
        "status": "ready" if image["ok"] and long["ok"] else "partial",
        "captured_at": captured,
        "environment": {
            "region": "eastus",
            "models/deployments": [
                {"model": "Kimi-K3.1-Pro", "version": "2026-11-04", "deployment": "kimi-k3-1-pro", "format": "MoonshotAI", "sku": "GlobalStandard"}
            ],
            "tool_versions": {"azure_cli": "2.92.0", "uv": "0.12.0", "three_js": "0.160.1"},
        },
        "assets": assets,
        "metrics": {
            "scenes": [
                {k: r[k] for k in ["requested_reasoning_effort", "input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "latency_ms", "correct"]}
                for r in scenes
            ],
            "image": {k: image[k] for k in ["correct", "input_tokens", "output_tokens", "latency_ms"]},
            "long_context": {k: long[k] for k in ["correct", "input_tokens", "output_tokens", "latency_ms"]},
        },
        "live": {
            "supported": True,
            "command": "uv run demos/kimi-k3-1-pro/run.py --json --mode scene --effort none --max-tokens 12000",
            "typical_seconds": round(scenes[0]["latency_ms"] / 1000, 2),
        },
        "preview": "/demos/kimi-k3-1-pro/index.html",
        "render_validation": json.loads((PUBLIC / "render-validation.json").read_text(encoding="utf-8")),
        "sources": SOURCES,
        "caveats": CAVEATS,
    }
    (PUBLIC / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "scenes": manifest["metrics"]["scenes"]}))


if __name__ == "__main__":
    build()
