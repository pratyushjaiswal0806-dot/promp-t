"""SummarizePass — compress long segments while preserving entities."""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any

from promptcompiler.entities import extract_entities
from promptcompiler.ir import ContextGraph, ContextRole, SegmentType
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry
from promptcompiler.tokenizer import estimate_segment_tokens

_ENTITY_LINE_CACHE: dict[str, bool] = {}

_ALLOWED_MODES = {"lossless": 0, "balanced": 1, "aggressive": 2}


def _has_entity(line: str) -> bool:
    key = line[:80]
    if key not in _ENTITY_LINE_CACHE:
        _ENTITY_LINE_CACHE[key] = bool(extract_entities(line))
    return _ENTITY_LINE_CACHE[key]


def _compact_repeated_lines(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    if len(lines) < 2:
        return text, 0
    output: list[str] = []
    removed = 0
    i = 0
    while i < len(lines):
        cur = lines[i]
        repeat = 1
        while i + repeat < len(lines) and lines[i + repeat] == cur:
            repeat += 1
        output.append(cur)
        if repeat > 1:
            extra = repeat - 1
            removed += extra
            output.append(f"[repeated {extra} more times]")
        i += repeat
    return "\n".join(output), removed


def _truncate_tool_output(text: str, mode_int: int) -> tuple[str, int]:
    lines = text.splitlines()
    configs = [(80, 45, 10), (36, 18, 6), (22, 10, 4)]
    max_lines, head_count, tail_count = configs[min(mode_int, len(configs) - 1)]
    if len(lines) <= max_lines:
        return text, 0
    head = lines[:head_count]
    tail = lines[-tail_count:] if tail_count else []
    middle = lines[head_count:-tail_count]
    protected = [l for l in middle if _has_entity(l) and l not in head and l not in tail]
    omitted = len(lines) - len(head) - len(protected) - len(tail)
    marker = f"[omitted {omitted} middle lines]"
    return "\n".join([*head, *protected, marker, *tail]), max(0, omitted)


def _summarize_tool_output(text: str, mode_int: int, role: ContextRole) -> tuple[str, int]:
    """Summarise verbose tool/rag output into a compact block preserving entities."""
    if mode_int == 0:
        return text, 0

    tokens = estimate_segment_tokens(text)
    threshold = 18 if mode_int == 1 else 12
    if tokens <= threshold:
        return text, 0

    if not any(_has_entity(line) for line in text.splitlines()):
        return text, 0

    protected_lines = [line for line in text.splitlines() if _has_entity(line)]
    summary_lines = [
        "[tool summary]",
        *protected_lines,
    ]
    summary = "\n".join(OrderedDict.fromkeys(line for line in summary_lines if line.strip()))
    return summary, max(0, tokens - estimate_segment_tokens(summary))


def _summarize_long(text: str, role: ContextRole, segment_type: SegmentType, mode_int: int, index: int, total: int) -> tuple[str, int]:
    """Summarise older user/assistant context beyond the threshold."""

    if role in (ContextRole.SYSTEM, ContextRole.TOOL_OUTPUT) or segment_type == SegmentType.CODE:
        return text, 0
    if mode_int == 0:
        return text, 0
    if index >= max(0, total - 2):
        return text, 0

    tokens = estimate_segment_tokens(text)
    threshold = 90 if mode_int == 1 else 45
    if tokens <= threshold:
        return text, 0

    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = parts[:2] if mode_int == 1 else parts[:1]
    protected = [l for l in text.splitlines() if _has_entity(l)]
    combined = [p for p in [*kept, *protected] if p.strip()]
    summary = "\n".join(OrderedDict.fromkeys(combined))
    if not summary:
        summary = text[:240]
    summary = f"[summarized older context]\n{summary}"
    saved = max(0, tokens - estimate_segment_tokens(summary))
    return summary, saved


@PassRegistry.register
class SummarizePass:
    """Compress long segments via repeat-collapse, tool truncation, and summarization.

    Operates only on unpinned segments.  Entity-preserving lines are kept.
    """

    pass_id = "summarize.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["normalize.v1"]

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        mode_str = graph.pipeline_config.get("mode", "lossless")
        mode_int = _ALLOWED_MODES.get(mode_str, 0)
        total = len(graph.segments)

        total_saved = 0
        affected = 0

        for idx, (seg_id, seg) in enumerate(graph.segments.items()):
            if seg.metadata.is_pinned:
                continue

            original = seg.text
            actions_taken: list[str] = []

            # 1) Repeated lines
            text, r_removed = _compact_repeated_lines(original)
            if r_removed:
                actions_taken.append(f"repeat_collapse({r_removed})")

            # 2) Tool output truncation — long text segments treated as tool output
            is_tool_like = (
                seg.context_role == ContextRole.TOOL_OUTPUT
                or len(seg.text.splitlines()) > 20
            )
            if is_tool_like:
                text, t_removed = _truncate_tool_output(text, mode_int)
                if t_removed:
                    actions_taken.append(f"tool_truncate({t_removed})")

            # 3) Tool summarization — compact verbose output
            if is_tool_like:
                text, s_removed = _summarize_tool_output(text, mode_int, seg.context_role)
                if s_removed:
                    actions_taken.append(f"tool_summary({s_removed})")

            # 4) History summarization
            text, h_removed = _summarize_long(text, seg.context_role, seg.segment_type, mode_int, idx, total)
            if h_removed:
                actions_taken.append(f"summarize({h_removed})")

            if not actions_taken:
                continue

            tokens_before = seg.metadata.tokens_after or estimate_segment_tokens(seg.text)
            tokens_after = estimate_segment_tokens(text)
            saved = tokens_before - tokens_after

            seg.text = text
            seg.metadata.tokens_after = tokens_after
            seg.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason="; ".join(actions_taken),
                metadata={"token_delta": -saved},
            ))
            total_saved += saved
            affected += 1

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="SUMMARIZE_COMPLETE",
            message=f"Compressed {affected} segments, saved ~{total_saved} tokens (mode={mode_str})",
        ))
        return graph
