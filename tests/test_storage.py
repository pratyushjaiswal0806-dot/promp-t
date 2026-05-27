import tempfile
import unittest
from pathlib import Path

from promptcompiler.storage import SQLiteStore


class SQLiteStoreTests(unittest.TestCase):
    def test_records_trace_metrics_without_raw_payload_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "promptcompiler.sqlite3")
            store.record_trace(
                {
                    "trace_id": "tr_test",
                    "endpoint": "compile",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "session_id": "sess_1",
                    "mode": "balanced",
                    "original_token_count": 100,
                    "optimized_token_count": 60,
                    "token_reduction_percent": 40,
                    "estimated_cost_before_usd": 0.001,
                    "estimated_cost_after_usd": 0.0006,
                    "cache_status": "bypass",
                    "evaluation_status": "not_configured",
                    "zero_retention": True,
                    "latency_ms": 12,
                    "transformations": [{"type": "dedupe"}],
                    "retention": {"raw_payload_stored": False},
                }
            )

            trace = store.get_trace("tr_test")
            metrics = store.metrics({})
            store.close()

        self.assertEqual(trace["trace_id"], "tr_test")
        self.assertEqual(trace["original_token_count"], 100)
        self.assertFalse(trace["retention"]["raw_payload_stored"])
        self.assertEqual(metrics["requests"], 1)
        self.assertEqual(metrics["original_tokens"], 100)
        self.assertEqual(metrics["optimized_tokens"], 60)
        self.assertEqual(metrics["tokens_saved"], 40)

    def test_session_append_compacts_at_seventy_percent_and_redacts_zero_retention(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "promptcompiler.sqlite3")
            responses = []
            for index in range(4):
                responses.append(
                    store.append_session_turn(
                        session_id="sess_compact",
                        provider="openai",
                        model="gpt-4o-mini",
                        role="tool",
                        content=f"SECRET-RAW-{index} " + ("failure log " * 25),
                        target_token_budget=100,
                        mode="balanced",
                        zero_retention=True,
                    )
                )
            rows = store.session_turn_rows("sess_compact")
            store.close()

        triggered = [item for item in responses if item["adaptive_management_triggered"]]
        self.assertTrue(triggered)
        self.assertLess(
            triggered[-1]["new_total_session_tokens"],
            triggered[-1]["total_session_tokens"],
        )
        self.assertTrue(all(row["content"] is None for row in rows))
        self.assertTrue(any(row["is_summary"] for row in rows))
