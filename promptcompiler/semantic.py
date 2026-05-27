"""Local semantic chunking and RAG scoring helpers."""

from __future__ import annotations

import re
from typing import Any

from .embeddings import cosine_similarity, embed_texts, normalize_semantic_policy
from .entities import extract_entities
from .parser import Segment
from .tokenizer import estimate_text_tokens


DEFAULT_WINDOW_TOKENS = 256
DEFAULT_OVERLAP_TOKENS = 32

_SOURCE_PATTERN = re.compile(r"^\s*source\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_CITATION_PATTERN = re.compile(
    r"^\s*(?:citation|cite)\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "does",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "over",
    "the",
    "this",
    "to",
    "with",
}


def chunk_segment(
    segment: Segment,
    window_tokens: int = DEFAULT_WINDOW_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[dict[str, Any]]:
    """Split a segment into sentence-aware chunks with source metadata."""

    source = _first_match(_SOURCE_PATTERN, segment.text)
    citation = _first_match(_CITATION_PATTERN, segment.text)

    if segment.pinned or segment.tokens <= window_tokens:
        return [_chunk_dict(segment, 1, segment.text, source, citation, overlap_tokens=0)]

    units = _sentence_units(segment.text)
    if not units:
        return [_chunk_dict(segment, 1, segment.text, source, citation, overlap_tokens=0)]

    chunks: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = estimate_text_tokens(unit)
        if current and current_tokens + unit_tokens > window_tokens:
            chunks.append(current)
            current = _overlap_tail(current, overlap_tokens)
            current_tokens = sum(estimate_text_tokens(item) for item in current)

        current.append(unit)
        current_tokens += unit_tokens

    if current:
        chunks.append(current)

    return [
        _chunk_dict(
            segment,
            index,
            _join_units(unit_group),
            source,
            citation,
            overlap_tokens=0 if index == 1 else overlap_tokens,
        )
        for index, unit_group in enumerate(chunks, start=1)
    ]


def score_chunks(
    chunks: list[dict[str, Any]],
    query: str,
    semantic_policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return chunks with local relevance, similarity, novelty, and risk scores."""

    policy = normalize_semantic_policy(semantic_policy)
    if policy["scorer"] == "embedding":
        return _score_chunks_with_embeddings(chunks, query, policy)

    return _score_chunks_lexical(chunks, query, policy)


def _score_chunks_lexical(
    chunks: list[dict[str, Any]],
    query: str,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    query_tokens = _semantic_tokens(query)
    token_sets = {chunk["id"]: _semantic_tokens(str(chunk.get("text", ""))) for chunk in chunks}
    scored: list[dict[str, Any]] = []

    for chunk in chunks:
        chunk_id = str(chunk["id"])
        tokens = token_sets[chunk_id]
        relevance = _query_relevance(tokens, query_tokens)
        max_similarity = 0.0
        for other in chunks:
            other_id = str(other["id"])
            if other_id == chunk_id:
                continue
            max_similarity = max(max_similarity, _jaccard(tokens, token_sets[other_id]))

        novelty = 1.0 - max_similarity
        risk = _compression_risk(chunk, relevance, max_similarity)
        scored.append(
            {
                **chunk,
                "query_relevance_score": round(relevance, 4),
                "inter_chunk_similarity_score": round(max_similarity, 4),
                "novelty_score": round(novelty, 4),
                "compression_risk_score": round(risk, 4),
                "decision": "retained",
                "scorer": policy["scorer"],
            }
        )

    return scored


def _score_chunks_with_embeddings(
    chunks: list[dict[str, Any]],
    query: str,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    texts = [str(chunk.get("text", "")) for chunk in chunks]
    vectors = embed_texts([query, *texts], policy)
    query_vector = vectors[0]
    chunk_vectors = vectors[1:]
    scored: list[dict[str, Any]] = []

    for index, chunk in enumerate(chunks):
        chunk_vector = chunk_vectors[index]
        relevance = cosine_similarity(query_vector, chunk_vector)
        max_similarity = 0.0
        for other_index, other_vector in enumerate(chunk_vectors):
            if other_index == index:
                continue
            max_similarity = max(max_similarity, cosine_similarity(chunk_vector, other_vector))

        novelty = 1.0 - max_similarity
        risk = _compression_risk(chunk, relevance, max_similarity)
        scored.append(
            {
                **chunk,
                "query_relevance_score": round(relevance, 4),
                "inter_chunk_similarity_score": round(max_similarity, 4),
                "novelty_score": round(novelty, 4),
                "compression_risk_score": round(risk, 4),
                "decision": "retained",
                "scorer": policy["scorer"],
                "_embedding_vector": chunk_vector,
            }
        )

    return scored


def build_semantic_report(
    segments: list[Segment],
    query: str,
    mode: str,
    semantic_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build semantic scores and safe RAG pruning decisions."""

    policy = normalize_semantic_policy(semantic_policy)
    chunks = [chunk for segment in segments for chunk in chunk_segment(segment)]
    scored = score_chunks(chunks, query, semantic_policy=policy)

    # Extract embedding vectors into separate dict to prevent leaking into output
    embedding_vectors: dict[str, list[float]] = {}
    for chunk in scored:
        vec = chunk.pop("_embedding_vector", None)
        if vec is not None:
            embedding_vectors[str(chunk["id"])] = vec

    by_segment: dict[str, list[dict[str, Any]]] = {}
    for chunk in scored:
        by_segment.setdefault(str(chunk["segment_id"]), []).append(chunk)

    decisions: list[dict[str, Any]] = []
    removed_chunk_ids: set[str] = set()
    removed_segment_ids: set[str] = set()

    if mode in {"balanced", "aggressive"}:
        threshold = 0.78 if mode == "balanced" else 0.62
        retained_rag: list[dict[str, Any]] = []
        rag_chunks = [chunk for chunk in scored if chunk.get("segment_type") == "rag"]
        rag_chunks.sort(
            key=lambda item: (
                -float(item["query_relevance_score"]),
                int(item["segment_order"]),
                int(item["chunk_index"]),
            )
        )

        for chunk in rag_chunks:
            if chunk.get("pinned"):
                retained_rag.append(chunk)
                continue

            cross_segment_retained = [
                c for c in retained_rag if c["segment_id"] != chunk["segment_id"]
            ]
            redundant_with = _similar_retained_chunk(chunk, cross_segment_retained, threshold, policy, embedding_vectors)
            if (
                redundant_with is not None
                and float(chunk["query_relevance_score"])
                <= float(redundant_with["query_relevance_score"]) + 0.0001
                and not _has_unique_entities(chunk, retained_rag)
            ):
                chunk["decision"] = "removed"
                chunk["redundant_with"] = redundant_with["id"]
                removed_chunk_ids.add(str(chunk["id"]))
                removed_segment_ids.add(str(chunk["segment_id"]))
                decisions.append(
                    {
                        "action": "rag_prune",
                        "segment_ids": [chunk["segment_id"]],
                        "chunk_ids": [chunk["id"]],
                        "retained_chunk_id": redundant_with["id"],
                        "reason": (
                            "Removed redundant RAG chunk with equivalent query relevance "
                            "and no unique protected values."
                        ),
                        "estimated_tokens_saved": chunk["tokens"],
                    }
                )
                continue

            retained_rag.append(chunk)

    public_scored = [_public_chunk(chunk) for chunk in scored]
    retained_chunk_ids = [str(chunk["id"]) for chunk in scored if chunk["id"] not in removed_chunk_ids]
    retained_segment_ids = [
        segment.id for segment in segments if segment.id not in removed_segment_ids
    ]
    return {
        "query": query,
        "scorer": policy["scorer"],
        "provider": policy["provider"],
        "model": policy["model"],
        "external": policy["external"],
        "chunks": public_scored,
        "removed_chunk_ids": sorted(removed_chunk_ids),
        "retained_chunk_ids": retained_chunk_ids,
        "removed_segment_ids": sorted(removed_segment_ids),
        "retained_segment_ids": retained_segment_ids,
        "decisions": decisions,
        "summary": {
            "total_chunks": len(scored),
            "rag_chunks": sum(1 for chunk in scored if chunk.get("segment_type") == "rag"),
            "removed_chunks": len(removed_chunk_ids),
            "retained_chunks": len(retained_chunk_ids),
        },
    }


def _chunk_dict(
    segment: Segment,
    chunk_index: int,
    text: str,
    source: str,
    citation: str,
    overlap_tokens: int,
) -> dict[str, Any]:
    return {
        "id": f"{segment.id}_chunk_{chunk_index}",
        "segment_id": segment.id,
        "segment_order": int(segment.id.split("_")[-1] or 0),
        "chunk_index": chunk_index,
        "segment_type": segment.type,
        "role": segment.role,
        "text": text,
        "tokens": estimate_text_tokens(text),
        "source": source,
        "citation": citation,
        "entities": extract_entities(text),
        "pinned": segment.pinned,
        "overlap_tokens": overlap_tokens,
    }


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _sentence_units(text: str) -> list[str]:
    units: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _SOURCE_PATTERN.match(stripped) or _CITATION_PATTERN.match(stripped):
            units.append(stripped)
            continue
        parts = re.split(r"(?<=[.!?])\s+", stripped)
        units.extend(part.strip() for part in parts if part.strip())
    return units


def _overlap_tail(units: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0:
        return []

    output: list[str] = []
    total = 0
    for unit in reversed(units):
        unit_tokens = estimate_text_tokens(unit)
        if output and total + unit_tokens > overlap_tokens:
            break
        output.insert(0, unit)
        total += unit_tokens
    return output


def _join_units(units: list[str]) -> str:
    return " ".join(units).strip()


def _semantic_tokens(text: str) -> set[str]:
    content = "\n".join(
        line
        for line in text.splitlines()
        if not (_SOURCE_PATTERN.match(line.strip()) or _CITATION_PATTERN.match(line.strip()))
    )
    tokens: set[str] = set()
    for raw in _TOKEN_PATTERN.findall(content.lower()):
        token = _normalize_token(raw)
        if token and token not in _STOPWORDS:
            tokens.add(token)
    return tokens


def _normalize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _query_relevance(tokens: set[str], query_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(tokens & query_tokens) / len(query_tokens)


def _jaccard(first: set[str], second: set[str]) -> float:
    if not first and not second:
        return 1.0
    if not first or not second:
        return 0.0
    return len(first & second) / len(first | second)


def _compression_risk(chunk: dict[str, Any], relevance: float, similarity: float) -> float:
    risk = (1.0 - relevance) * 0.35 + similarity * 0.25
    if chunk.get("entities"):
        risk += 0.2
    if chunk.get("pinned"):
        risk += 0.4
    if chunk.get("source") or chunk.get("citation"):
        risk += 0.08
    return min(1.0, risk)


def _similar_retained_chunk(
    chunk: dict[str, Any],
    retained: list[dict[str, Any]],
    threshold: float,
    policy: dict[str, Any],
    embedding_vectors: dict[str, list[float]] | None = None,
) -> dict[str, Any] | None:
    if policy["scorer"] == "embedding":
        chunk_vector = (embedding_vectors or {}).get(chunk.get("id", ""))
        if not isinstance(chunk_vector, list):
            return None
        best: dict[str, Any] | None = None
        best_similarity = 0.0
        for candidate in retained:
            candidate_vector = (embedding_vectors or {}).get(candidate.get("id", ""))
            if not isinstance(candidate_vector, list):
                continue
            similarity = cosine_similarity(chunk_vector, candidate_vector)
            if similarity >= threshold and similarity > best_similarity:
                best = candidate
                best_similarity = similarity
        return best

    chunk_tokens = _semantic_tokens(str(chunk.get("text", "")))
    best: dict[str, Any] | None = None
    best_similarity = 0.0
    for candidate in retained:
        similarity = _jaccard(chunk_tokens, _semantic_tokens(str(candidate.get("text", ""))))
        if similarity >= threshold and similarity > best_similarity:
            best = candidate
            best_similarity = similarity
    return best


def _public_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in chunk.items() if not key.startswith("_")}


def _has_unique_entities(chunk: dict[str, Any], retained: list[dict[str, Any]]) -> bool:
    entities = set(chunk.get("entities") or [])
    if not entities:
        return False

    retained_entities = {
        entity
        for candidate in retained
        for entity in (candidate.get("entities") or [])
    }
    return bool(entities - retained_entities)
