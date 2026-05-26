import json
import os
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from promptcompiler.server import handle_api_request, handle_api_request_with_headers


def post_v1(path, payload):
    return handle_api_request("POST", path, json.dumps(payload).encode("utf-8"))


class V1ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "PROMPTCOMPILER_DB_PATH": str(Path(self.tmp.name) / "test.sqlite3"),
                "PROMPTCOMPILER_DISABLE_DOTENV": "1",
            },
            clear=False,
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_v1_analyze_accepts_platform_payload_and_returns_trace_metadata(self):
        status, response = post_v1(
            "/v1/analyze",
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "@pin Return JSON for CASE-123."},
                    {"role": "user", "content": "Should we approve a refund over $500?"},
                ],
                "rag_chunks": [
                    {
                        "id": "chunk_a",
                        "source": "policy-a",
                        "text": "Source says refunds over $500 require manager approval.",
                    }
                ],
                "tools": [{"name": "lookup_policy", "description": "Find refund policy."}],
                "session_id": "sess_123",
                "target_token_budget": 8000,
                "mode": "balanced",
                "dry_run": True,
                "zero_retention": True,
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertTrue(payload["trace_id"].startswith("tr_"))
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(payload["session_id"], "sess_123")
        self.assertEqual(payload["tokenizer_accuracy"], "estimated")
        self.assertTrue(payload["retention"]["zero_retention"])
        self.assertFalse(payload["retention"]["raw_payload_stored"])
        self.assertGreater(payload["total_tokens"], 0)
        self.assertGreater(payload["pinned_tokens"], 0)
        self.assertIn("components", payload)
        self.assertTrue(any(item["component_type"] == "rag" for item in payload["components"]))
        self.assertIn("recommendation", payload)

    def test_v1_compile_returns_optimized_messages_and_transformations(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "@pin Keep CASE-123 exactly."},
                    {"role": "user", "content": "Can ACME approve the refund?"},
                ],
                "rag_chunks": [
                    {
                        "id": "policy-a",
                        "source": "policy-a",
                        "text": "Refunds over $500 require manager approval for CASE-345.",
                    },
                    {
                        "id": "policy-b",
                        "source": "policy-b",
                        "text": "Refunds over $500 require manager approval for CASE-345.",
                    },
                ],
                "mode": "balanced",
                "target_token_budget": 2000,
                "session_id": "sess_456",
                "policy": {"zero_retention": True},
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertTrue(payload["trace_id"].startswith("tr_"))
        self.assertEqual(payload["mode"], "balanced")
        self.assertEqual(payload["original_token_count"], payload["compile"]["original_tokens"])
        self.assertLess(payload["optimized_token_count"], payload["original_token_count"])
        self.assertGreater(payload["token_reduction_percent"], 0)
        self.assertTrue(payload["optimized_messages"])
        self.assertEqual(payload["optimized_messages"][0]["role"], "system")
        self.assertIn("CASE-123", payload["optimized_messages"][0]["content"])
        self.assertTrue(
            any(item["type"] == "rag_prune" for item in payload["transformations"])
        )
        self.assertEqual(payload["evaluation"]["layer2_status"], "disabled_zero_retention")
        self.assertEqual(payload["cache"]["status"], "bypass")
        self.assertEqual(payload["tokenizer"]["accuracy"], "estimated")
        self.assertFalse(payload["retention"]["raw_payload_stored"])

    def test_v1_compile_uses_embedding_semantic_policy_for_paraphrased_rag(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": "Do refunds over 500 need manager approval?",
                    }
                ],
                "rag_chunks": [
                    {
                        "id": "policy-a",
                        "source": "policy-a",
                        "text": "Refunds over 500 require manager approval.",
                    },
                    {
                        "id": "policy-b",
                        "source": "policy-b",
                        "text": "Reimbursements greater than 500 dollars need supervisor review.",
                    },
                ],
                "mode": "balanced",
                "semantic_policy": {"scorer": "embedding", "provider": "deterministic"},
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["semantic_policy"]["scorer"], "embedding")
        self.assertEqual(payload["semantic"]["scorer"], "embedding")
        self.assertIn("policy-a", payload["optimized_prompt"])
        self.assertNotIn("policy-b", payload["optimized_prompt"])
        self.assertTrue(
            any(item["type"] == "rag_prune" for item in payload["transformations"])
        )

    def test_v1_compile_rejects_invalid_messages_shape(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": {"role": "user", "content": "not a list"},
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 400)
        self.assertIn("messages must be a list", payload["error"])

    def test_legacy_api_compile_still_works(self):
        status, response = handle_api_request(
            "POST",
            "/api/compile",
            json.dumps({"input": "repeat\n\nrepeat"}).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn("optimized_text", payload)
        self.assertIn("semantic", payload)

    def test_v1_get_returns_json_method_error(self):
        status, response = handle_api_request("GET", "/v1/analyze", b"")

        payload = json.loads(response)
        self.assertEqual(status, 405)
        self.assertEqual(payload["error"], "Method not allowed")

    def test_v1_compile_records_trace_and_metrics(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "session_id": "sess_metrics",
                "messages": [{"role": "user", "content": "repeat\n\nrepeat"}],
                "mode": "balanced",
                "zero_retention": True,
            },
        )
        compile_payload = json.loads(response)
        self.assertEqual(status, 200)

        metrics_status, metrics_response = handle_api_request("GET", "/v1/metrics", b"")
        trace_status, trace_response = handle_api_request(
            "GET",
            f"/v1/requests/{compile_payload['trace_id']}",
            b"",
        )

        metrics = json.loads(metrics_response)
        trace = json.loads(trace_response)
        self.assertEqual(metrics_status, 200)
        self.assertEqual(trace_status, 200)
        self.assertEqual(metrics["requests"], 1)
        self.assertGreater(metrics["original_tokens"], 0)
        self.assertEqual(trace["trace_id"], compile_payload["trace_id"])
        self.assertFalse(trace["retention"]["raw_payload_stored"])

    def test_v1_session_append_triggers_compaction_and_metrics(self):
        responses = []
        for index in range(4):
            status, response = post_v1(
                "/v1/sessions/sess_agent/append",
                {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "turn": {
                        "role": "tool",
                        "content": f"SECRET-RAW-{index} " + ("compile failure " * 25),
                    },
                    "target_token_budget": 100,
                    "mode": "balanced",
                    "zero_retention": True,
                },
            )
            self.assertEqual(status, 200)
            responses.append(json.loads(response))

        metrics_status, metrics_response = handle_api_request("GET", "/v1/metrics", b"")
        metrics = json.loads(metrics_response)

        self.assertEqual(metrics_status, 200)
        self.assertTrue(any(item["adaptive_management_triggered"] for item in responses))
        triggered = [item for item in responses if item["adaptive_management_triggered"]][-1]
        self.assertTrue(triggered["summary_segment_id"].startswith("seg_summary_"))
        self.assertLess(triggered["new_total_session_tokens"], triggered["total_session_tokens"])
        self.assertEqual(metrics["sessions"]["active"], 1)
        self.assertGreaterEqual(metrics["sessions"]["compactions"], 1)

    def test_v1_compile_expands_system_prompt_ref_and_output_policy(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Give status for CASE-123."}],
                "context_policy": {"system_prompt_ref": "json_only", "cache_static_prefix": True},
                "output_policy": {"max_words": 50, "format": "json", "explain": False},
                "mode": "balanced",
                "zero_retention": True,
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["context_policy"]["system_prompt_ref"], "json_only")
        self.assertTrue(payload["context_policy"]["cache_static_prefix"])
        self.assertEqual(payload["output_policy"]["max_words"], 50)
        self.assertIn("Return JSON only", payload["optimized_prompt"])
        self.assertIn("Answer in <=50 words", payload["optimized_prompt"])

    def test_v1_session_context_returns_compact_messages(self):
        for index in range(3):
            status, _ = post_v1(
                "/v1/sessions/sess_context/append",
                {
                    "turn": {"role": "user", "content": f"turn {index} CASE-123 " + ("older " * 20)},
                    "target_token_budget": 90,
                    "zero_retention": False,
                },
            )
            self.assertEqual(status, 200)

        status, response = handle_api_request(
            "GET",
            "/v1/sessions/sess_context/context?target_token_budget=80&sliding_window_turns=1",
            b"",
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["session_id"], "sess_context")
        self.assertEqual(payload["context"]["strategy"], "pinned_summary_recent")
        self.assertLessEqual(payload["context"]["token_count"], 80)
        self.assertTrue(payload["context"]["messages"])

    def test_v1_compile_accepts_structured_input(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "structured_input": {"age_gt": 20, "product": "shoes", "month": "last"},
                "mode": "balanced",
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn('{"age_gt":20,"month":"last","product":"shoes"}', payload["optimized_prompt"])

    def test_v1_retrieve_budgets_rag_chunks(self):
        status, response = post_v1(
            "/v1/retrieve",
            {
                "query": "refund over 500",
                "rag_chunks": [
                    {"id": "a", "source": "doc-a", "text": "refund approval over 500 manager"},
                    {"id": "b", "source": "doc-b", "text": "refund approval over 500 manager"},
                    {"id": "c", "source": "doc-c", "text": "shipping policy"},
                ],
                "top_k": 2,
                "max_tokens": 12,
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in payload["chunks"]], ["a"])
        self.assertIn("b", payload["removed_chunk_ids"])

    def test_v1_compile_compacts_and_selects_tools(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "messages": [{"role": "user", "content": "Need refund policy for CASE-123."}],
                "tools": [
                    {
                        "name": "lookup_refund_policy",
                        "description": "refund manager approval " * 20,
                        "examples": ["long"],
                    },
                    {"name": "book_flight", "description": "travel booking " * 20, "examples": ["long"]},
                ],
                "tool_policy": {"max_tools": 1, "compact": True},
                "mode": "balanced",
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn("lookup_refund_policy", payload["optimized_prompt"])
        self.assertNotIn("book_flight", payload["optimized_prompt"])
        self.assertIn("tool_policy", payload)

    def test_v1_compile_cache_hit_and_route_metadata(self):
        payload = {
            "messages": [{"role": "user", "content": "format this json"}],
            "mode": "balanced",
            "task_type": "formatting",
            "cache_policy": {"enabled": True},
        }
        first_status, first_response = post_v1("/v1/compile", payload)
        second_status, second_response = post_v1("/v1/compile", payload)

        first = json.loads(first_response)
        second = json.loads(second_response)
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)
        self.assertEqual(first["cache"]["status"], "miss")
        self.assertEqual(second["cache"]["status"], "hit")
        self.assertEqual(second["route"]["tier"], "small")

    def test_v1_lint_returns_token_waste_findings(self):
        status, response = post_v1(
            "/v1/lint",
            {"input": "Analyze this code, explain it, optimize it, write tests, generate docs"},
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertTrue(any(item["code"] == "MULTI_TASK_REQUEST" for item in payload["findings"]))

    def test_v1_openai_proxy_returns_mock_chat_completion_and_headers(self):
        status, response, headers = handle_api_request_with_headers(
            "POST",
            "/v1/proxy/openai/chat/completions",
            json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "@pin Keep CASE-123."},
                        {"role": "user", "content": "repeat\n\nrepeat"},
                    ],
                    "promptcompiler": {
                        "mode": "balanced",
                        "session_id": "sess_proxy",
                        "zero_retention": True,
                    },
                }
            ).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["object"], "chat.completion")
        self.assertTrue(payload["id"].startswith("chatcmpl_pc_"))
        self.assertEqual(payload["choices"][0]["message"]["role"], "assistant")
        self.assertIn("promptcompiler", payload)
        self.assertEqual(headers["X-PromptCompiler-Trace"], payload["promptcompiler"]["trace_id"])
        self.assertIn("X-PromptCompiler-Original-Tokens", headers)
        self.assertIn("X-PromptCompiler-Optimized-Tokens", headers)
        self.assertFalse(payload["promptcompiler"]["retention"]["raw_payload_stored"])

    def test_v1_openai_proxy_forwards_semantic_policy_metadata(self):
        status, response, _headers = handle_api_request_with_headers(
            "POST",
            "/v1/proxy/openai/chat/completions",
            json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Do refunds over 500 need manager approval?",
                        }
                    ],
                    "promptcompiler": {
                        "mode": "balanced",
                        "semantic_policy": {
                            "scorer": "embedding",
                            "provider": "deterministic",
                        },
                        "rag_chunks": [
                            {
                                "id": "policy-a",
                                "source": "policy-a",
                                "text": "Refunds over 500 require manager approval.",
                            },
                            {
                                "id": "policy-b",
                                "source": "policy-b",
                                "text": "Reimbursements greater than 500 dollars need supervisor review.",
                            },
                        ],
                    },
                }
            ).encode("utf-8"),
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["promptcompiler"]["semantic_policy"]["scorer"], "embedding")
        self.assertGreater(payload["promptcompiler"]["token_reduction_percent"], 0)

    def test_v1_openai_proxy_rejects_streaming_for_now(self):
        status, response = post_v1(
            "/v1/proxy/openai/chat/completions",
            {
                "model": "gpt-4o-mini",
                "stream": True,
                "messages": [{"role": "user", "content": "hello"}],
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 400)
        self.assertIn("Streaming proxy responses are not supported", payload["error"])


if __name__ == "__main__":
    unittest.main()
