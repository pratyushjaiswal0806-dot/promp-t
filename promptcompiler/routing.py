"""Simple local model routing policy."""

from __future__ import annotations

from typing import Any


_SIMPLE_TASKS = {"grammar", "regex", "summarization", "classification", "formatting", "json_repair"}


def choose_model_route(features: dict[str, Any]) -> dict[str, str]:
    task_type = str(features.get("task_type") or "").strip().lower()
    total_tokens = int(features.get("total_tokens") or 0)
    if task_type in _SIMPLE_TASKS and total_tokens <= 2000:
        return {"tier": "small", "reason": "simple_task", "model_hint": "small"}
    if total_tokens <= 800 and task_type:
        return {"tier": "small", "reason": "short_task", "model_hint": "small"}
    return {"tier": "primary", "reason": "complex_or_large_task", "model_hint": "primary"}
