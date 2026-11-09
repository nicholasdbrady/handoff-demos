"""Offline contract tests; no Azure authentication or paid generation."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

import httpx
from azure.core.exceptions import ClientAuthenticationError


SPEC = importlib.util.spec_from_file_location("fal_run", Path(__file__).with_name("run.py"))
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)

CONFIG = {
    "FAL_ACCESS_CONFIRMED": "true",
    "FOUNDRY_RESOURCE_ENDPOINT": "https://example.services.ai.azure.com",
    "FAL_DEPLOYMENTS": '{"ltx-2.5-fast":"draft","ltx-2.5-pro":"final"}',
    "FAL_PRICES_PER_SECOND_USD": '{"ltx-2.5-fast":0.09,"ltx-2.5-pro":0.12}',
}


class RunnerTests(unittest.TestCase):
    def main_result(self, argv, env):
        with patch.dict(os.environ, env, clear=True), patch.object(RUN, "load_dotenv"), \
                patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()) as output:
            code = RUN.main()
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])

    def test_unavailable_is_failure_not_recording(self):
        code, result = self.main_result(["run.py", "--json"], {})
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("access has not been confirmed", result["error"])
        for field in ("seconds", "video_path", "width", "height", "duration_s", "est_cost_usd"):
            self.assertIsNone(result[field])

    def test_default_prefers_configured_speed_option(self):
        with patch.object(RUN, "generate", return_value={"ok": True}) as generate:
            code, _ = self.main_result(["run.py", "--json"], CONFIG)
        self.assertEqual(code, 0)
        self.assertEqual(generate.call_args.args[0], "ltx-2.5-fast")

    def test_missing_price_blocks_before_authentication(self):
        config = {**CONFIG, "FAL_PRICES_PER_SECOND_USD": "{}"}
        with patch.object(RUN, "DefaultAzureCredential") as credential:
            code, result = self.main_result(["run.py", "--json"], config)
        self.assertEqual(code, 1)
        self.assertIn("price", result["error"])
        credential.assert_not_called()

    def test_invalid_prices(self):
        for price in (True, 0, -1, "0.09", float("nan"), float("inf")):
            with self.subTest(price=price), patch.dict(os.environ, {
                **CONFIG, "FAL_PRICES_PER_SECOND_USD": json.dumps({"ltx-2.5-fast": price})
            }, clear=True):
                with self.assertRaisesRegex(ValueError, "positive"):
                    RUN.generate("ltx-2.5-fast", RUN.PROMPT)

    def test_token_endpoint_restriction(self):
        for endpoint in (
            "http://example.services.ai.azure.com", "https://evil.example",
            "https://example.services.ai.azure.com.evil.example",
            "https://name:secret@example.services.ai.azure.com",
            "https://example.services.ai.azure.com:444", "https://example.services.ai.azure.com/path",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                RUN.check_endpoint(endpoint)

    def test_family_payloads(self):
        ltx = RUN.payload("ltx-2.5-fast", "draft", "scene")
        self.assertEqual((ltx["duration"], ltx["resolution"], ltx["fps"]), (6, "720p", 24))
        self.assertEqual(RUN.payload("ltx-2.5-pro", "final", "scene")["duration"], 6)
        kling = RUN.payload("kling-v3-pro", "kling", "scene")
        self.assertEqual(kling["duration"], "5")
        self.assertFalse(kling["generate_audio"])
        self.assertNotIn("resolution", kling)
        mini = RUN.payload("minimax-h3-max-turbo", "turbo", "scene")
        self.assertEqual((mini["duration"], mini["resolution"]), (5, "480P"))

    def test_authentication_error_still_one_json_object(self):
        with patch.object(RUN, "generate", side_effect=ClientAuthenticationError("private detail")):
            code, result = self.main_result(["run.py", "--json"], CONFIG)
        self.assertEqual(code, 1)
        self.assertNotIn("private detail", result["error"])

    def test_success_uses_live_result_and_measured_metadata(self):
        client = MagicMock()
        responses = [
            {"request_id": "job-123"}, {"status": "IN_PROGRESS"},
            {"status": "COMPLETED"}, {"video": {"url": "https://storage.example/clip?sig=private"}},
        ]
        client.request.side_effect = [
            httpx.Response(200, json=body) for body in responses
        ]
        download = MagicMock(status_code=200)
        download.iter_bytes.return_value = [b"real-test-payload"]
        client.stream.return_value.__enter__.return_value = download
        credential = MagicMock()
        credential.get_token.return_value.token = "azure-token-test"
        with tempfile.TemporaryDirectory() as directory, patch.object(RUN, "ROOT", Path(directory)), \
                patch.dict(os.environ, CONFIG, clear=True), patch.object(RUN.shutil, "which", return_value="ffprobe"), \
                patch.object(RUN, "DefaultAzureCredential") as credential_type, \
                patch.object(RUN.httpx, "Client") as client_type, patch.object(RUN.time, "sleep"), \
                patch.object(RUN, "probe", return_value={
                    "width": 1280, "height": 720, "duration_s": 6.125, "fps": 24, "file_mb": 0.001
                }):
            credential_type.return_value.__enter__.return_value = credential
            client_type.return_value.__enter__.return_value = client
            result = RUN.generate("ltx-2.5-fast", "scene")
            self.assertTrue(result["ok"])
            self.assertEqual(result["duration_s"], 6.125)
            self.assertEqual(result["est_cost_usd"], 0.54)
            self.assertEqual((Path(directory) / result["video_path"]).read_bytes(), b"real-test-payload")
            self.assertFalse(list(Path(directory).rglob("*.part")))
        self.assertEqual(client.request.call_args_list[0].args[0], "POST")
        self.assertEqual(sum(call.args[0] == "POST" for call in client.request.call_args_list), 1)
        self.assertEqual(client.stream.call_args.kwargs["headers"], {})

    def test_unexpected_poll_status_does_not_resubmit(self):
        client = MagicMock()
        client.request.side_effect = [
            httpx.Response(200, json={"request_id": "job"}),
            httpx.Response(200, json={"status": "FAILED"}),
        ]
        with patch.dict(os.environ, CONFIG, clear=True), \
                patch.object(RUN.shutil, "which", return_value="ffprobe"), \
                patch.object(RUN, "DefaultAzureCredential"), \
                patch.object(RUN.httpx, "Client") as client_type:
            client_type.return_value.__enter__.return_value = client
            with self.assertRaisesRegex(RuntimeError, "FAILED"):
                RUN.generate("ltx-2.5-fast", "scene")
        self.assertEqual(client.request.call_count, 2)

    def test_manifest_assets_and_source_prices(self):
        public = RUN.ROOT / "public" / "demos" / "fal-video"
        manifest = json.loads((public / "manifest.json").read_text())
        evidence = json.loads((public / "evidence.json").read_text())
        self.assertEqual(manifest["status"], "unavailable")
        self.assertFalse(manifest["live"]["supported"])
        self.assertEqual(manifest["metrics"]["generation_attempts"], 0)
        for asset in manifest["assets"]:
            self.assertTrue((RUN.ROOT / "public" / asset["path"].lstrip("/")).is_file())
            self.assertNotEqual(asset["kind"], "video")
        self.assertFalse(evidence["pricing"]["confirmed_billing_unit"])
        for model in evidence["pricing"]["models"]:
            rate = model["rates"].get(model.get("illustrative_resolution"), model["rates"].get("audio_off"))
            self.assertAlmostEqual(model["illustrative_duration_s"] * rate, model["illustrative_est_cost_usd"])
        svg = ET.parse(public / "comparison.svg").getroot()
        self.assertEqual((svg.attrib["width"], svg.attrib["height"]), ("1280", "860"))


if __name__ == "__main__":
    unittest.main()
