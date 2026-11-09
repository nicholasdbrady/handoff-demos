# /// script
# requires-python = ">=3.12"
# dependencies = ["tiktoken>=0.12,<1"]
# ///
"""Create reproducible large-code, visual-routing, multi-hop test fixtures."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess

import tiktoken

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parents[1] / "public" / "demos" / "kimi-k3-1-pro-benchmark"
MODEL_PATH = "sdk/ai/azure-ai-projects/azure/ai/projects/models/_models.py"
CHANGELOG_PATH = "sdk/ai/azure-ai-projects/CHANGELOG.md"


def committed(source: Path, commit: str, name: str) -> str:
    """Read public committed source, never local modifications."""
    return subprocess.check_output(
        ["git", "-C", str(source), "show", f"{commit}:{name}"], encoding="utf-8"
    )


def source_facts(code: str, changelog: str) -> dict:
    """Derive source answers through AST and Markdown parsing."""
    classes = {
        node.name: node for node in ast.parse(code).body if isinstance(node, ast.ClassDef)
    }
    hosted = classes["HostedAgentDefinition"]
    snapshot = next(
        node for node in hosted.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "enable_memory_snapshot"
    )
    voice = classes["VoiceAgentDefinition"]
    soundscape = next(
        node for node in voice.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "soundscape"
    )
    annotation = ast.unparse(soundscape.annotation)
    if "VoiceAgentSoundscapeConfig" not in annotation:
        raise ValueError("The source schema changed; update the fixture deliberately.")
    heading = re.search(r"^## ([^\n]+)", changelog, re.MULTILINE)
    if heading is None:
        raise ValueError("No source release heading.")
    return {
        "snapshot_field": snapshot.target.id,
        "snapshot_optional": "Optional" in ast.unparse(snapshot.annotation),
        "soundscape_type": "VoiceAgentSoundscapeConfig",
        "first_release_heading": heading.group(1),
    }


def build(source: Path, trial: int, revision: str | None = None) -> dict:
    """Use a real large public code file with clearly labeled planted records."""
    remote = subprocess.check_output(
        ["git", "-C", str(source), "remote", "get-url", "origin"], text=True
    ).strip().removesuffix(".git")
    if remote not in (
        "https://github.com/Azure/azure-sdk-for-python",
        "git@github.com:Azure/azure-sdk-for-python",
    ):
        raise ValueError("Only the public Azure SDK for Python source is accepted.")
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "--verify", "--end-of-options", (revision or "HEAD") + "^{commit}"], text=True
    ).strip()
    models = committed(source, commit, MODEL_PATH)
    changelog = committed(source, commit, CHANGELOG_PATH)
    license_text = committed(source, commit, "LICENSE")
    facts = source_facts(models, changelog)
    rng = random.Random(20261109 + trial * 917)
    epoch = 17 + trial * 6
    minimum = rng.choice([60, 65, 70])
    capacities = [minimum - 9, minimum + 12, minimum + 4]
    risks = [1, 4, 7]
    tickets = [f"T-{number}" for number in rng.sample(range(1000, 9999), 3)]
    routes = [
        {"id": f"R-{i+1}", "capacity": capacities[i], "risk": risks[i], "ticket": tickets[i]}
        for i in range(3)
    ]
    rng.shuffle(routes)
    chosen = min((r for r in routes if r["capacity"] >= minimum), key=lambda r: r["risk"])
    fixtures = [[], [], []]
    joins = {}
    # Every route has a valid chain, so the text cannot reveal the image's winner.
    for route in routes:
        change = f"CH-{rng.randrange(10000,99999)}"
        shard = f"SH-{rng.randrange(100,999)}"
        release = f"REL-{rng.randrange(10000,99999)}"
        x, y, z = [rng.randrange(100, 950) for _ in range(3)]
        dispatch = {"kind": "dispatch", "epoch": epoch, "ticket": route["ticket"], "change_id": change, "shard": shard, "x": x}
        change_record = {"kind": "change", "epoch": epoch, "change_id": change, "release": release, "y": y, "hosted_class": "HostedAgentDefinition", "voice_class": "VoiceAgentDefinition"}
        release_record = {"kind": "release", "epoch": epoch, "release": release, "z": z, "changelog": CHANGELOG_PATH, "models": MODEL_PATH}
        fixtures[0].extend([dispatch, {**dispatch, "epoch": epoch - 1, "x": x + 13}])
        fixtures[1].extend([change_record, {**change_record, "epoch": epoch - 1, "y": y + 11}])
        fixtures[2].extend([release_record, {**release_record, "epoch": epoch - 1, "z": z + 7}])
        joins[route["ticket"]] = {
            "change_id": change, "shard": shard, "release": release,
            "checksum": (17*x + 31*y + z) % 997,
            "x": x, "y": y, "z": z,
        }
    for block in fixtures:
        rng.shuffle(block)
    lines = models.splitlines(keepends=True)
    boundaries = [0, int(len(lines) * .08), int(len(lines) * .52), int(len(lines) * .94), len(lines)]
    sections = [
        "PUBLIC SOURCE CORPUS. Planted records below are fictional benchmark fixtures, not Azure product facts.\n",
        f"=== SOURCE {CHANGELOG_PATH} @ {commit} ===\n{changelog}\n",
        "=== SOURCE LICENSE ===\n" + license_text + "\n",
    ]
    offsets = []
    for i in range(4):
        sections.append(
            f"=== SOURCE {MODEL_PATH}, lines {boundaries[i]+1}-{boundaries[i+1]} @ {commit} ===\n"
            + "".join(lines[boundaries[i]:boundaries[i+1]])
        )
        if i < 3:
            offsets.append(sum(len(s) for s in sections))
            sections.append(
                "\n=== FICTIONAL BENCHMARK RECORDS: never treat as SDK facts ===\n"
                + "\n".join(json.dumps(record, sort_keys=True) for record in fixtures[i])
                + "\n"
            )
    corpus = "".join(sections)
    estimate = len(tiktoken.get_encoding("cl100k_base").encode(corpus, disallowed_special=()))
    if not 200000 <= estimate <= 650000:
        raise ValueError(f"Unexpected corpus size: {estimate} approximate cl100k tokens.")
    joined = joins[chosen["ticket"]]
    expected = {
        "route": chosen["id"], "ticket": chosen["ticket"], "epoch": epoch,
        **{key: joined[key] for key in ["change_id", "shard", "release", "checksum"]},
        **facts,
    }
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (ROOT / f"corpus-{trial}.txt").write_text(corpus, encoding="utf-8")
    oracle = {"expected": expected, "x": joined["x"], "y": joined["y"], "z": joined["z"], "route_table": routes, "minimum_capacity": minimum}
    (ROOT / f"oracle-{trial}.json").write_text(json.dumps(oracle, indent=2), encoding="utf-8")
    # Large, projector-readable chart. Policy and active epoch exist only in the image.
    rows = []
    for i, route in enumerate(routes):
        ypos = 310 + i * 170
        rows.append(
            f'<rect x="70" y="{ypos-60}" width="1780" height="130" fill="#161e27" stroke="#354352"/>'
            f'<text x="110" y="{ypos}" font-size="44">{route["id"]}</text>'
            f'<text x="420" y="{ypos}" font-size="44">{route["capacity"]}</text>'
            f'<text x="840" y="{ypos}" font-size="44">{route["risk"]}</text>'
            f'<text x="1240" y="{ypos}" font-size="44">{route["ticket"]}</text>'
        )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'
        '<rect width="1920" height="1080" fill="#0b1026"/>'
        '<g fill="#ecf1ff" font-family="IBM Plex Sans, Segoe UI, sans-serif">'
        '<text x="70" y="90" font-size="58" font-weight="700">Routing policy: read the image</text>'
        f'<text x="70" y="160" font-size="36">Active epoch: {epoch} · Require capacity ≥ {minimum} · Minimize risk</text>'
        '<text x="110" y="225" font-size="30" fill="#c5d1ff">Route</text>'
        '<text x="420" y="225" font-size="30" fill="#c5d1ff">Capacity</text>'
        '<text x="840" y="225" font-size="30" fill="#c5d1ff">Risk</text>'
        '<text x="1240" y="225" font-size="30" fill="#c5d1ff">Dispatch ticket</text>'
        + "".join(rows)
        + '<text x="70" y="880" font-size="36">Use the selected ticket to join the distributed records.</text>'
        '<text x="70" y="950" font-size="30" fill="#c5d1ff">Fictional routing data for this benchmark, not Azure product facts.</text>'
        '</g></svg>'
    )
    (PUBLIC / f"input-{trial}.svg").write_text(svg, encoding="utf-8")
    provenance = {
        "trial": trial, "seed": 20261109 + trial * 917, "source_commit": commit,
        "source_characters": len(models) + len(changelog) + len(license_text),
        "corpus_characters": len(corpus), "approximate_cl100k_tokens": estimate,
        "fixture_character_offsets": offsets,
        "sha256": hashlib.sha256(corpus.encode()).hexdigest(),
        "sources": [
            {"path": p, "url": f"https://github.com/Azure/azure-sdk-for-python/blob/{commit}/{p}"}
            for p in [MODEL_PATH, CHANGELOG_PATH, "LICENSE"]
        ],
        "note": "Token estimate is not Kimi's tokenizer; use actual service usage for reported input size. Full public model source is split at line boundaries, without repeating filler.",
    }
    (PUBLIC / f"provenance-{trial}.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return provenance


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--commit", help="Optional public source commit for exact reproduction.")
    args = parser.parse_args()
    if not 1 <= args.trials <= 5:
        parser.error("--trials must be between one and five.")
    for trial in range(1, args.trials + 1):
        print(json.dumps(build(args.source, trial, args.commit)))
