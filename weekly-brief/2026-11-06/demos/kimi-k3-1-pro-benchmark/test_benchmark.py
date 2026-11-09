# /// script
# requires-python = ">=3.12"
# dependencies = ["azure-identity>=1.25,<2", "openai>=2,<3", "python-dotenv>=1,<2"]
# ///
"""Validate deterministic grading and fixture integrity before paid calls."""

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location("benchmark_runner", ROOT / "run.py")
runner = importlib.util.module_from_spec(specification)
specification.loader.exec_module(runner)


class BenchmarkTests(unittest.TestCase):
    def test_exact_answer_passes(self):
        expected = {"route": "R-2", "epoch": 23, "snapshot_optional": True}
        self.assertTrue(runner.grade(json.dumps(expected), expected)["all_correct"])

    def test_boolean_is_not_an_integer(self):
        self.assertFalse(runner.grade('{"epoch":true}', {"epoch": 1})["all_correct"])

    def test_extra_keys_fail(self):
        self.assertFalse(runner.grade('{"epoch":1,"extra":0}', {"epoch": 1})["all_correct"])

    def test_invalid_json_cannot_pass(self):
        for answer in ["not json", "[]", "```json\n{}\n```"]:
            self.assertFalse(runner.grade(answer, {"epoch": 1})["all_correct"])

    def test_partial_answers_are_counted(self):
        result = runner.grade('{"a":1,"b":4}', {"a": 1, "b": 2})
        self.assertEqual(result["correct_count"], 1)
        self.assertFalse(result["all_correct"])

    def test_all_trial_fixtures_are_reproducible_and_large(self):
        hashes = []
        for trial in [1, 2, 3]:
            corpus = (ROOT / f"corpus-{trial}.txt").read_text(encoding="utf-8")
            oracle = json.loads((ROOT / f"oracle-{trial}.json").read_text(encoding="utf-8"))
            provenance = json.loads((runner.PUBLIC / f"provenance-{trial}.json").read_text(encoding="utf-8"))
            sha = hashlib.sha256(corpus.encode()).hexdigest()
            self.assertEqual(sha, provenance["sha256"])
            self.assertGreaterEqual(provenance["approximate_cl100k_tokens"], 200000)
            self.assertEqual(oracle["expected"]["checksum"], (17*oracle["x"] + 31*oracle["y"] + oracle["z"]) % 997)
            eligible = [r for r in oracle["route_table"] if r["capacity"] >= oracle["minimum_capacity"]]
            selected = min(eligible, key=lambda r: r["risk"])
            self.assertEqual(selected["id"], oracle["expected"]["route"])
            self.assertEqual(len(oracle["expected"]), 11)
            self.assertEqual(len(provenance["fixture_character_offsets"]), 3)
            hashes.append(sha)
        self.assertEqual(len(set(hashes)), 3)

    def test_live_records_meet_measured_threshold_and_total_shape(self):
        for trial in [1, 2, 3]:
            value = json.loads((runner.PUBLIC / f"trial-{trial}.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(value["input_tokens"], 200000)
            self.assertEqual(value["total_tokens"], value["input_tokens"] + value["output_tokens"])
            self.assertLessEqual(value["reasoning_tokens"], value["output_tokens"])
            self.assertEqual(runner.grade(value["answer"], value["expected"]), value["grading"])

    def test_manifest_assets_exist_and_are_bounded(self):
        manifest = json.loads((runner.PUBLIC / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["metrics"]["attempts"], 3)
        self.assertEqual(manifest["metrics"]["items_total"], 33)
        for asset in manifest["assets"]:
            path = runner.PUBLIC / asset["path"].removeprefix("/demos/kimi-k3-1-pro-benchmark/")
            self.assertTrue(path.is_file())
            self.assertLessEqual(path.stat().st_size, 15 * 1024 * 1024)

    def test_visual_is_self_contained(self):
        html = (runner.PUBLIC / "benchmark.html").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("__REPORT__", html)
        self.assertIn("data:font/woff2;base64,", html)
        self.assertIn("connect-src 'none'", html)


if __name__ == "__main__":
    unittest.main()
