"""Local deterministic embedding helpers for semantic scoring.

Phase 1 intentionally avoids external embedding providers. The deterministic
provider gives tests and local runs a stable meaning-aware scorer while keeping
the default lexical path unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from typing import Any

from .storage import DEFAULT_DB_PATH


DEFAULT_EMBEDDING_DIMENSIONS = 64
_ALLOWED_SCORERS = {"lexical", "embedding"}
_LOCAL_PROVIDERS = {"deterministic", "local"}
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
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
    "the",
    "this",
    "to",
    "with",
}
_SYNONYMS = {
    "approved": "approval",
    "approve": "approval",
    "greater": "over",
    "manager": "manager",
    "managers": "manager",
    "need": "require",
    "needed": "require",
    "needs": "require",
    "reimbursement": "refund",
    "reimbursements": "refund",
    "review": "approval",
    "reviewed": "approval",
    "reviewing": "approval",
    "requires": "require",
    "refunds": "refund",
    "supervisor": "manager",
    "supervisors": "manager",
}


def normalize_semantic_policy(value: Any) -> dict[str, Any]:
    """Normalize semantic scoring options without enabling network access."""

    raw = value if isinstance(value, dict) else {}
    scorer = str(raw.get("scorer") or "lexical").strip().lower()
    if scorer not in _ALLOWED_SCORERS:
        scorer = "lexical"
    provider = str(raw.get("provider") or "deterministic").strip().lower()
    if provider not in _LOCAL_PROVIDERS:
        provider = "deterministic"
    return {
        "scorer": scorer,
        "provider": provider,
        "model": str(raw.get("model") or "local-deterministic-v1"),
        "dimensions": _positive_int(raw.get("dimensions"), DEFAULT_EMBEDDING_DIMENSIONS),
        "external": False,
    }


def embed_texts(texts: list[str], policy: dict[str, Any] | None = None) -> list[list[float]]:
    """Return deterministic local embeddings for text blocks."""

    normalized = normalize_semantic_policy(policy)
    dimensions = int(normalized["dimensions"])
    vectors: list[list[float]] = []
    for text in texts:
        cache_key = cache_key_for_embedding(text, normalized)
        vector = _get_cached_embedding(cache_key)
        if vector is None:
            vector = _normalize_vector(_vector_for_text(text, dimensions))
            _set_cached_embedding(cache_key, vector)
        vectors.append(vector)
    return vectors


def cache_key_for_embedding(text: str, policy: dict[str, Any] | None = None) -> str:
    """Return a stable key for local deterministic embedding cache entries."""

    payload = {
        "text": text,
        "policy": normalize_semantic_policy(policy),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "embcache_" + hashlib.sha256(encoded).hexdigest()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for already-normalized or raw vectors."""

    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _vector_for_text(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    for token in _embedding_tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0
    return vector


def _embedding_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _TOKEN_PATTERN.findall(text.lower()):
        token = _canonical_token(raw)
        if token and token not in _STOPWORDS:
            tokens.append(token)
    return tokens


def _canonical_token(token: str) -> str:
    if token in _SYNONYMS:
        return _SYNONYMS[token]
    if len(token) > 4 and token.endswith("ies"):
        token = f"{token[:-3]}y"
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    return _SYNONYMS.get(token, token)


def _normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [round(value / norm, 8) for value in vector]


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _get_cached_embedding(cache_key: str) -> list[float] | None:
    _ensure_embedding_cache()
    conn = _connect_embedding_cache()
    try:
        row = conn.execute(
            "SELECT vector_json FROM embedding_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    parsed = json.loads(row[0])
    if not isinstance(parsed, list):
        return None
    return [float(value) for value in parsed]


def _set_cached_embedding(cache_key: str, vector: list[float]) -> None:
    _ensure_embedding_cache()
    conn = _connect_embedding_cache()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO embedding_cache (cache_key, vector_json, created_at)
            VALUES (?, ?, ?)
            """,
            (
                cache_key,
                json.dumps(vector, ensure_ascii=True, separators=(",", ":")),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_embedding_cache() -> None:
    path = _embedding_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                cache_key TEXT PRIMARY KEY,
                vector_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _connect_embedding_cache() -> sqlite3.Connection:
    return sqlite3.connect(_embedding_cache_path())


def _embedding_cache_path() -> Path:
    return Path(os.environ.get("PROMPTCOMPILER_DB_PATH") or DEFAULT_DB_PATH)
