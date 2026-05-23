"""Deterministic prompt compilation.

This module only performs transformations that can be explained locally:
duplicate removal and repeated log-line compaction.
"""

from __future__ import annotations

import re
from typing import Any

from .diff import kept_diff, removed_diff
from .entities import extract_entities
from .models import DEFAULT_NIM_MODEL
from .parser import Segment, parse_prompt
from .tokenizer import estimate_text_tokens


def compile_prompt(raw_input: str, model: str = DEFAULT_NIM_MODEL) -> dict[str, Any]:
    """Compile a prompt with deterministic, safety-first transforms."""

    original_segments = parse_prompt(raw_input)
    changes: list[dict[str, Any]] = []
    diff: list[dict[str, object]] = []
    retained: list[tuple[Segment, str]] = []
    seen: dict[str, str] = {}

    for segment in original_segments:
        normalized = _normalize(segment.text)
        if not segment.pinned and normalized in seen:
            changes.append(
                {
                    "type": "duplicate_removed",
                    "segment_id": segment.id,
                    "kept_segment_id": seen[normalized],
                    "tokens": segment.tokens,
                }
            )
            diff.append(removed_diff(segment, "Exact duplicate of retained unpinned segment."))
            continue

        seen[normalized] = segment.id
        compiled_text = segment.text
        if not segment.pinned:
            compiled_text, compaction_change = _compact_segment(segment)
            if compaction_change:
                changes.append(compaction_change)
        retained.append((segment, compiled_text))
        diff.append(kept_diff(segment, compiled_text))

    optimized_text = "\n\n".join(text for _, text in retained)
    original_tokens = sum(segment.tokens for segment in original_segments)
    optimized_tokens = estimate_text_tokens(optimized_text)
    tokens_saved = max(0, original_tokens - optimized_tokens)

    return {
        "model": model,
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "savings_ratio": round(tokens_saved / original_tokens, 4) if original_tokens else 0,
        "optimized_text": optimized_text,
        "changes": changes,
        "diff": diff,
        "retained_segment_ids": [segment.id for segment, _ in retained],
    }


def _compact_segment(segment: Segment) -> tuple[str, dict[str, Any] | None]:
    compacted, repeated_removed = _compact_repeated_lines(segment.text)
    truncated, truncated_lines = _truncate_large_tool_output(compacted, segment)

    removed = repeated_removed + truncated_lines
    if removed == 0:
        return segment.text, None

    return (
        truncated,
        {
            "type": "segment_compacted",
            "segment_id": segment.id,
            "lines_removed": removed,
            "tokens_before": segment.tokens,
            "tokens_after": estimate_text_tokens(truncated),
        },
    )


def _compact_repeated_lines(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    if len(lines) < 2:
        return text, 0

    output: list[str] = []
    removed = 0
    index = 0
    while index < len(lines):
        current = lines[index]
        repeat_count = 1
        while index + repeat_count < len(lines) and lines[index + repeat_count] == current:
            repeat_count += 1

        output.append(current)
        if repeat_count > 1:
            extra = repeat_count - 1
            removed += extra
            output.append(f"[repeated {extra} more times]")
        index += repeat_count

    return "\n".join(output), removed


def _truncate_large_tool_output(text: str, segment: Segment) -> tuple[str, int]:
    lines = text.splitlines()
    if segment.type not in {"tool", "rag"} or len(lines) <= 80:
        return text, 0

    head = lines[:45]
    middle = lines[45:-10]
    protected_middle = [
        line for line in middle if extract_entities(line) and line not in head and line not in lines[-10:]
    ]
    tail = lines[-10:]
    omitted = len(lines) - len(head) - len(protected_middle) - len(tail)
    marker = f"[omitted {omitted} middle lines]"
    return "\n".join([*head, *protected_middle, marker, *tail]), max(0, omitted)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
