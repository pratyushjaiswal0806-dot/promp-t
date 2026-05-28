"""Prompt parsing for raw text and OpenAI-compatible messages."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from .entities import extract_entities
from .tokenizer import estimate_segment_tokens


@dataclass(frozen=True)
class Segment:
    id: str
    type: str
    role: str
    text: str
    tokens: int
    pinned: bool
    entities: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "role": self.role,
            "text": self.text,
            "tokens": self.tokens,
            "pinned": self.pinned,
            "entities": self.entities,
        }


def parse_prompt(raw_input: str) -> list[Segment]:
    """Parse raw text, a messages array, or an object with messages."""

    stripped = raw_input.strip()
    if not stripped:
        return []

    parsed = _try_parse_json(stripped)
    if isinstance(parsed, dict) and isinstance(parsed.get("messages"), list):
        return _segments_from_messages(parsed["messages"])
    if isinstance(parsed, list) and _looks_like_messages(parsed):
        return _segments_from_messages(parsed)

    return _segments_from_text(raw_input)


def _try_parse_json(value: str) -> Any | None:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _looks_like_messages(value: list[Any]) -> bool:
    return all(isinstance(item, dict) and "content" in item for item in value)


def _segments_from_messages(messages: list[dict[str, Any]]) -> list[Segment]:
    segments: list[Segment] = []
    for index, message in enumerate(messages, start=1):
        role = str(message.get("role") or "unknown")
        text = _content_to_text(message.get("content", ""))
        segments.append(_make_segment(index, role, _type_from_role(role), text))
    return segments


def _segments_from_text(text: str) -> list[Segment]:
    blocks = _split_text_blocks(text)
    return [
        _make_segment(index, _role_from_text(block), _type_from_text(block), block)
        for index, block in enumerate(blocks, start=1)
    ]


def _split_text_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code = False

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            current.append(line)
            continue
        if not in_code and not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())

    return [block for block in blocks if block]


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return json.dumps(content, ensure_ascii=True, sort_keys=True)


def _type_from_role(role: str) -> str:
    normalized = role.lower()
    if normalized in {"system", "developer", "user", "assistant", "tool"}:
        return "tool" if normalized == "tool" else normalized
    return "text"


def _type_from_text(text: str) -> str:
    lower = text.lower()
    if lower.startswith(("error", "traceback", "warning")) or "\nerror" in lower:
        return "tool"
    if "source:" in lower or "citation" in lower:
        return "rag"
    if lower.startswith(("system:", "system prompt", "you are", "your role")):
        return "system"
    if lower.startswith(("task:", "goal:", "objective:", "instruction:")):
        return "text"
    if re.match(r"^(?:POST|GET|PUT|DELETE|PATCH|WebSocket)\s+/", text.strip()):
        return "text"
    if re.match(r"^\d+\.\s+\w", text.strip()):
        return "text"
    return "text"


def _role_from_text(text: str) -> str:
    lower = text.lower()
    if lower.startswith(("system:", "system prompt")):
        return "system"
    if lower.startswith(("user:", "human:")):
        return "user"
    if lower.startswith(("assistant:", "ai:", "bot:")):
        return "assistant"
    if lower.startswith(("task:", "goal:", "objective:")):
        return "user"
    return "unknown"


def _make_segment(index: int, role: str, segment_type: str, text: str) -> Segment:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return Segment(
        id=f"seg_{content_hash}_{index}",
        type=segment_type,
        role=role,
        text=text,
        tokens=estimate_segment_tokens(text),
        pinned="@pin" in text.lower(),
        entities=extract_entities(text),
    )
