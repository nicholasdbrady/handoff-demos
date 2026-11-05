"""Offline evidence-gate and exact-arithmetic tests for the retail demo."""

import unittest
from unittest.mock import patch

from retail_receiving import check_receiving, receiving_fixture, receiving_request, receiving_route
import test_demo_server
import demo_server as server


class ReceivingTests(unittest.TestCase):
    """Keep extraction gates independent from semantic model confidence."""

    def test_exact_shortage_and_reference_value(self) -> None:
        result = check_receiving(receiving_fixture("clear"))
        self.assertEqual(result["status"], "semantic_needed")
        self.assertEqual(result["short_cases"], 2)
        self.assertEqual(result["reference_usd"], "37.00")

    def test_source_failures_stop_before_semantics(self) -> None:
        for fixture in ("low_ocr", "missing_region", "contradiction"):
            self.assertEqual(check_receiving(receiving_fixture(fixture))["status"], "review")
        for key, value in (("unit", "each"), ("currency", "EUR"), ("received", "12 cases"),
                           ("received", "NaN"), ("received", "13"), ("received", "-1"),
                           ("received", "10.5"), ("unit_price", "18.501"), ("note", ""),
                           ("recognition_confidence", None), ("recognition_confidence", True)):
            evidence = receiving_fixture("clear")
            evidence[key] = value
            with self.subTest(key=key, value=value):
                self.assertEqual(check_receiving(evidence)["status"], "review")
        evidence = receiving_fixture("clear")
        evidence["field_confidence"]["note"] = 0.899
        self.assertEqual(check_receiving(evidence)["status"], "review")

    def test_structured_reason_and_exact_match_skip_model(self) -> None:
        self.assertEqual(check_receiving(receiving_fixture("reason_code"))["status"], "partial_delivery")
        evidence = receiving_fixture("clear")
        evidence["received"] = "12"
        result = check_receiving(evidence)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["reference_usd"], "0.00")

    def test_semantic_gate_boundaries_and_refusal(self) -> None:
        answer = {"name": "delivery_reason", "type": "choice", "choice": "partial_delivery", "confidence": 0.8}
        self.assertEqual(receiving_route([answer])["label"], "partial_delivery")
        for alteration in ({"confidence": 0.799}, {"confidence": float("nan")},
                           {"confidence": True}, {"choice": "other"}, {"type": "refusal"}):
            self.assertEqual(receiving_route([{**answer, **alteration}])["label"], "review")
        self.assertEqual(receiving_route([])["label"], "review")
        self.assertEqual(receiving_route([answer, answer])["label"], "review")

    def test_model_request_contains_evidence_not_expected_label(self) -> None:
        request = receiving_request(receiving_fixture("clear"), "test-luna")
        self.assertIn("Two held at depot", request["input"])
        self.assertNotIn("37.00", request["input"])
        self.assertNotIn("source_regions", request["input"])
        self.assertEqual(request["questions"][0]["name"], "delivery_reason")


class RetailEndpointTests(unittest.TestCase):
    """Reuse the HTTP setup without repeating the adapter test cases."""

    setUp = test_demo_server.DemoServerTests.setUp
    tearDown = test_demo_server.DemoServerTests.tearDown

    def test_no_model_call_on_gate_failure_or_structured_reason(self) -> None:
        with patch.object(server, "live_or_mock") as factory:
            for fixture in ("low_ocr", "missing_region", "contradiction", "reason_code"):
                response = self.client.post("/demo-api/retail-decision", json={"fixture": fixture, "mode": "live"})
                self.assertEqual(response.status_code, 409)
            preview = self.client.post("/demo-api/retail-check", json={"fixture": "clear"}).json()
            self.assertEqual(preview["checks"]["reference_usd"], "37.00")
        factory.assert_not_called()

    def test_live_opt_in_and_explicit_rehearsal(self) -> None:
        self.assertEqual(self.client.post("/demo-api/retail-decision", json={"mode": "live"}).status_code, 409)
        response = self.client.post("/demo-api/retail-decision", json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "rehearsal")
        self.assertIsNone(response.json()["elapsed_ms"])
        self.assertEqual(self.client.post("/demo-api/retail-check", json={"fixture": "arbitrary"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
