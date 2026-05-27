"""ParsePass — raw input to IR ContextGraph.

Port of the existing :mod:`promptcompiler.parser` into the v2 pass pipeline.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from promptcompiler.ir import ContextGraph, ContextRole, Segment, SegmentType, SourceRef, NodeMetadata
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry
from promptcompiler.tokenizer import estimate_segment_tokens
from promptcompiler.entities import extract_entities

_ROLE_MAP: dict[str, ContextRole] = {
    "system": ContextRole.SYSTEM,
    "developer": ContextRole.SYSTEM,
    "user": ContextRole.USER,
    "assistant": ContextRole.ASSISTANT,
    "tool": ContextRole.TOOL_OUTPUT,
}


@PassRegistry.register
class ParsePass:
    """Convert raw prompt text / messages array into a ContextGraph."""

    pass_id = "parse.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = []

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        raw = graph.data.get("raw_input", "")
        if not raw.strip():
            return graph

        parsed = self._try_parse_json(raw.strip())
        if isinstance(parsed, dict) and isinstance(parsed.get("messages"), list):
            segments = self._from_messages(parsed["messages"])
        elif isinstance(parsed, list) and self._looks_like_messages(parsed):
            segments = self._from_messages(parsed)
        else:
            segments = self._from_text(raw)

        for seg in segments:
            graph.add_segment(seg)

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="PARSE_COMPLETE",
            message=f"Parsed {len(segments)} segments from input",
        ))
        return graph

    # ------------------------------------------------------------------
    # Messages path
    # ------------------------------------------------------------------

    def _from_messages(self, messages: list[dict[str, Any]]) -> list[Segment]:
        segments: list[Segment] = []
        for index, msg in enumerate(messages, start=1):
            role = str(msg.get("role") or "unknown")
            text = self._content_to_text(msg.get("content", ""))
            segments.append(self._make_segment(index, role, text))
        return segments

    # ------------------------------------------------------------------
    # Plain text path
    # ------------------------------------------------------------------

    def _from_text(self, text: str) -> list[Segment]:
        blocks = self._split_text_blocks(text)
        return [
            self._make_segment(index, "unknown", block)
            for index, block in enumerate(blocks, start=1)
        ]

    @staticmethod
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
        return [b for b in blocks if b]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _try_parse_json(value: str) -> Any | None:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _looks_like_messages(value: list) -> bool:
        return all(isinstance(item, dict) and "content" in item for item in value)

    @staticmethod
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

    @staticmethod
    def _infer_role(role_str: str) -> ContextRole:
        return _ROLE_MAP.get(role_str.lower(), ContextRole.UNKNOWN)

    @staticmethod
    def _infer_segment_type(text: str) -> SegmentType:
        lower = text.lower()
        if lower.startswith(("error", "traceback", "warning")) or "\nerror" in lower:
            return SegmentType.TEXT  # tool output, but represented as TEXT
        return SegmentType.TEXT

    def _make_segment(self, index: int, role_str: str, text: str) -> Segment:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        tokens = estimate_segment_tokens(text)
        entities = extract_entities(text)
        seg = Segment(
            id=f"seg_{content_hash}_{index}",
            text=text,
            segment_type=self._infer_segment_type(text),
            context_role=self._infer_role(role_str),
            metadata=NodeMetadata(
                tokens_original=tokens,
                tokens_after=tokens,
                is_pinned="@pin" in text.lower(),
            ),
        )
        seg.metadata.entity_ids = {f"ent_{i}" for i in entities}
        return seg
