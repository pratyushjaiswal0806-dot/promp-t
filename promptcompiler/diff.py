"""Segment-level diff helpers for compile reports."""

from __future__ import annotations

from .parser import Segment


def kept_diff(segment: Segment, optimized_text: str) -> dict[str, object]:
    status = "kept" if optimized_text == segment.text else "changed"
    return {
        "segment_id": segment.id,
        "status": status,
        "type": segment.type,
        "role": segment.role,
        "pinned": segment.pinned,
        "original_text": segment.text,
        "optimized_text": optimized_text,
    }


def removed_diff(segment: Segment, reason: str) -> dict[str, object]:
    return {
        "segment_id": segment.id,
        "status": "removed",
        "type": segment.type,
        "role": segment.role,
        "pinned": segment.pinned,
        "reason": reason,
        "original_text": segment.text,
        "optimized_text": "",
    }
