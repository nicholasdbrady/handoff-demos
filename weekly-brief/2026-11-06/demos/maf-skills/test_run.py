import asyncio
import unittest
from unittest.mock import patch

import run


class RunTests(unittest.TestCase):
    def test_missing_configuration_fails_without_a_recorded_fallback(self) -> None:
        with patch.object(run, "load_dotenv"), patch.dict(run.os.environ, {}, clear=True):
            result = asyncio.run(run.run())
        self.assertFalse(result["ok"])
        self.assertEqual(result["output_text"], "")
        self.assertEqual(result["tool_calls"], [])
        self.assertEqual(result["error"], "ValueError")

    def test_generated_add_is_deterministic(self) -> None:
        self.assertEqual(run.generated_add(19, 23), 42)
        self.assertEqual(run.generated_add(-5, 2), -3)


if __name__ == "__main__":
    unittest.main()
