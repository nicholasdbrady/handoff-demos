"""Offline contract checks for the fixed-task demo and token lifecycle."""

import json
import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import copilot_harness_factory as factory
from copilot_harness_factory import shared_task, setup_continuous_evaluation
import demo_server as server

HERE = Path(__file__).parent


class DemoTests(unittest.TestCase):
    """Check replay integrity and request-path authentication boundaries."""

    def test_shared_task_exact(self) -> None:
        self.assertEqual(json.loads((HERE / "public" / "task.json").read_text())["prompt"], shared_task())

    def test_token_not_ready(self) -> None:
        server.READY.clear()
        with self.assertRaises(RuntimeError):
            server.cached_token()

    def test_evaluator_intent(self) -> None:
        self.assertEqual(
            [row["name"] for row in setup_continuous_evaluation(None)],
            ["coherence", "relevance", "task_adherence"],
        )

    def test_no_live_without_opt_in(self) -> None:
        with patch.dict("os.environ", {"SLIDEV_ENABLE_LIVE": "0"}):
            self.assertFalse(server.status()["ready"])

    def test_bundled_replays_are_explicit_synthetic_fixtures(self) -> None:
        recordings = list((HERE / "public" / "recordings").glob("*.json"))
        self.assertTrue(recordings)
        for recording in recordings:
            result = json.loads(recording.read_text(encoding="utf-8"))
            self.assertEqual(result["mode"], "synthetic")
            self.assertEqual(result["raw"]["status"], "illustration")
            self.assertEqual(result["elapsed_ms"], 0)
            self.assertEqual(result["usage"], {})
            self.assertIsNone(result["cost_usd"])
            self.assertTrue(result["text"])
            for file in result["files"]:
                self.assertTrue((HERE / "public" / "recordings" / "files" / file["name"]).is_file())

    def test_missing_live_configuration_is_actionable(self) -> None:
        with patch.dict("os.environ", {"AZURE_AI_PROJECT_ENDPOINT": ""}):
            with self.assertRaisesRegex(ValueError, "Set AZURE_AI_PROJECT_ENDPOINT"):
                factory.get_project_client()

    def test_offline_start_does_not_create_cloud_client(self) -> None:
        async def start():
            async with server.lifespan(server.app):
                self.assertIsNone(server.PROJECT)
        with patch.dict("os.environ", {"SLIDEV_ENABLE_LIVE": "0"}), \
                patch.object(server, "get_project_client") as client:
            asyncio.run(start())
        client.assert_not_called()

    def test_quota_retry_is_visible_and_same_conversation(self) -> None:
        calls = []

        def fake(client, lane, query, conversation):
            calls.append(conversation)
            if len(calls) == 1:
                raise factory.HarnessRateLimitError("conv-test", "quota")
            yield {"type": "result", "result": {"elapsed_ms": 1}}

        with patch.object(factory, "_stream_agent_once", fake), patch.object(factory.time, "sleep") as sleep:
            events = list(factory.stream_agent(None, "copilot", "original task"))
        self.assertEqual(calls, [None, "conv-test"])
        self.assertEqual(events[0]["name"], "quota_wait")
        self.assertEqual(events[-1]["result"]["quota_retries"], 1)
        sleep.assert_called_once_with(65)

    def test_ndjson_errors_are_not_success(self) -> None:
        def broken():
            yield {"type": "tool", "name": "shell_call"}
            raise RuntimeError("actual failure")
        server.MODEL_LOCK.acquire()
        events = [json.loads(row) for row in server.ndjson(broken())]
        self.assertEqual([row["type"] for row in events], ["tool", "error"])
        self.assertFalse(server.MODEL_LOCK.locked())

    def test_missing_hosted_adapter_does_not_hold_model_slot(self) -> None:
        with patch.object(server, "status", return_value={"ready": True}), patch.object(server, "HOSTED", None):
            with self.assertRaises(server.HTTPException) as error:
                server.stream_hosted("sdk")
        self.assertEqual(error.exception.status_code, 503)
        self.assertFalse(server.MODEL_LOCK.locked())

    def test_stream_lanes_share_one_model_lock(self) -> None:
        server.MODEL_LOCK.acquire()
        try:
            with patch.object(server, "status", return_value={"ready": True}):
                with self.assertRaises(server.HTTPException) as error:
                    server.stream_run("copilot")
            self.assertEqual(error.exception.status_code, 409)
        finally:
            server.MODEL_LOCK.release()

    def test_model_worker_finishes_without_a_browser_reader(self) -> None:
        completed = []

        def events():
            yield {"type": "delta", "text": "actual delta"}
            completed.append(True)
            yield {"type": "result", "result": {"text": "actual result"}}

        server.MODEL_LOCK.acquire()
        response = server.live_response(events())
        self.assertTrue(server.MODEL_LOCK.acquire(timeout=2))
        server.MODEL_LOCK.release()
        self.assertEqual(completed, [True])

        async def read():
            return [json.loads(row) async for row in response.body_iterator]

        self.assertEqual([row["type"] for row in asyncio.run(read())], ["delta", "result"])

    def test_file_id_is_not_joined_to_the_next_assistant_message(self) -> None:
        file_id = "assistant-testfile"
        raw = {"usage": {}, "output": [
            {"type": "message", "content": [{"type": "output_text", "text": file_id,
              "annotations": [{"file_id": file_id, "filename": "review.json"}]}]},
            {"type": "message", "content": [{"type": "output_text", "text": "The file is attached.", "annotations": []}]},
        ]}
        final = SimpleNamespace(model_dump=lambda **kwargs: raw, output_text=file_id + "The file is attached.")
        client = MagicMock()
        openai = client.get_openai_client.return_value.__enter__.return_value
        openai.conversations.create.return_value.id = "conversation-test"
        openai.responses.create.return_value.__enter__.return_value = [
            SimpleNamespace(type="response.completed", response=final)
        ]
        result = list(factory._stream_agent_once(client, "copilot", "task"))[-1]["result"]
        self.assertEqual(result["text"], file_id + "\n\nThe file is attached.")
        self.assertEqual(result["files"], [{"id": file_id, "name": "review.json"}])
        client.get_openai_client.assert_called_once()

    def test_generated_files_use_the_project_files_endpoint(self) -> None:
        client = MagicMock()
        client.get_openai_client.return_value.__enter__.return_value.files.content.return_value.read.return_value = b"{}"
        with TemporaryDirectory() as directory, patch.object(factory, "HERE", Path(directory)):
            factory.save_recording(client, "copilot", {"files": [{"id": "assistant-test", "name": "review.json"}]})
            self.assertEqual((Path(directory) / "public" / "recordings" / "files" / "review.json").read_bytes(), b"{}")
        client.get_openai_client.assert_called_once_with()

    def test_summary_events_do_not_expose_raw_reasoning(self) -> None:
        final = SimpleNamespace(model_dump=lambda **kwargs: {"output": [
            {"type": "reasoning", "summary": [{"type": "summary_text", "text": "Supported summary"}],
             "encrypted_content": "private", "content": "private"}], "usage": {}})
        client = MagicMock()
        openai = client.get_openai_client.return_value.__enter__.return_value
        openai.conversations.create.return_value.id = "test"
        openai.responses.create.return_value.__enter__.return_value = [
            SimpleNamespace(type="response.created"),
            SimpleNamespace(type="response.reasoning_summary_part.added"),
            SimpleNamespace(type="response.reasoning_summary_text.delta", delta="Supported summary"),
            SimpleNamespace(type="response.reasoning_summary_text.done"),
            SimpleNamespace(type="response.completed", response=final),
        ]
        events = list(factory.stream_agent(client, "default", "task"))
        self.assertEqual([event["type"] for event in events], ["start", "step", "reasoning", "reasoning", "reasoning", "result"])
        self.assertEqual(events[3]["text"], "Supported summary")
        self.assertNotIn("private", json.dumps(events))
        self.assertTrue(all("at_ms" in event for event in events))
        self.assertNotIn("reasoning", openai.responses.create.call_args.kwargs)

    def test_archive_keeps_selected_recording_unchanged(self) -> None:
        with TemporaryDirectory() as directory, patch.object(server, "__file__", str(Path(directory) / "demo_server.py")):
            target = Path(directory) / "public" / "recordings" / "copilot.json"
            target.parent.mkdir(parents=True)
            target.write_text("selected replay")
            server.archive_result("copilot", {"raw": {"type": "reasoning", "encrypted_content": "private", "summary": []}})
            self.assertEqual(target.read_text(), "selected replay")
            archived = list((Path(directory) / ".logs" / "runs").glob("*.json"))
            self.assertEqual(len(archived), 1)
            self.assertNotIn("private", archived[0].read_text())


if __name__ == "__main__":
    unittest.main()
