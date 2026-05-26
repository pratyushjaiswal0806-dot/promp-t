"""SQLite storage for local sessions and metrics."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from .tokenizer import estimate_segment_tokens


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / ".promptcompiler" / "promptcompiler.sqlite3"


class SQLiteStore:
    """Small SQLite boundary for Phase 5 local persistence."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.environ.get("PROMPTCOMPILER_DB_PATH") or DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def record_trace(self, trace: dict[str, Any]) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO request_traces (
                trace_id, endpoint, provider, model, session_id, mode,
                original_token_count, optimized_token_count, token_reduction_percent,
                estimated_cost_before_usd, estimated_cost_after_usd, cache_status,
                evaluation_status, zero_retention, latency_ms, transformations_json,
                retention_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace["trace_id"],
                trace.get("endpoint", "unknown"),
                trace.get("provider"),
                trace.get("model"),
                trace.get("session_id"),
                trace.get("mode"),
                int(trace.get("original_token_count") or 0),
                int(trace.get("optimized_token_count") or 0),
                float(trace.get("token_reduction_percent") or 0),
                float(trace.get("estimated_cost_before_usd") or 0),
                float(trace.get("estimated_cost_after_usd") or 0),
                trace.get("cache_status", "bypass"),
                trace.get("evaluation_status", "not_configured"),
                1 if trace.get("zero_retention") else 0,
                int(trace.get("latency_ms") or 0),
                json.dumps(trace.get("transformations") or [], ensure_ascii=True),
                json.dumps(trace.get("retention") or {}, ensure_ascii=True),
                _now(),
            ),
        )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        row = self._fetchone(
            "SELECT * FROM request_traces WHERE trace_id = ?",
            (trace_id,),
        )
        return _trace_from_row(row) if row else None

    def metrics(self, filters: dict[str, str]) -> dict[str, Any]:
        clauses: list[str] = []
        values: list[Any] = []
        for field in ("provider", "model", "mode", "session_id"):
            if filters.get(field):
                clauses.append(f"{field} = ?")
                values.append(filters[field])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        row = self._fetchone(
            f"""
            SELECT
                COUNT(*) AS requests,
                COALESCE(SUM(original_token_count), 0) AS original_tokens,
                COALESCE(SUM(optimized_token_count), 0) AS optimized_tokens,
                COALESCE(SUM(original_token_count - optimized_token_count), 0) AS tokens_saved,
                COALESCE(SUM(estimated_cost_before_usd), 0.0) AS estimated_cost_before_usd,
                COALESCE(SUM(estimated_cost_after_usd), 0.0) AS estimated_cost_after_usd,
                COALESCE(AVG(latency_ms), 0) AS average_latency_ms
            FROM request_traces
            {where}
            """,
            tuple(values),
        )
        modes = self._fetchall(
            f"""
            SELECT mode, COUNT(*) AS count
            FROM request_traces
            {where}
            GROUP BY mode
            ORDER BY mode
            """,
            tuple(values),
        )
        cache_rows = self._fetchall(
            f"""
            SELECT cache_status, COUNT(*) AS count
            FROM request_traces
            {where}
            GROUP BY cache_status
            """,
            tuple(values),
        )
        session_row = self._fetchone(
            """
            SELECT
                COUNT(*) AS active,
                COALESCE(SUM(current_token_count), 0) AS total_tokens,
                COALESCE(SUM(compaction_count), 0) AS compactions
            FROM sessions
            """
        )

        requests = int(row["requests"] or 0)
        tokens_saved = int(row["tokens_saved"] or 0)
        original_tokens = int(row["original_tokens"] or 0)
        cache_counts = {item["cache_status"]: int(item["count"]) for item in cache_rows}
        cache_hits = int(cache_counts.get("hit", 0))
        return {
            "requests": requests,
            "original_tokens": original_tokens,
            "optimized_tokens": int(row["optimized_tokens"] or 0),
            "tokens_saved": tokens_saved,
            "token_reduction_percent": (
                round((tokens_saved / original_tokens) * 100, 2) if original_tokens else 0.0
            ),
            "estimated_cost_before_usd": round(float(row["estimated_cost_before_usd"] or 0), 8),
            "estimated_cost_after_usd": round(float(row["estimated_cost_after_usd"] or 0), 8),
            "estimated_cost_saved_usd": round(
                float(row["estimated_cost_before_usd"] or 0)
                - float(row["estimated_cost_after_usd"] or 0),
                8,
            ),
            "average_latency_ms": round(float(row["average_latency_ms"] or 0), 2),
            "cache": {
                "hits": cache_hits,
                "misses": int(cache_counts.get("miss", 0)),
                "bypass": int(cache_counts.get("bypass", 0)),
                "disabled": int(cache_counts.get("disabled", 0)),
                "hit_rate": round(cache_hits / requests, 4) if requests else 0.0,
            },
            "modes": {item["mode"]: int(item["count"]) for item in modes},
            "sessions": {
                "active": int(session_row["active"] or 0),
                "total_tokens": int(session_row["total_tokens"] or 0),
                "compactions": int(session_row["compactions"] or 0),
            },
        }

    def append_session_turn(
        self,
        session_id: str,
        provider: str,
        model: str,
        role: str,
        content: str,
        target_token_budget: int | None,
        mode: str,
        zero_retention: bool,
    ) -> dict[str, Any]:
        token_count = estimate_segment_tokens(content)
        pinned = "@pin" in content.lower()
        existing = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session_zero_retention = zero_retention or bool(existing["zero_retention"]) if existing else zero_retention

        if existing:
            if session_zero_retention:
                self._execute(
                    "UPDATE session_turns SET content = NULL WHERE session_id = ?",
                    (session_id,),
                )
            self._execute(
                """
                UPDATE sessions
                SET provider = ?, model = ?, target_token_budget = ?,
                    compression_mode = ?, zero_retention = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    provider,
                    model,
                    target_token_budget,
                    mode,
                    1 if session_zero_retention else 0,
                    _now(),
                    session_id,
                ),
            )
        else:
            self._execute(
                """
                INSERT INTO sessions (
                    id, provider, model, target_token_budget, current_token_count,
                    compression_mode, zero_retention, created_at, updated_at, compaction_count
                )
                VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 0)
                """,
                (
                    session_id,
                    provider,
                    model,
                    target_token_budget,
                    mode,
                    1 if session_zero_retention else 0,
                    _now(),
                    _now(),
                ),
            )

        self._execute(
            """
            INSERT INTO session_turns (
                id, session_id, role, token_count, pinned, content,
                is_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                f"turn_{uuid4().hex}",
                session_id,
                role,
                token_count,
                1 if pinned else 0,
                None if session_zero_retention else content,
                _now(),
            ),
        )
        total_session_tokens = self._session_token_count(session_id)
        self._update_session_count(session_id, total_session_tokens)

        compaction = self._maybe_compact_session(
            session_id=session_id,
            target_token_budget=target_token_budget,
            zero_retention=session_zero_retention,
            total_session_tokens=total_session_tokens,
        )
        session = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return {
            "session_id": session_id,
            "total_session_tokens": total_session_tokens,
            "budget_utilization": _budget_utilization(total_session_tokens, target_token_budget),
            "adaptive_management_triggered": compaction["triggered"],
            "summary_segment_id": compaction["summary_segment_id"],
            "new_total_session_tokens": int(session["current_token_count"]),
            "target_token_budget": target_token_budget,
            "mode": mode,
            "retention": {
                "zero_retention": session_zero_retention,
                "raw_turn_content_stored": not session_zero_retention,
            },
        }

    def session_turn_rows(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._fetchall(
            "SELECT * FROM session_turns WHERE session_id = ? ORDER BY created_at, rowid",
            (session_id,),
        )
        return [dict(row) for row in rows]

    def session_context(
        self,
        session_id: str,
        target_token_budget: int | None,
        sliding_window_turns: int,
    ) -> dict[str, Any]:
        from .session_context import build_compact_session_context

        turns = self.session_turn_rows(session_id)
        return build_compact_session_context(
            turns,
            target_token_budget=target_token_budget,
            sliding_window_turns=sliding_window_turns,
        )

    def get_compile_cache(self, cache_key: str) -> dict[str, Any] | None:
        row = self._fetchone(
            "SELECT response_json FROM compile_cache WHERE cache_key = ?",
            (cache_key,),
        )
        return json.loads(row["response_json"]) if row else None

    def set_compile_cache(self, cache_key: str, response: dict[str, Any]) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO compile_cache (cache_key, response_json, created_at)
            VALUES (?, ?, ?)
            """,
            (cache_key, json.dumps(response, ensure_ascii=True), _now()),
        )

    def _maybe_compact_session(
        self,
        session_id: str,
        target_token_budget: int | None,
        zero_retention: bool,
        total_session_tokens: int,
    ) -> dict[str, Any]:
        if not target_token_budget:
            return {"triggered": False, "summary_segment_id": None}
        if total_session_tokens < int(target_token_budget * 0.7):
            return {"triggered": False, "summary_segment_id": None}

        rows = self.session_turn_rows(session_id)
        non_summary = [row for row in rows if not row["is_summary"]]
        recent_ids = {row["id"] for row in non_summary[-2:]}
        candidates = [
            row
            for row in non_summary
            if not row["pinned"] and row["id"] not in recent_ids
        ]
        if not candidates:
            return {"triggered": False, "summary_segment_id": None}

        removed_tokens = sum(int(row["token_count"]) for row in candidates)
        summary_tokens = max(8, min(80, int(removed_tokens * 0.22)))
        if summary_tokens >= removed_tokens:
            return {"triggered": False, "summary_segment_id": None}

        summary_id = f"seg_summary_{uuid4().hex[:8]}"
        candidate_ids = [row["id"] for row in candidates]
        placeholders = ",".join("?" for _ in candidate_ids)
        self._execute(
            f"DELETE FROM session_turns WHERE id IN ({placeholders})",
            tuple(candidate_ids),
        )
        self._execute(
            """
            INSERT INTO session_turns (
                id, session_id, role, token_count, pinned, content,
                is_summary, created_at
            )
            VALUES (?, ?, 'system', ?, 0, ?, 1, ?)
            """,
            (
                summary_id,
                session_id,
                summary_tokens,
                None if zero_retention else "[session summary] Older low-relevance turns compacted.",
                _now(),
            ),
        )
        new_total = self._session_token_count(session_id)
        self._execute(
            """
            UPDATE sessions
            SET current_token_count = ?, compaction_count = compaction_count + 1,
                updated_at = ?
            WHERE id = ?
            """,
            (new_total, _now(), session_id),
        )
        return {"triggered": True, "summary_segment_id": summary_id}

    def _session_token_count(self, session_id: str) -> int:
        row = self._fetchone(
            "SELECT COALESCE(SUM(token_count), 0) AS total FROM session_turns WHERE session_id = ?",
            (session_id,),
        )
        return int(row["total"] or 0)

    def _update_session_count(self, session_id: str, total: int) -> None:
        self._execute(
            "UPDATE sessions SET current_token_count = ?, updated_at = ? WHERE id = ?",
            (total, _now(), session_id),
        )

    def _initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    provider TEXT,
                    model TEXT,
                    target_token_budget INTEGER,
                    current_token_count INTEGER NOT NULL DEFAULT 0,
                    compression_mode TEXT,
                    zero_retention INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    compaction_count INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS session_turns (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT,
                    token_count INTEGER NOT NULL,
                    pinned INTEGER NOT NULL DEFAULT 0,
                    content TEXT,
                    is_summary INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS request_traces (
                    trace_id TEXT PRIMARY KEY,
                    endpoint TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    session_id TEXT,
                    mode TEXT,
                    original_token_count INTEGER NOT NULL DEFAULT 0,
                    optimized_token_count INTEGER NOT NULL DEFAULT 0,
                    token_reduction_percent REAL NOT NULL DEFAULT 0,
                    estimated_cost_before_usd REAL NOT NULL DEFAULT 0,
                    estimated_cost_after_usd REAL NOT NULL DEFAULT 0,
                    cache_status TEXT NOT NULL DEFAULT 'bypass',
                    evaluation_status TEXT NOT NULL DEFAULT 'not_configured',
                    zero_retention INTEGER NOT NULL DEFAULT 0,
                    latency_ms INTEGER NOT NULL DEFAULT 0,
                    transformations_json TEXT NOT NULL DEFAULT '[]',
                    retention_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS compile_cache (
                    cache_key TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, statement: str, params: tuple[Any, ...] = ()) -> None:
        conn = self._connect()
        try:
            conn.execute(statement, params)
            conn.commit()
        finally:
            conn.close()

    def _fetchone(
        self,
        statement: str,
        params: tuple[Any, ...] = (),
    ) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(statement, params).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _fetchall(
        self,
        statement: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            return [dict(row) for row in conn.execute(statement, params).fetchall()]
        finally:
            conn.close()


def get_store() -> SQLiteStore:
    return SQLiteStore()


def _trace_from_row(row: dict[str, Any]) -> dict[str, Any]:
    original = int(row["original_token_count"] or 0)
    optimized = int(row["optimized_token_count"] or 0)
    return {
        "trace_id": row["trace_id"],
        "endpoint": row["endpoint"],
        "provider": row["provider"],
        "model": row["model"],
        "session_id": row["session_id"],
        "mode": row["mode"],
        "original_token_count": original,
        "optimized_token_count": optimized,
        "tokens_saved": max(0, original - optimized),
        "token_reduction_percent": float(row["token_reduction_percent"] or 0),
        "estimated_cost_before_usd": float(row["estimated_cost_before_usd"] or 0),
        "estimated_cost_after_usd": float(row["estimated_cost_after_usd"] or 0),
        "cache_status": row["cache_status"],
        "evaluation_status": row["evaluation_status"],
        "zero_retention": bool(row["zero_retention"]),
        "latency_ms": int(row["latency_ms"] or 0),
        "transformations": json.loads(row["transformations_json"] or "[]"),
        "retention": json.loads(row["retention_json"] or "{}"),
        "created_at": row["created_at"],
    }


def _budget_utilization(tokens: int, target_token_budget: int | None) -> float | None:
    if not target_token_budget:
        return None
    return round(tokens / target_token_budget, 6)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
