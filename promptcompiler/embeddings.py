"""Local deterministic embeddings backed by SimHash (64-bit) fingerprints.

Phase 1 intentionally avoids external embedding providers.  The deterministic
provider uses SimHash (64-bit) to produce stable, meaning-aware fingerprints
for semantic scoring in tests and local runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


DEFAULT_FINGERPRINT_BITS = 64
_ALLOWED_SCORERS = {"lexical", "embedding"}
_LOCAL_PROVIDERS = {"deterministic", "local"}
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "by", "can",
    "do", "does", "for", "from", "if", "in", "is", "it", "of", "on",
    "or", "the", "this", "to", "with",
}
_SYNONYMS = {
    "approved": "approval", "approve": "approval",
    "greater": "over",
    "manager": "manager", "managers": "manager",
    "need": "require", "needed": "require", "needs": "require",
    "reimbursement": "refund", "reimbursements": "refund",
    "review": "approval", "reviewed": "approval", "reviewing": "approval",
    "requires": "require", "refunds": "refund",
    "supervisor": "manager", "supervisors": "manager",
}


@dataclass
class FingerprintStore:
    """SQLite-backed cache for SimHash fingerprints and weight vectors."""

    db_path: Path = field(default_factory=lambda: Path(
        os.environ.get("PROMPTCOMPILER_DB_PATH") or DEFAULT_DB_PATH,
    ))

    def __post_init__(self) -> None:
        self._ensure()

    def get(self, cache_key: str) -> tuple[int, list[int]] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT fingerprint, weights_json FROM fingerprint_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        fp: int = row[0]
        weights: list[int] = json.loads(row[1])
        return fp, weights

    def set(self, cache_key: str, fingerprint: int, weights: list[int]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO fingerprint_cache (cache_key, fingerprint, weights_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (cache_key, fingerprint,
                 json.dumps(weights, separators=(",", ":")),
                 datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _ensure(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        has_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fingerprint_cache'"
        ).fetchone()
        if has_table:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(fingerprint_cache)")}
            if "weights_json" not in cols:
                conn.execute("DROP TABLE fingerprint_cache")
                conn.execute(
                    "CREATE TABLE fingerprint_cache ("
                    "  cache_key TEXT PRIMARY KEY,"
                    "  fingerprint INTEGER NOT NULL,"
                    "  weights_json TEXT NOT NULL DEFAULT '[]',"
                    "  created_at TEXT NOT NULL"
                    ")"
                )
                conn.commit()
        else:
            conn.execute(
                "CREATE TABLE fingerprint_cache ("
                "  cache_key TEXT PRIMARY KEY,"
                "  fingerprint INTEGER NOT NULL,"
                "  weights_json TEXT NOT NULL DEFAULT '[]',"
                "  created_at TEXT NOT NULL"
                ")"
            )
            conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# SimHash 64-bit
# ---------------------------------------------------------------------------

def _simhash_weights(text: str) -> tuple[int, list[int]]:
    """Return (fingerprint, weight_vector) for *text*.

    *weight_vector* holds the accumulated +1/-1 per bit position and is
    suitable as an L2-normalised embedding vector for cosine similarity.
    """
    v = [0] * 64
    for token in _embedding_tokens(text):
        h_bytes = hashlib.sha256(token.encode("utf-8")).digest()[:8]
        h_int = int.from_bytes(h_bytes, "big")
        for i in range(64):
            if h_int & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= 1 << i
    return fingerprint, v


def _fingerprint_similarity(a: int, b: int) -> float:
    """Return similarity in [0, 1] from Hamming distance of two 64-bit ints."""
    return 1.0 - ((a ^ b).bit_count() / 64.0)


# ---------------------------------------------------------------------------
# Public API  (unchanged signatures for backward compatibility)
# ---------------------------------------------------------------------------

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
        "dimensions": _positive_int(raw.get("dimensions"), DEFAULT_FINGERPRINT_BITS),
        "external": False,
    }


_FINGERPRINT_STORE: FingerprintStore | None = None
_FINGERPRINT_STORE_PATH: str = ""


def _get_store() -> FingerprintStore:
    global _FINGERPRINT_STORE, _FINGERPRINT_STORE_PATH
    current_path = os.environ.get("PROMPTCOMPILER_DB_PATH") or str(DEFAULT_DB_PATH)
    if _FINGERPRINT_STORE is None or current_path != _FINGERPRINT_STORE_PATH:
        _FINGERPRINT_STORE = FingerprintStore(db_path=Path(current_path))
        _FINGERPRINT_STORE_PATH = current_path
    return _FINGERPRINT_STORE


def embed_texts(texts: list[str], policy: dict[str, Any] | None = None) -> list[list[float]]:
    """Return deterministic local embeddings for text blocks.

    The underlying representation is a SimHash 64-bit fingerprint with its
    associated weight vector, returned as an L2-normalised float vector for
    backward compatibility with consumers that expect ``cosine_similarity``.
    """
    normalized = normalize_semantic_policy(policy)
    dimensions = int(normalized["dimensions"])
    store = _get_store()
    vectors: list[list[float]] = []
    for text in texts:
        key = cache_key_for_embedding(text, normalized)
        cached = store.get(key)
        if cached is not None:
            _, weights = cached
        else:
            fp, weights = _simhash_weights(text)
            store.set(key, fp, weights)
        vector = _weights_to_vector(weights, dimensions)
        vectors.append(vector)
    return vectors


def cache_key_for_embedding(text: str, policy: dict[str, Any] | None = None) -> str:
    """Return a stable cache key for fingerprint entries."""
    payload = {
        "text": text,
        "policy": normalize_semantic_policy(policy),
    }
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "fp_" + hashlib.sha256(encoded).hexdigest()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for pre-normalized vectors (dot product only)."""
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


# ---------------------------------------------------------------------------
# Helper: tokenisation (shared with previous implementation)
# ---------------------------------------------------------------------------

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


def _weights_to_vector(weights: list[int], dimensions: int) -> list[float]:
    """Map 64 weights into a *dimensions*-length L2-normalised float vector.

    When *dimensions* < 64, multiple bit-positions fold into the same
    coordinate by simple addition.
    """
    vec = [0.0] * dimensions
    for i, w in enumerate(weights):
        vec[i % dimensions] += float(w)
    norm = math.sqrt(sum(v * v for v in vec))
    if norm:
        vec = [round(v / norm, 8) for v in vec]
    return vec


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
