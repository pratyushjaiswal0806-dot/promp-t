import json
import os
import unittest
from unittest.mock import patch

from promptcompiler.nim import NimRequestError
from promptcompiler.server import WEB_ROOT, _static_file_for_request, handle_api_request


class ServerTests(unittest.TestCase):
    def test_health_reports_nim_status(self):
        with patch.dict(os.environ, {"PROMPTCOMPILER_DISABLE_DOTENV": "1"}, clear=True):
            status, body = handle_api_request("GET", "/api/health", b"")

        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertFalse(payload["nim_configured"])

    def test_analyze_endpoint_returns_segments(self):
        body = json.dumps({"input": "repeat\n\nrepeat"}).encode("utf-8")

        status, response = handle_api_request("POST", "/api/analyze", body)

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["segment_count"], 2)
        self.assertEqual(payload["duplicate_groups"][0]["count"], 2)

    def test_analyze_endpoint_returns_dashboard_fields(self):
        body = json.dumps(
            {
                "input": (
                    '{"messages":['
                    '{"role":"system","content":"@pin Follow CASE-123."},'
                    '{"role":"user","content":"Summarize this support ticket."}'
                    "]}"
                )
            }
        ).encode("utf-8")

        status, response = handle_api_request("POST", "/api/analyze", body)

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["segment_count"], 2)
        self.assertIn("segments", payload)
        self.assertIn("by_type", payload)
        self.assertIn("by_role", payload)
        self.assertIn("protected_entities", payload)
        self.assertIn("compression_opportunity", payload)

    def test_nim_summarize_without_key_returns_clear_error(self):
        with patch.dict(os.environ, {"PROMPTCOMPILER_DISABLE_DOTENV": "1"}, clear=True):
            status, response = handle_api_request(
                "POST",
                "/api/nim/summarize",
                json.dumps({"text": "hello"}).encode("utf-8"),
            )

        payload = json.loads(response)
        self.assertEqual(status, 400)
        self.assertEqual(payload["code"], "NIM_API_KEY_MISSING")

    def test_nim_authorization_failure_returns_403(self):
        error = NimRequestError(
            "NVIDIA NIM is not authorized for chat completions with the configured API key.",
            status_code=403,
            error_code="NIM_AUTHORIZATION_FAILED",
        )
        with (
            patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}, clear=True),
            patch("promptcompiler.server.NimClient.from_env") as from_env,
        ):
            from_env.return_value.summarize.side_effect = error
            status, response = handle_api_request(
                "POST",
                "/api/nim/summarize",
                json.dumps({"text": "hello"}).encode("utf-8"),
            )

        payload = json.loads(response)
        self.assertEqual(status, 403)
        self.assertEqual(payload["code"], "NIM_AUTHORIZATION_FAILED")
        self.assertIn("not authorized", payload["error"])

    def test_generate_prompt_requires_topic(self):
        status, response = handle_api_request(
            "POST",
            "/api/generate-prompt",
            json.dumps({"idea": "   "}).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 400)
        self.assertIn("idea is required", payload["error"])

    def test_generate_prompt_uses_default_gpt_oss_120b(self):
        generated = (
            "# Website Build Prompt\n\n"
            "Build a full website for an AI resume reviewer with sections, interactions, "
            "responsive behavior, accessibility, and acceptance criteria."
        )
        with (
            patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}, clear=True),
            patch("promptcompiler.server.NimClient.from_env") as from_env,
        ):
            from_env.return_value.generate_extensive_prompt.return_value = {
                "generated_prompt": generated,
                "model": "openai/gpt-oss-120b",
                "kind": "website",
            }
            status, response = handle_api_request(
                "POST",
                "/api/generate-prompt",
                json.dumps({"idea": "AI resume reviewer", "kind": "website"}).encode("utf-8"),
            )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(payload["kind"], "website")
        self.assertIn("AI resume reviewer", payload["generated_prompt"])
        from_env.return_value.generate_extensive_prompt.assert_called_once_with(
            "AI resume reviewer",
            kind="website",
            model="openai/gpt-oss-120b",
        )

    def test_compile_endpoint_accepts_mode_budget_and_dry_run(self):
        status, response = handle_api_request(
            "POST",
            "/api/compile",
            json.dumps(
                {
                    "input": "repeat\n\nrepeat",
                    "mode": "balanced",
                    "target_token_budget": 20,
                    "dry_run": True,
                }
            ).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "balanced")
        self.assertTrue(payload["dry_run"])
        self.assertIn("plan", payload)

    def test_compile_endpoint_returns_413_for_pinned_quota(self):
        status, response = handle_api_request(
            "POST",
            "/api/compile",
            json.dumps(
                {
                    "input": "@pin one two three four five six seven eight",
                    "target_token_budget": 8,
                }
            ).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 413)
        self.assertEqual(payload["code"], "PINNED_BUDGET_EXCEEDED")

    def test_compile_endpoint_returns_semantic_metadata(self):
        status, response = handle_api_request(
            "POST",
            "/api/compile",
            json.dumps(
                {
                    "mode": "balanced",
                    "input": (
                        "Question: Does a refund over $500 require manager approval?\n\n"
                        "Source: doc-a\nRefunds over $500 require manager approval for CASE-345.\n\n"
                        "Source: doc-b\nRefunds over $500 require manager approval for CASE-345."
                    ),
                }
            ).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn("semantic", payload)
        self.assertIn("chunks", payload["semantic"])
        self.assertTrue(payload["semantic"]["removed_chunk_ids"])

    def test_spa_page_routes_fall_back_to_vite_entrypoint(self):
        for route in (
            "/",
            "/workbench",
            "/how-it-works",
            "/platform",
            "/security",
            "/use-cases",
            "/docs",
            "/api-reference",
            "/observability",
        ):
            with self.subTest(route=route):
                self.assertEqual(_static_file_for_request(route), WEB_ROOT / "index.html")

        self.assertIsNone(_static_file_for_request("/assets/not-found.js"))


if __name__ == "__main__":
    unittest.main()
