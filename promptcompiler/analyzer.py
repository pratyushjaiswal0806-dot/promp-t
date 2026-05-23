"""Prompt analysis: token allocation, duplicates, and protected entities."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from .models import DEFAULT_NIM_MODEL
from .parser import Segment, parse_prompt


def analyze_prompt(raw_input: str, model: str = DEFAULT_NIM_MODEL) -> dict[str, Any]:
    """Analyze prompt structure and return JSON-serializable metrics."""

    segments = parse_prompt(raw_input)
    total_tokens = sum(segment.tokens for segment in segments)
    duplicate_groups = _duplicate_groups(segments)
    duplicate_tokens = _duplicate_token_count(segments, duplicate_groups)

    by_type = _sum_by(segments, "type")
    by_role = _sum_by(segments, "role")
    protected_entities = _unique_entities(segments)

    return {
        "model": model,
        "total_tokens": total_tokens,
        "segment_count": len(segments),
        "by_type": by_type,
        "by_role": by_role,
        "largest_segments": [
            segment.to_dict()
            for segment in sorted(segments, key=lambda item: item.tokens, reverse=True)[:5]
        ],
        "duplicate_groups": duplicate_groups,
        "protected_entities": protected_entities,
        "compression_opportunity": round(duplicate_tokens / total_tokens, 4) if total_tokens else 0,
        "segments": [segment.to_dict() for segment in segments],
    }


def _sum_by(segments: list[Segment], attr: str) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for segment in segments:
        totals[str(getattr(segment, attr))] += segment.tokens
    return dict(sorted(totals.items()))


def _duplicate_groups(segments: list[Segment]) -> list[dict[str, Any]]:
    buckets: dict[str, list[Segment]] = defaultdict(list)
    for segment in segments:
        buckets[_normalize(segment.text)].append(segment)

    groups: list[dict[str, Any]] = []
    for items in buckets.values():
        if len(items) < 2:
            continue
        groups.append(
            {
                "text": items[0].text,
                "count": len(items),
                "segment_ids": [item.id for item in items],
                "tokens": sum(item.tokens for item in items),
            }
        )

    return sorted(groups, key=lambda group: group["tokens"], reverse=True)


def _duplicate_token_count(
    segments: list[Segment],
    duplicate_groups: list[dict[str, Any]],
) -> int:
    by_id = {segment.id: segment.tokens for segment in segments}
    duplicate_tokens = 0
    for group in duplicate_groups:
        duplicate_ids = group["segment_ids"][1:]
        duplicate_tokens += sum(by_id[segment_id] for segment_id in duplicate_ids)
    return duplicate_tokens


def _unique_entities(segments: list[Segment]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for segment in segments:
        for entity in segment.entities:
            if entity not in seen:
                seen.add(entity)
                values.append(entity)
    return values


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
