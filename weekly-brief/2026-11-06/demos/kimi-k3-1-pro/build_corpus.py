"""Build a bounded corpus from tracked public Azure SDK changelogs."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
NEEDLE = "sdk/ai/azure-ai-projects/CHANGELOG.md"


def build(source: Path, max_chars: int) -> dict:
    """Retain source URLs, commit identity, and a verifiable real heading."""
    remote = subprocess.check_output(
        ["git", "-C", str(source), "remote", "get-url", "origin"], text=True
    ).strip()
    if remote.removesuffix(".git") not in (
        "https://github.com/Azure/azure-sdk-for-python",
        "git@github.com:Azure/azure-sdk-for-python",
    ):
        raise ValueError("Corpus must come from the public Azure SDK for Python clone.")
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    tracked = subprocess.check_output(
        ["git", "-C", str(source), "ls-files", "sdk/ai/*/CHANGELOG.md"], text=True
    ).splitlines()
    if NEEDLE not in tracked:
        raise ValueError("Azure AI Projects changelog is not tracked in this clone.")
    files = [p for p in sorted(tracked) if p != NEEDLE]
    files.insert(len(files) // 2, NEEDLE)
    sections, provenance = [], []
    used = 0
    for name in files:
        text = subprocess.check_output(
            ["git", "-C", str(source), "show", f"{commit}:{name}"],
            encoding="utf-8",
        )
        if name == NEEDLE:
            match = re.search(r"^## ([^\n]+)", text, re.MULTILINE)
            if not match:
                raise ValueError("No release heading in Azure AI Projects changelog.")
            expected = match.group(1)
        # Reserve room for the actual needle; never inject an invented answer.
        room = max_chars - used - (12000 if name != NEEDLE and NEEDLE not in [p["path"] for p in provenance] else 0)
        excerpt = text[:max(0, min(room, 16000))]
        if not excerpt:
            continue
        sections.append(f"\n=== SOURCE: {name} ===\n{excerpt}")
        used += len(sections[-1])
        provenance.append({
            "path": name,
            "url": f"https://github.com/Azure/azure-sdk-for-python/blob/{commit}/{name}",
            "characters": len(excerpt),
            "sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
            "truncated": len(excerpt) < len(text),
        })
    corpus = "".join(sections)
    index = {
        "question": f"In SOURCE {NEEDLE}, what is the first level-two release heading? Return it verbatim.",
        "expected": expected,
        "characters": len(corpus),
        "source_commit": commit,
        "sources": provenance,
        "sha256": hashlib.sha256(corpus.encode()).hexdigest(),
        "note": "Bounded public changelog excerpts; not a million-token benchmark.",
    }
    (ROOT / "corpus.txt").write_text(corpus, encoding="utf-8")
    (ROOT / "corpus-index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--max-chars", type=int, default=80000)
    args = parser.parse_args()
    if not 20000 <= args.max_chars <= 1000000:
        parser.error("--max-chars must be between 20000 and 1000000.")
    print(json.dumps(build(args.source, args.max_chars)))
