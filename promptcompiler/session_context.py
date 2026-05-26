"""Build compact session context from stored turns."""

from __future__ import annotations

from typing import Any


def build_compact_session_context(
    turns: list[dict[str, Any]],
    target_token_budget: int | None,
    sliding_window_turns: int = 4,
) -> dict[str, Any]:
    budget = target_token_budget or sum(int(row.get("token_count") or 0) for row in turns)
    non_summary = [row for row in turns if not row.get("is_summary")]
    recent_ids = {str(row["id"]) for row in non_summary[-max(1, sliding_window_turns) :]}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in turns:
        row_id = str(row["id"])
        if row.get("pinned") or row.get("is_summary") or row_id in recent_ids:
            if row_id not in seen:
                selected.append(row)
                seen.add(row_id)

    trimmed: list[dict[str, Any]] = []
    used = 0
    for row in selected:
        tokens = int(row.get("token_count") or 0)
        if row.get("pinned") or used + tokens <= budget:
            trimmed.append(row)
            used += tokens

    return {
        "strategy": "pinned_summary_recent",
        "token_count": used,
        "messages": [
            {
                "role": str(row.get("role") or "user"),
                "content": str(row.get("content") or ""),
                "source_turn_id": str(row.get("id")),
                "token_count": int(row.get("token_count") or 0),
                "pinned": bool(row.get("pinned")),
                "is_summary": bool(row.get("is_summary")),
            }
            for row in trimmed
            if row.get("content")
        ],
    }
