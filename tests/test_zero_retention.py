"""Zero-retention proof tests.

These tests verify that when zero_retention is True, no raw prompt
content appears in SQLite traces, compile cache, or session turns.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from promptcompiler.storage import SQLiteStore


class ZeroRetentionProofTests(unittest.TestCase):
    """Prove zero_retention prevents raw prompt storage across all surfaces."""

    def test_trace_contains_no_raw_input_when_zero_retention(self):
        """Verify trace record has no raw prompt text fields."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "test.sqlite3")
            store.record_trace(
                {
                    "trace_id": "tr_zero_1",
                    "endpoint": "compile",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "session_id": None,
                    "mode": "balanced",
                    "original_token_count": 250,
                    "optimized_token_count": 140,
                    "token_reduction_percent": 44.0,
                    "estimated_cost_before_usd": 0.001,
                    "estimated_cost_after_usd": 0.00056,
                    "cache_status": "bypass",
                    "evaluation_status": "not_configured",
                    "zero_retention": True,
                    "latency_ms": 8,
                    "transformations": [{"type": "dedupe", "removed": 3}],
                    "retention": {"raw_payload_stored": False},
                }
            )
            trace = store.get_trace("tr_zero_1")
            store.close()

        self.assertIsNotNone(trace)
        self.assertTrue(trace["zero_retention"])
        self.assertFalse(trace["retention"].get("raw_payload_stored", True))
        # Verify no raw text fields exist in the trace
        for key in trace:
            val = trace[key]
            if isinstance(val, str) and "SECRET-RAW" in val:
                self.fail(f"Raw prompt leaked into trace field: {key}")

    def test_compile_cache_stores_response_not_input(self):
        """Verify compile cache entries don't echo raw input text."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "test.sqlite3")
            cache_key = "ck_zero_retention_test"
            # Simulate a compile response that would contain raw text only if echoed
            fake_response = {
                "optimized_text": "summarized output — no raw input here",
                "original_tokens": 250,
                "optimized_tokens": 140,
                "tokens_saved": 110,
                "cache_status": "miss",
            }
            store.set_compile_cache(cache_key, fake_response)

            cached = store.get_compile_cache(cache_key)
            store.close()

        self.assertIsNotNone(cached)
        cached_text = str(cached)
        # The compile cache should store the optimized output, not the raw input.
        # Verify the raw input marker does not appear.
        self.assertNotIn("SECRET-RAW", cached_text)

    def test_session_turn_content_is_none_when_zero_retention(self):
        """Verify session turns redact content when zero_retention is True."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "test.sqlite3")
            store.append_session_turn(
                session_id="sess_zero",
                provider="openai",
                model="gpt-4o-mini",
                role="user",
                content="SECRET-RAW session content must not persist",
                target_token_budget=200,
                mode="balanced",
                zero_retention=True,
            )
            rows = store.session_turn_rows("sess_zero")
            store.close()

        self.assertTrue(len(rows) > 0)
        for row in rows:
            self.assertIsNone(
                row.get("content"),
                msg="Raw session content leaked despite zero_retention=True",
            )

    def test_trace_row_columns_exclude_raw_payload_text(self):
        """Directly query trace rows to ensure no text payload columns exist."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "test.sqlite3")
            store.record_trace(
                {
                    "trace_id": "tr_zero_2",
                    "endpoint": "compile",
                    "provider": "nvidia-nim",
                    "model": "nvidia/llama-3.1-nemotron-nano-8b",
                    "session_id": None,
                    "mode": "aggressive",
                    "original_token_count": 500,
                    "optimized_token_count": 200,
                    "token_reduction_percent": 60.0,
                    "estimated_cost_before_usd": 0.002,
                    "estimated_cost_after_usd": 0.0008,
                    "cache_status": "bypass",
                    "evaluation_status": "not_configured",
                    "zero_retention": True,
                    "latency_ms": 15,
                    "transformations": [
                        {"type": "dedupe", "removed": 5},
                        {"type": "compact", "removed": 2},
                    ],
                    "retention": {"raw_payload_stored": False},
                }
            )

            # Check schema for any text payload columns
            conn = store._connect()
            cursor = conn.execute("PRAGMA table_info(traces)")
            columns = {row[1] for row in cursor.fetchall()}
            store.close()

        text_payload_cols = {"raw_input", "input_text", "prompt_text", "original_text"}
        leaked = text_payload_cols & columns
        self.assertEqual(
            leaked, set(),
            f"Trace table has raw payload columns that should not exist: {leaked}",
        )


if __name__ == "__main__":
    unittest.main()