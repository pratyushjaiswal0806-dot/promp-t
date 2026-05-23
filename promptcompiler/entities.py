"""Protected entity extraction for values that should survive compression."""

from __future__ import annotations

import re


_ENTITY_PATTERNS = [
    re.compile(r"https?://[^\s)\"']+"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    re.compile(r"[$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?"),
    re.compile(r"\b\d+(?:\.\d+)?%"),
    re.compile(r"\b[A-Z]{2,}[A-Z0-9]*-\d+[A-Z0-9-]*\b"),
    re.compile(r"(?:>=|<=|>|<)\s?\d+(?:\.\d+)?\b"),
]


def extract_entities(text: str) -> list[str]:
    """Return protected entities in first-seen order."""

    seen: set[str] = set()
    entities: list[str] = []

    for pattern in _ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).rstrip(".,;:")
            if value and value not in seen:
                seen.add(value)
                entities.append(value)

    return entities
