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

    def test_summarize_uses_ssl_context_and_reports_missing_entities(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return (
                    b'{"choices":[{"message":{"content":"Compressed without the case id."}}]}'
                )

        client = NimClient(api_key="test-key")

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            result = client.summarize(
                "Preserve CASE-123 and 2026-05-23.",
                "openai/gpt-oss-20b",
            )

        self.assertIn("context", urlopen.call_args.kwargs)
        self.assertFalse(result["preservation"]["ok"])
        self.assertIn("CASE-123", result["preservation"]["missing_entities"])
        self.assertIn("2026-05-23", result["preservation"]["missing_entities"])

    def test_list_available_models_uses_nvidia_models_endpoint(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"data":[{"id":"nvidia/nemotron-3-nano-30b-a3b"},{"id":"openai/gpt-oss-20b"}]}'

        client = NimClient(api_key="test-key")

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            models = client.list_available_models()

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://integrate.api.nvidia.com/v1/models")
        self.assertIn("context", urlopen.call_args.kwargs)
        self.assertEqual(models[0]["id"], "nvidia/nemotron-3-nano-30b-a3b")
        self.assertEqual(models[0]["provider"], "nvidia-nim")


if __name__ == "__main__":
    unittest.main()
