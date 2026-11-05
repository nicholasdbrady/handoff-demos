"""Offline tests for equal workloads, reference separation, and provider boundaries."""

import json
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import demo_server as server
from catalog_matching import PAIRS, catalog_pair, catalog_request


class CatalogTests(unittest.TestCase):
    """Keep the live payload independent of the authored reference answers."""

    def setUp(self) -> None:
        self.client = TestClient(server.app, base_url="http://127.0.0.1",
                                 headers={"X-Demo-Client": "slidev"})

    def tearDown(self) -> None:
        self.client.close()

    def test_fixture_set_and_isolation(self) -> None:
        self.assertEqual(len(PAIRS), 12)
        self.assertEqual(len({pair["id"] for pair in PAIRS}), 12)
        self.assertEqual({pair["expected"] for pair in PAIRS}, {"same", "different", "review"})
        first = catalog_pair("renamed")
        first["left"]["model"] = "mutated"
        self.assertEqual(catalog_pair("renamed")["left"]["model"], "H4")
        for pair in PAIRS:
            for side in ("left", "right"):
                image = server.HERE / "public" / "catalog" / pair[side]["image"]
                self.assertGreater(image.stat().st_size, 1000)

    def test_payload_parity_and_no_reference_leak(self) -> None:
        for pair in PAIRS:
            native = catalog_request(pair["id"], "decision-1")
            luna = server.native_to_luna(native)
            self.assertEqual(luna["input"], native["state"])
            evidence = json.loads(native["state"])
            self.assertEqual(set(evidence), {"left", "right"})
            for side in ("left", "right"):
                self.assertNotIn("image", evidence[side])
                self.assertEqual(evidence[side], {k: v for k, v in pair[side].items() if k != "image"})
            self.assertNotIn(pair["reason"], json.dumps(native))
            self.assertNotIn('"expected"', json.dumps(native))
            question = native["questions"]["match"]
            self.assertEqual(luna["questions"][0]["instructions"], question["instructions"])
            self.assertEqual(luna["questions"][0]["choices"],
                             [{"value": key, "description": value} for key, value in question["criteria"].items()])

    def test_preview_and_unknown_ids_never_infer(self) -> None:
        with patch.object(server, "live_or_mock") as sdk, patch.object(server, "call_microsoft") as send:
            response = self.client.post("/demo-api/catalog-code", json={"pair": "capacity"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["microsoft"]["state"], response.json()["luna"]["input"])
            for route in ("catalog-code", "catalog-decision"):
                self.assertEqual(self.client.post(f"/demo-api/{route}", json={"pair": "unknown"}).status_code, 422)
            sdk.assert_not_called()
            send.assert_not_called()

    def test_rehearsal_is_explicit_and_unpriced(self) -> None:
        for provider in ("luna", "microsoft"):
            result = self.client.post("/demo-api/catalog-decision",
                                      json={"pair": "capacity", "provider": provider}).json()
            self.assertEqual(result["mode"], "rehearsal")
            self.assertIsNone(result["elapsed_ms"])
            self.assertIsNone(result["cost_usd"])
            self.assertEqual(result["raw"]["model"], "synthetic-rendering-fixture")
            answers = result["raw"]["answers"]
            answer = answers[0] if provider == "luna" else answers["match"]
            self.assertEqual(answer["choice"], "different")

    def test_live_requires_opt_in(self) -> None:
        with patch.object(server, "LIVE_ENABLED", False), patch.object(server, "live_or_mock") as sdk, \
                patch.object(server, "call_microsoft") as send:
            for provider in ("luna", "microsoft"):
                self.assertEqual(self.client.post("/demo-api/catalog-decision", json={
                    "mode": "live", "pair": "renamed", "provider": provider,
                }).status_code, 409)
            sdk.assert_not_called()
            send.assert_not_called()

    def test_live_native_request_is_the_preview(self) -> None:
        with patch.object(server, "LIVE_ENABLED", True), patch.object(server, "call_microsoft") as send:
            send.return_value = {"mode": "live", "raw": {"answers": {}}, "elapsed_ms": 898}
            response = self.client.post("/demo-api/catalog-decision", json={
                "mode": "live", "pair": "conflict", "provider": "microsoft",
            })
            self.assertEqual(response.status_code, 200)
            preview = self.client.post("/demo-api/catalog-code", json={"pair": "conflict"}).json()
            send.assert_called_once_with(preview["microsoft"])

    def test_live_luna_uses_sdk_and_preserves_raw(self) -> None:
        sdk = Mock()
        sdk.decisions.create.return_value.model_dump.return_value = {"answers": [{"type": "refusal", "name": "match"}]}
        with patch.object(server, "LIVE_ENABLED", True), patch.object(server, "live_or_mock", return_value=sdk), \
                patch.object(server, "run_cost", return_value=None):
            response = self.client.post("/demo-api/catalog-decision", json={
                "mode": "live", "pair": "renamed", "provider": "luna",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["raw"]["answers"][0]["type"], "refusal")
        self.assertIsNone(response.json()["cost_usd"])
        sdk.decisions.create.assert_called_once_with(**server.native_to_luna(server.checked_catalog_request("renamed")))


if __name__ == "__main__":
    unittest.main()
