"""Local payload minification helpers."""

from __future__ import annotations

import json
import re
from typing import Any


def compact_json_text(text: str, aliases: dict[str, str] | None = None) -> str:
    value = json.loads(text)
    value = _alias_keys(value, aliases or {})
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def compact_markdown_text(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = re.sub(r"^[-*+]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def structured_input_to_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def maybe_compact_text(
    text: str,
    aliases: dict[str, str] | None = None,
) -> tuple[str, str | None]:
    stripped = text.strip()
    if not stripped:
        return text, None
    if stripped.startswith(("{", "[")):
        try:
            return compact_json_text(stripped, aliases=aliases), "json_minify"
        except json.JSONDecodeError:
            return text, None
    if any(line.lstrip().startswith(("#", "-", "*", "+")) for line in text.splitlines()):
        compacted = compact_markdown_text(text)
        return (compacted, "markdown_plaintext") if len(compacted) < len(text) else (text, None)
    return text, None


def _alias_keys(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {aliases.get(str(key), str(key)): _alias_keys(item, aliases) for key, item in value.items()}
    if isinstance(value, list):
        return [_alias_keys(item, aliases) for item in value]
    return value
