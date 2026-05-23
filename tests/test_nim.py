import os
import unittest
from unittest.mock import patch

from promptcompiler.nim import NimClient, NimConfigError


class NimClientTests(unittest.TestCase):
    def test_missing_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NimConfigError):
                NimClient.from_env()

    def test_builds_openai_compatible_payload(self):
        client = NimClient(api_key="test-key")

        payload = client.build_summarize_payload(
            "Preserve CASE-123.",
            "openai/gpt-oss-20b",
        )

        self.assertEqual(payload["model"], "openai/gpt-oss-20b")
        self.assertEqual(payload["temperature"], 0.1)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("Preserve CASE-123.", payload["messages"][-1]["content"])


if __name__ == "__main__":
    unittest.main()
