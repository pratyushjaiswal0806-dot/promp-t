"""Tool schema compaction and relevance selection."""

from __future__ import annotations

import re
from typing import Any


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def compact_tool_schema(tool: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key in ("type", "name", "function"):
        if key in tool:
            compacted[key] = tool[key]
    if "description" in tool:
        compacted["description"] = _shorten(str(tool["description"]), 160)
    if "parameters" in tool:
        compacted["parameters"] = _compact_parameters(tool["parameters"])
    return compacted


def select_tools_for_query(
    query: str,
    tools: list[dict[str, Any]],
    max_tools: int = 8,
) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored = []
    for index, tool in enumerate(tools):
        haystack = f"{tool.get('name', '')} {tool.get('description', '')}"
        score = len(query_tokens & _tokens(haystack))
        scored.append((score, index, compact_tool_schema(tool)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [tool for score, _, tool in scored[:max_tools] if score > 0] or [
        tool for _, _, tool in scored[:max_tools]
    ]


def _compact_parameters(value: Any) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if key in {"examples", "example", "$comment"}:
                continue
            if key == "description" and isinstance(item, str):
                output[key] = _shorten(item, 120)
            else:
                output[key] = _compact_parameters(item)
        return output
    if isinstance(value, list):
        return [_compact_parameters(item) for item in value]
    return value


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "."


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}
