# /// script
# requires-python = ">=3.12"
# dependencies = ["azure-identity>=1.25,<2", "openai>=2,<3", "python-dotenv>=1,<2"]
# ///
"""Small regression checks for the live JSON contract and recorded artifacts."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run


class DemoTests(unittest.TestCase):
    def test_image_case_is_not_a_factual_error(self):
        self.assertTrue(run.image_correct('{"orbit":"Copper","particles":240}'))

    def test_image_rejects_wrong_value(self):
        self.assertFalse(run.image_correct('{"orbit":"Copper","particles":180}'))

    def test_image_requires_shape(self):
        for answer in ['[]', 'not json', '{"orbit":"Copper","particles":"240"}']:
            self.assertFalse(run.image_correct(answer))

    def test_extract_only_removes_outer_fence(self):
        html = "<html><body><script>const n=1;</script></body></html>"
        self.assertEqual(run.extract_html("```html\n" + html + "\n```"), html)

    def test_extract_rejects_partial_html(self):
        with self.assertRaises(ValueError):
            run.extract_html("<html><body>unfinished")

    def test_request_retains_tokens_when_incomplete(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content="partial"),
                finish_reason="length",
            )],
            usage=SimpleNamespace(
                prompt_tokens=10, completion_tokens=20, total_tokens=30,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=5),
            ),
            model="Kimi-K3.1", id="test-request",
        )
        api = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: response
        )))
        with patch.dict("os.environ", {"KIMI_DEPLOYMENT": "test"}):
            result = run.request(api, "probe", "none", 512)
        self.assertFalse(result["ok"])
        self.assertEqual(result["total_tokens"], 30)
        self.assertEqual(result["reasoning_tokens"], 5)

    def test_recorded_scene_prompt_is_identical(self):
        data = json.loads((run.PUBLIC / "recorded-results.json").read_text(encoding="utf-8"))
        self.assertEqual(len({r["question"] for r in data["scenes"]}), 1)
        self.assertEqual(
            data["scenes"][0]["question"],
            (run.ROOT / "prompt.txt").read_text(encoding="utf-8"),
        )
        for result in data["scenes"]:
            self.assertTrue(result["ok"])
            self.assertEqual(result["total_tokens"], result["input_tokens"] + result["output_tokens"])
            self.assertLessEqual(result["reasoning_tokens"], result["output_tokens"])

    def test_public_contract_and_asset_limits(self):
        data = json.loads((run.PUBLIC / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(data["status"], ["ready", "partial", "unavailable"])
        self.assertTrue(data["live"]["supported"])
        for asset in data["assets"]:
            name = asset["path"].removeprefix("/demos/kimi-k3-1-pro/")
            self.assertTrue((run.PUBLIC / name).is_file(), name)
            self.assertLessEqual((run.PUBLIC / name).stat().st_size, 15 * 1024 * 1024)
        for path in run.PUBLIC.rglob("*"):
            if path.is_file():
                self.assertLessEqual(path.stat().st_size, 15 * 1024 * 1024)

    def test_generated_code_is_not_repaired(self):
        names = ["none-final", "comparison-low", "comparison-high"]
        for name in names:
            result = json.loads((run.PUBLIC / f"{name}.json").read_text(encoding="utf-8"))
            html = (run.PUBLIC / f"{name}.txt").read_text(encoding="utf-8")
            self.assertEqual(html, run.extract_html(result["answer"]))


if __name__ == "__main__":
    unittest.main()
