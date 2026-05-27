import unittest
from unittest.mock import patch
import os
from pathlib import Path
import tempfile
import json

from fastapi.testclient import TestClient

from promptcompiler.fastapi_server import app


class FastApiServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("nim_configured", data)
        self.assertIn("default_model", data)

    def test_models_endpoint(self):
        response = self.client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIn("default_model", data)

    def test_samples_endpoint(self):
        response = self.client.get("/api/samples")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("samples", data)

    def test_v1_analyze(self):
        payload = {"input": "Hello world"}
        response = self.client.post("/v1/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_tokens", data)
        self.assertIn("components", data)

    def test_v1_compile_lossless(self):
        payload = {"input": "@pin Keep this.\n\nHello world\n\nHello world", "mode": "lossless"}
        response = self.client.post("/v1/compile", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("optimized_prompt", data)
        self.assertIn("optimized_token_count", data)

    def test_v1_compile_balanced(self):
        payload = {"input": "@pin Keep this.\n\nHello world\n\nHello world", "mode": "balanced"}
        response = self.client.post("/v1/compile", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("optimized_prompt", data)

    def test_v1_lint(self):
        payload = {"input": "Analyze this and explain it"}
        response = self.client.post("/v1/lint", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("findings", data)

    def test_v1_retrieve(self):
        payload = {
            "query": "refund approval",
            "rag_chunks": [
                {"id": "c1", "text": "Refunds over $500 require manager approval."},
                {"id": "c2", "text": "Standard refunds are processed within 5 business days."},
                {"id": "c3", "text": "International refunds require customs review."},
            ],
            "top_k": 2,
        }
        response = self.client.post("/v1/retrieve", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chunks", data)
    def test_v1_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"PROMPTCOMPILER_DB_PATH": str(Path(tmp) / "test.sqlite3")}, clear=False):
                response = self.client.get("/v1/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("requests", data)

    def test_v1_request_trace_not_found(self):
        response = self.client.get("/v1/requests/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_v1_compile_rejects_invalid_mode(self):
        payload = {"input": "Hello", "mode": "invalid"}
        response = self.client.post("/v1/compile", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_v1_compile_rejects_negative_budget(self):
        payload = {"input": "Hello", "mode": "lossless", "target_token_budget": -1}
        response = self.client.post("/v1/compile", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_legacy_api_analyze(self):
        payload = {"input": "Hello world"}
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_tokens", data)

    def test_legacy_api_compile(self):
        payload = {"input": "@pin Keep.\n\nHello\n\nHello", "mode": "balanced"}
        response = self.client.post("/api/compile", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("optimized_text", data)

    def test_docs_endpoints(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        spec = response.json()
        self.assertEqual(spec["info"]["title"], "PromptCompiler API")


if __name__ == "__main__":
    unittest.main()
