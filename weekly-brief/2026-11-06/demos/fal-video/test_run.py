"""Offline contract tests; no Azure authentication or paid generation."""

import contextlib
import hashlib
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
        both = {**CONFIG, "FAL_DEPLOYMENTS": '{"ltx-2.5-fast":"draft","minimax-h3-max-turbo":"turbo"}'}
        with patch.object(RUN, "generate", return_value={"ok": True}) as generate:
            self.main_result(["run.py", "--json"], both)
        self.assertEqual(generate.call_args.args[0], "minimax-h3-max-turbo")

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
        self.assertTrue(ltx["generate_audio"])
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
            self.assertEqual(result["request_id"], "job-123")
            self.assertEqual(result["duration_s"], 6.125)
            self.assertEqual(result["est_cost_usd"], 0.54)
            self.assertEqual((Path(directory) / result["video_path"]).read_bytes(), b"real-test-payload")
            self.assertFalse(list(Path(directory).rglob("*.part")))
            saved = json.loads(next(Path(directory).rglob("*job-123.request.json")).read_text())
            self.assertEqual((saved["request_id"], saved["payload"]["prompt"]), ("job-123", "scene"))
            self.assertTrue(saved["payload"]["generate_audio"])
            self.assertNotIn("azure-token-test", json.dumps(saved))
        self.assertEqual(client.request.call_args_list[0].args[0], "POST")
        self.assertEqual(sum(call.args[0] == "POST" for call in client.request.call_args_list), 1)
        self.assertEqual(client.stream.call_args.kwargs["headers"], {})

    def test_unexpected_poll_status_does_not_resubmit(self):
        client = MagicMock()
        client.request.side_effect = [
            httpx.Response(200, json={"request_id": "job"}),
            httpx.Response(200, json={"status": "FAILED"}),
        ]
        with tempfile.TemporaryDirectory() as directory, patch.object(RUN, "ROOT", Path(directory)), \
                patch.dict(os.environ, CONFIG, clear=True), \
                patch.object(RUN.shutil, "which", return_value="ffprobe"), \
                patch.object(RUN, "DefaultAzureCredential"), \
                patch.object(RUN.httpx, "Client") as client_type:
            client_type.return_value.__enter__.return_value = client
            with self.assertRaisesRegex(RuntimeError, "FAILED"):
                RUN.generate("ltx-2.5-fast", "scene")
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(RUN.STATE["request_id"], "job")

    def test_resume_never_posts(self):
        client = MagicMock()
        client.request.side_effect = [httpx.Response(200, json={"status": "FAILED"})]
        with tempfile.TemporaryDirectory() as directory, patch.object(RUN, "ROOT", Path(directory)), \
                patch.dict(os.environ, CONFIG, clear=True), \
                patch.object(RUN.shutil, "which", return_value="ffprobe"), \
                patch.object(RUN, "DefaultAzureCredential"), \
                patch.object(RUN.httpx, "Client") as client_type:
            client_type.return_value.__enter__.return_value = client
            with self.assertRaisesRegex(RuntimeError, "FAILED"):
                RUN.generate("ltx-2.5-fast", "scene", resume="job-9")
        self.assertNotIn("POST", [call.args[0] for call in client.request.call_args_list])
        with patch.object(RUN.shutil, "which", return_value="ffprobe"):
            code, result = self.main_result(["run.py", "--json", "--model", "ltx-2.5-fast",
                                             "--resume", "bad/id"], CONFIG)
        self.assertEqual((code, result["ok"]), (1, False))
        self.assertIn("unexpected format", result["error"])

    def test_manifest_assets_and_source_prices(self):
        public = RUN.ROOT / "public" / "demos" / "fal-video"
        manifest = json.loads((public / "manifest.json").read_text())
        evidence = json.loads((public / "evidence.json").read_text())
        self.assertEqual(manifest["status"], "partial")
        self.assertTrue(manifest["live"]["supported"])
        self.assertEqual(manifest["metrics"]["generation_attempts"], 5)
        videos = [asset for asset in manifest["assets"] if asset["kind"] == "video"]
        self.assertEqual([asset["model"] for asset in videos], [
            "minimax-h3-max-turbo", "kling-v3-pro", "ltx-2.5-fast", "ltx-2.5-pro", "minimax-h3-max"])
        originals = {r["model"]: r.get("sha256_original", r.get("sha256"))
                     for r in evidence["measured_generation_results"]}
        for video in videos:
            self.assertTrue(video["prompt"] and video["title"] and video["poster"])
            self.assertTrue((RUN.ROOT / "public" / video["poster"].lstrip("/")).is_file())
            path = RUN.ROOT / "public" / video["path"].lstrip("/")
            digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            self.assertEqual(digest, originals[video["model"]])
            self.assertTrue(video["byte_identical_to_original"])
            derivative = video.get("derivative")
            if derivative:
                self.assertLessEqual(derivative["file_mb"], 15)
                derived = RUN.ROOT / "public" / derivative["path"].lstrip("/")
                self.assertEqual(hashlib.sha256(derived.read_bytes()).hexdigest().upper(),
                                 derivative["sha256"])
        self.assertLessEqual(sum(v["metrics"]["file_mb"] for v in videos), 40)
        self.assertLessEqual(manifest["metrics"]["generation_spend_usd_estimate_creative_clips"], 2.25)
        for asset in manifest["assets"]:
            self.assertTrue((RUN.ROOT / "public" / asset["path"].lstrip("/")).is_file())
        self.assertTrue(evidence["pricing"]["confirmed_billing_unit"])
        for model in evidence["pricing"]["models"]:
            rate = model["rates"].get(model.get("illustrative_resolution"), model["rates"].get("audio_off"))
            self.assertAlmostEqual(model["illustrative_duration_s"] * rate, model["illustrative_est_cost_usd"])
        svg = ET.parse(public / "comparison.svg").getroot()
        self.assertEqual((svg.attrib["width"], svg.attrib["height"]), ("1280", "480"))
        texts = svg.findall(".//{http://www.w3.org/2000/svg}text")
        visible_copy = " ".join("".join(text.itertext()) for text in texts)
        self.assertNotIn("$", visible_copy)
        self.assertNotIn("$", manifest["assets"][0]["alt"])
        self.assertIn("IBM Plex Sans", (public / "comparison.svg").read_text())
        self.assertTrue(all(float(node.attrib["font-size"]) >= 24
                            for node in svg.iter() if "font-size" in node.attrib))


if __name__ == "__main__":
    unittest.main()
