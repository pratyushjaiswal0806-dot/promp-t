import json
import os
import unittest
from unittest.mock import patch

from promptcompiler.models import DEFAULT_NIM_MODEL, list_models
from promptcompiler.server import handle_api_request


class ModelAndApiTests(unittest.TestCase):
    def test_default_model_is_not_openai_oss(self):
        models = list_models()

        self.assertNotEqual(DEFAULT_NIM_MODEL, "openai/gpt-oss-20b")
        self.assertTrue(any(model["id"] == DEFAULT_NIM_MODEL for model in models))

    def test_models_endpoint_returns_registry(self):
        with patch.dict(os.environ, {}, clear=True):
            status, body = handle_api_request("GET", "/api/models", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["source"], "local-registry")
        self.assertEqual(payload["default_model"], DEFAULT_NIM_MODEL)
        self.assertTrue(any(model["id"] == "openai/gpt-oss-20b" for model in payload["models"]))

    def test_models_endpoint_uses_live_nvidia_models_when_key_exists(self):
        live_models = [
            {"id": "nvidia/nemotron-3-nano-30b-a3b", "provider": "nvidia-nim"},
            {"id": "deepseek-ai/deepseek-v3.2", "provider": "nvidia-nim"},
        ]

        with (
            patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}, clear=True),
            patch("promptcompiler.server.NimClient.from_env") as from_env,
        ):
            from_env.return_value.list_available_models.return_value = live_models
            status, body = handle_api_request("GET", "/api/models", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["source"], "nvidia-live")
        self.assertEqual(payload["default_model"], "nvidia/nemotron-3-nano-30b-a3b")
        self.assertEqual(payload["models"], live_models)

    def test_samples_endpoint_returns_named_payloads(self):
        status, body = handle_api_request("GET", "/api/samples", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(payload["samples"]), 3)
        self.assertIn("name", payload["samples"][0])
        self.assertIn("input", payload["samples"][0])

    def test_export_endpoint_returns_optimized_text_and_compile_report(self):
        status, body = handle_api_request(
            "POST",
            "/api/export",
            json.dumps({"input": "@pin Keep CASE-123.\n\nx\n\nx"}).encode("utf-8"),
        )

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["optimized_text"], "@pin Keep CASE-123.\n\nx")
        self.assertIn("compile", payload)
