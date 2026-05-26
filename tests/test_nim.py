import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

from promptcompiler.env import load_local_env
from promptcompiler.nim import NimClient, NimConfigError, NimRequestError


class NimClientTests(unittest.TestCase):
    def test_missing_key_raises_clear_error(self):
        with patch.dict(os.environ, {"PROMPTCOMPILER_DISABLE_DOTENV": "1"}, clear=True):
            with self.assertRaises(NimConfigError):
                NimClient.from_env()

    def test_from_env_loads_key_from_folder_env_file(self):
        env_path = Path(__file__).resolve().parents[1] / ".env"
        original = env_path.read_text(encoding="utf-8") if env_path.exists() else None
        try:
            env_path.write_text(
                "NVIDIA_API_KEY=folder-test-key\nNVIDIA_NIM_BASE_URL=https://example.test/v1\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                client = NimClient.from_env()
        finally:
            if original is None:
                env_path.unlink(missing_ok=True)
            else:
                env_path.write_text(original, encoding="utf-8")

        self.assertEqual(client.api_key, "folder-test-key")
        self.assertEqual(client.base_url, "https://example.test/v1")

    def test_local_env_ignores_empty_placeholder_values(self):
        env_path = Path(__file__).resolve().parents[1] / ".env"
        original = env_path.read_text(encoding="utf-8") if env_path.exists() else None
        try:
            env_path.write_text("NVIDIA_API_KEY=\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                loaded = load_local_env(env_path)
                self.assertNotIn("NVIDIA_API_KEY", os.environ)
        finally:
            if original is None:
                env_path.unlink(missing_ok=True)
            else:
                env_path.write_text(original, encoding="utf-8")

        self.assertEqual(loaded, {})

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

    def test_builds_extensive_prompt_generation_payload(self):
        client = NimClient(api_key="test-key")

        payload = client.build_generate_prompt_payload(
            "AI portfolio website for student projects",
            kind="website",
            model="openai/gpt-oss-120b",
        )

        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertGreaterEqual(payload["max_tokens"], 1800)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("very extensive", payload["messages"][0]["content"].lower())
        self.assertIn("AI portfolio website", payload["messages"][-1]["content"])
        self.assertIn("website", payload["messages"][-1]["content"])

    def test_generate_extensive_prompt_returns_content(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"Generated extensive website prompt."}}]}'

        client = NimClient(api_key="test-key")

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            result = client.generate_extensive_prompt(
                "AI resume reviewer",
                kind="website",
                model="openai/gpt-oss-120b",
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://integrate.api.nvidia.com/v1/chat/completions")
        self.assertIn("context", urlopen.call_args.kwargs)
        self.assertEqual(result["generated_prompt"], "Generated extensive website prompt.")
        self.assertEqual(result["model"], "openai/gpt-oss-120b")
        self.assertEqual(result["kind"], "website")

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

    def test_summarize_reports_authorization_failure_as_actionable_error(self):
        error = urllib.error.HTTPError(
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=io.BytesIO(b'{"status":403,"title":"Forbidden","detail":"Authorization failed"}'),
        )
        client = NimClient(api_key="test-key")

        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(NimRequestError) as raised:
                client.summarize("hello", "meta/llama-3.1-8b-instruct")

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.error_code, "NIM_AUTHORIZATION_FAILED")
        self.assertIn("not authorized", str(raised.exception))

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
