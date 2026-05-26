"""Request policy helpers for compact prompt and output behavior."""

from __future__ import annotations

from typing import Any


_ALLOWED_OUTPUT_FORMATS = {"plain", "json", "bullets"}


def normalize_output_policy(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    max_words = _positive_int(raw.get("max_words"), default=None)
    output_format = str(raw.get("format") or "plain").strip().lower()
    if output_format not in _ALLOWED_OUTPUT_FORMATS:
        output_format = "plain"
    explain = bool(raw.get("explain", output_format != "json"))
    parts: list[str] = []
    if max_words:
        parts.append(f"Answer in <={max_words} words.")
    if output_format == "json":
        parts.append("Return JSON only.")
    elif output_format == "bullets":
        parts.append("Return bullet points only.")
    if not explain:
        parts.append("No explanation unless asked.")
    return {
        "max_words": max_words,
        "format": output_format,
        "explain": explain,
        "instruction": " ".join(parts),
    }


def normalize_context_policy(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "system_prompt_ref": _optional_string(raw.get("system_prompt_ref")),
        "cache_static_prefix": bool(raw.get("cache_static_prefix", False)),
        "sliding_window_turns": _positive_int(raw.get("sliding_window_turns"), default=None),
        "summary_token_budget": _positive_int(raw.get("summary_token_budget"), default=None),
        "retrieval_top_k": _positive_int(raw.get("retrieval_top_k"), default=None),
    }


def _positive_int(value: Any, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
