"""Budget-aware retrieval helpers for RAG/search context."""

from __future__ import annotations

import re
from typing import Any


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def select_retrieval_context(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int,
    max_tokens: int,
    similarity_threshold: float = 0.82,
) -> dict[str, Any]:
    query_tokens = _tokens(query)
    scored = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        score = _jaccard(query_tokens, _tokens(text))
        scored.append({**chunk, "score": round(score, 4)})
    scored.sort(key=lambda item: (-float(item["score"]), str(item.get("id") or "")))

    selected: list[dict[str, Any]] = []
    removed: list[str] = []
    used = 0
    for chunk in scored:
        chunk_id = str(chunk.get("id") or "")
        chunk_tokens = int(chunk.get("tokens") or len(_tokens(str(chunk.get("text") or ""))))
        if len(selected) >= top_k or used + chunk_tokens > max_tokens:
            removed.append(chunk_id)
            continue
        if any(
            _jaccard(_tokens(str(item.get("text") or "")), _tokens(str(chunk.get("text") or "")))
            >= similarity_threshold
            for item in selected
        ):
            removed.append(chunk_id)
            continue
        selected.append(chunk)
        used += chunk_tokens
    return {"chunks": selected, "tokens": used, "removed_chunk_ids": removed}


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
