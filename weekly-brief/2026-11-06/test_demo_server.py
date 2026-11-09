"""Offline route tests; no demo, credential, or cloud resource is used."""

import http.client
import json
import os
import threading
import tempfile
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import demo_server


class RouteTests(unittest.TestCase):
    def test_one_server_per_port(self):
        server = demo_server.DemoServer(("127.0.0.1", 0), demo_server.Handler)
        try:
            with self.assertRaises(OSError):
                demo_server.DemoServer(("127.0.0.1", server.server_port), demo_server.Handler)
        finally:
            server.server_close()

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), demo_server.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, body=body, headers=headers or {"X-Demo-Client": "slidev"})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_health(self):
        self.assertEqual(self.request("GET", "/demo-api/health")[0], 200)

    def test_foreign_origin(self):
        self.assertEqual(self.request("POST", "/demo-api/run/fal-video",
                                     {"X-Demo-Client": "slidev", "Origin": "https://evil.example"})[0], 403)

    def test_missing_client_and_rebinding(self):
        self.assertEqual(self.request("GET", "/demo-api/health", {"Origin": "http://localhost:3080"})[0], 403)
        self.assertEqual(self.request("GET", "/demo-api/health",
                                     {"X-Demo-Client": "slidev", "Host": "evil.example"})[0], 403)

    def test_disabled_live(self):
        with patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "0"}):
            self.assertEqual(self.request("POST", "/demo-api/run/azd-agent")[0], 409)

    def test_malformed_endpoint(self):
        with patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "1", "KIMI_ENDPOINT": "http://bad.example"}):
            status, body = self.request("POST", "/demo-api/run/kimi-k3-1-pro")
        self.assertEqual(status, 400)
        self.assertIn("HTTPS URL", body["detail"])

    def test_no_credentials_health(self):
        with patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "0"}, clear=True):
            status, body = self.request("GET", "/demo-api/health")
        self.assertEqual(status, 200)
        self.assertFalse(body["live_enabled"])

    def test_unknown_command_and_body(self):
        self.assertEqual(self.request("POST", "/demo-api/run/../../cmd")[0], 404)
        self.assertEqual(self.request("POST", "/demo-api/run/fal-video?cmd=evil")[0], 404)
        self.assertEqual(self.request("POST", "/demo-api/run/fal-video", body="{}")[0], 400)

    def test_success_marked_live(self):
        with patch.object(demo_server, "run_demo", return_value={"mode": "live", "result": {"ok": True}}):
            status, body = self.request("POST", "/demo-api/run/fal-video",
                                        {"X-Demo-Client": "slidev", "Origin": "http://localhost:3080"})
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "live")

    def test_real_error_no_capture_fallback(self):
        with patch.object(demo_server, "run_demo", side_effect=demo_server.DemoError(502, "Runner exited 1. quota exhausted")):
            status, body = self.request("POST", "/demo-api/run/kimi-k3-1-pro")
        self.assertEqual(status, 502)
        self.assertIn("quota exhausted", body["detail"])
        self.assertNotIn("result", body)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.manifest = self.root / "public" / "demos" / "maf-skills" / "manifest.json"
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text('{"live":{"supported":true}}', encoding="utf-8")
        script = self.root / "demos" / "maf-skills" / "run.py"
        script.parent.mkdir(parents=True)
        script.write_text("", encoding="utf-8")
        self.here = patch.object(demo_server, "HERE", self.root)
        self.here.start()
        self.env = patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "1", "FOUNDRY_PROJECT_ENDPOINT": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.here.stop()
        self.directory.cleanup()

    def test_missing_and_unsupported_manifest(self):
        self.manifest.write_text('{"live":{"supported":false}}', encoding="utf-8")
        with self.assertRaisesRegex(demo_server.DemoError, "does not support"):
            demo_server.run_demo("maf-skills")
        self.manifest.unlink()
        with self.assertRaisesRegex(demo_server.DemoError, "no capture manifest"):
            demo_server.run_demo("maf-skills")

    def test_fixed_command_and_json(self):
        def process(command, **kwargs):
            self.assertEqual(command, ["uv", "run", str(self.root / "demos" / "maf-skills" / "run.py"), "--json"])
            self.assertEqual(kwargs["cwd"], self.root)
            kwargs["stdout"].write(b'{"answer":42}')
            result = unittest.mock.Mock(returncode=0)
            return result
        with patch.object(demo_server.subprocess, "Popen", side_effect=process):
            result = demo_server.run_demo("maf-skills")
        self.assertEqual(result, {"mode": "live", "slug": "maf-skills", "result": {"answer": 42}})

    def test_nonzero_failure_not_replayed(self):
        def process(command, **kwargs):
            kwargs["stderr"].write(b"model deployment not available")
            return unittest.mock.Mock(returncode=1)
        with patch.object(demo_server.subprocess, "Popen", side_effect=process):
            with self.assertRaisesRegex(demo_server.DemoError, "model deployment not available"):
                demo_server.run_demo("maf-skills")

    def test_kimi_fixed_modes(self):
        for slug, options in demo_server.RUN_OPTIONS.items():
            manifest = self.root / "public" / "demos" / slug / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"live":{"supported":true}}', encoding="utf-8")
            script = self.root / "demos" / slug / "run.py"
            script.parent.mkdir(parents=True)
            script.write_text("", encoding="utf-8")
            def process(command, **kwargs):
                self.assertEqual(command, ["uv", "run", str(script), "--json", *options])
                kwargs["stdout"].write(b'{"ok":true}')
                return unittest.mock.Mock(returncode=0)
            with patch.object(demo_server.subprocess, "Popen", side_effect=process):
                self.assertEqual(demo_server.run_demo(slug)["mode"], "live")

    def test_json_failure_is_not_hidden_by_uv_installation(self):
        def process(command, **kwargs):
            kwargs["stderr"].write(b"Installed 30 packages")
            kwargs["stdout"].write(b'{"ok":false,"error":"ValueError: missing model configuration"}')
            return unittest.mock.Mock(returncode=1)
        with patch.object(demo_server.subprocess, "Popen", side_effect=process):
            with self.assertRaisesRegex(demo_server.DemoError, "missing model configuration"):
                demo_server.run_demo("maf-skills")

    def test_invalid_json_and_size(self):
        for output in [b"not JSON", b"[]", b"x" * (demo_server.OUTPUT_LIMIT + 1)]:
            def process(command, **kwargs):
                kwargs["stdout"].write(output)
                return unittest.mock.Mock(returncode=0)
            with patch.object(demo_server.subprocess, "Popen", side_effect=process):
                with self.assertRaises(demo_server.DemoError):
                    demo_server.run_demo("maf-skills")

    def test_timeout_stops_runner(self):
        import subprocess
        process = unittest.mock.Mock(pid=123456, returncode=-1)
        process.wait.side_effect = [subprocess.TimeoutExpired("uv", demo_server.TIMEOUT), None]
        with patch.object(demo_server.subprocess, "Popen", return_value=process), \
             patch.object(demo_server.subprocess, "run") as stop, \
             patch.object(demo_server.os, "name", "nt"):
            with self.assertRaisesRegex(demo_server.DemoError, "exceeded 350 seconds"):
                demo_server.run_demo("maf-skills")
        stop.assert_called_once_with(["taskkill", "/PID", "123456", "/T", "/F"], capture_output=True, check=False)
        self.assertFalse(demo_server.RUN_LOCK.locked())


if __name__ == "__main__":
    unittest.main()
