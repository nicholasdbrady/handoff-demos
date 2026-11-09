"""Offline tests for the live runner's output and failure contract."""

import contextlib
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import run

CONFIG = {
    "AZD_AGENT_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/demo",
    "AZD_AGENT_NAME": "handoff-azd-agent",
}


class RunnerTests(unittest.TestCase):
    def invoke(self, config, events=(), prompt="Hello", *, deck_config=None, environ=None):
        client = MagicMock()
        client.responses.create.return_value.__enter__.return_value = iter(events)
        project = MagicMock()
        project.get_openai_client.return_value.__enter__.return_value = client
        output = io.StringIO()
        with (
            patch.object(run, "dotenv_values", side_effect=[config, deck_config or {}]) as dotenv,
            patch.dict(run.os.environ, environ or {}, clear=True),
            patch.object(run, "AzureCliCredential"),
            patch.object(run, "AIProjectClient") as factory,
            patch("sys.argv", ["run.py", "--json", "--prompt", prompt]),
            contextlib.redirect_stdout(output),
        ):
            factory.return_value.__enter__.return_value = project
            code = run.main()
        self.assertEqual(
            [call.args[0] for call in dotenv.call_args_list],
            [
                run.Path(run.__file__).resolve().parent / ".env",
                run.Path(run.__file__).resolve().parent.parents[1] / ".env",
            ],
        )
        return code, json.loads(output.getvalue()), project

    def test_process_environment_overrides_both_dotenv_files(self):
        events = [
            SimpleNamespace(type="response.output_text.delta", delta="Hello"),
            SimpleNamespace(type="response.completed"),
        ]
        code, result, _ = self.invoke(
            {**CONFIG, "AZD_AGENT_NAME": "demo-agent"},
            events,
            deck_config={**CONFIG, "AZD_AGENT_NAME": "deck-agent"},
            environ={**CONFIG, "AZD_AGENT_NAME": "process-agent"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["agent"], "process-agent")

    def test_deck_dotenv_overrides_demo_dotenv(self):
        events = [
            SimpleNamespace(type="response.output_text.delta", delta="Hello"),
            SimpleNamespace(type="response.completed"),
        ]
        code, result, _ = self.invoke(
            {**CONFIG, "AZD_AGENT_NAME": "demo-agent"},
            events,
            deck_config={**CONFIG, "AZD_AGENT_NAME": "deck-agent"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["agent"], "deck-agent")

    def test_deck_dotenv_works_without_demo_dotenv(self):
        events = [
            SimpleNamespace(type="response.output_text.delta", delta="Hello"),
            SimpleNamespace(type="response.completed"),
        ]
        code, result, _ = self.invoke({}, events, deck_config=CONFIG)
        self.assertEqual(code, 0)
        self.assertEqual(result["agent"], CONFIG["AZD_AGENT_NAME"])

    def test_completed_live_response(self):
        events = [
            SimpleNamespace(type="response.output_text.delta", delta="Hello"),
            SimpleNamespace(type="response.completed"),
        ]
        code, result, project = self.invoke(CONFIG, events)
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["output_text"], "Hello")
        self.assertEqual(
            set(result), {"ok", "prompt", "output_text", "latency_ms", "agent", "endpoint_host"}
        )
        self.assertEqual(
            project.get_openai_client.call_args.kwargs["base_url"],
            CONFIG["AZD_AGENT_PROJECT_ENDPOINT"] + "/agents/handoff-azd-agent/endpoint/protocols/openai",
        )

    def test_stream_without_completion_is_failure(self):
        code, result, _ = self.invoke(
            CONFIG, [SimpleNamespace(type="response.output_text.delta", delta="Partial")]
        )
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("before completion", result["error"])

    def test_missing_config_is_failure(self):
        code, result, project = self.invoke({})
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        project.get_openai_client.assert_not_called()

    def test_untrusted_endpoint_is_rejected(self):
        code, result, project = self.invoke({**CONFIG, "AZD_AGENT_PROJECT_ENDPOINT": "https://example.net"})
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        project.get_openai_client.assert_not_called()

    def test_empty_prompt_is_rejected(self):
        code, result, project = self.invoke(CONFIG, prompt=" ")
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        project.get_openai_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
