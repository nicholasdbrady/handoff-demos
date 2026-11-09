"""Offline route tests; no demo, credential, or cloud resource is used."""

import http.client
import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import demo_server


class RouteTests(unittest.TestCase):
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
        with patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "1", "AZURE_AI_PROJECT_ENDPOINT": "http://bad.example"}):
            status, body = self.request("POST", "/demo-api/run/kimi-k3-1-pro")
        self.assertEqual(status, 400)
        self.assertIn("HTTPS project URL", body["detail"])

    def test_no_credentials_health(self):
        with patch.dict(os.environ, {"SLIDEV_ENABLE_LIVE": "0", "AZURE_AI_PROJECT_ENDPOINT": ""}):
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


if __name__ == "__main__":
    unittest.main()
