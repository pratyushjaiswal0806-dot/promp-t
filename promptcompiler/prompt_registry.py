"""Small local registry for reusable system prompt instructions."""

from __future__ import annotations

from typing import Any


_BUILTINS: dict[str, str] = {
    "concise": "Be concise.",
    "json_only": "Return JSON only.",
    "bullets_only": "Return bullet points only.",
    "no_explanation": "No explanation unless asked.",
}


def list_system_prompts() -> list[dict[str, str]]:
    return [{"id": key, "content": value} for key, value in sorted(_BUILTINS.items())]


def expand_system_prompt_ref(prompt_ref: str | None) -> dict[str, Any] | None:
    if not prompt_ref:
        return None
    key = str(prompt_ref).strip()
    if not key:
        return None
    if key not in _BUILTINS:
        raise ValueError(f"Unknown system_prompt_ref: {key}")
    return {"id": key, "content": _BUILTINS[key], "source": "builtin"}
