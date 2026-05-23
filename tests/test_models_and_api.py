import json
import unittest

from promptcompiler.models import DEFAULT_NIM_MODEL, list_models
from promptcompiler.server import handle_api_request


class ModelAndApiTests(unittest.TestCase):
    def test_model_registry_includes_default_nim_model(self):
        models = list_models()

        self.assertEqual(DEFAULT_NIM_MODEL, "openai/gpt-oss-20b")
        self.assertTrue(any(model["id"] == DEFAULT_NIM_MODEL for model in models))

    def test_models_endpoint_returns_registry(self):
        status, body = handle_api_request("GET", "/api/models", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(any(model["id"] == "openai/gpt-oss-20b" for model in payload["models"]))

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
