# TRD Gap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the eight high-value TRD gaps: real tokenizer routing, richer entity fingerprinting, Layer 1 retention scoring, request/session dashboard pages, side-by-side diff and heatmap, live OpenAI proxy forwarding, safe semantic cache, and a regression benchmark suite.

**Architecture:** Keep the current local-first standard-library Python server and static frontend for this plan. Add focused backend modules with optional external integrations, then expose their metadata through the existing `/v1/*` API and dashboard. Use deterministic fallbacks whenever optional packages, Redis, or provider keys are unavailable.

**Tech Stack:** Python 3 standard library, optional `tiktoken`, optional Redis client/server, optional OpenAI-compatible upstream API key, static HTML/CSS/JavaScript, SQLite local storage, `unittest`, headless Chrome E2E.

---

## Scope And Sequencing

This plan is intentionally split so each task can ship independently:

1. Add benchmark fixtures first so later savings/safety changes have a baseline.
2. Add tokenizer routing and wire it into API metadata.
3. Expand entity extraction into typed fingerprints.
4. Replace placeholder retention scoring with deterministic Layer 1 scoring.
5. Add a safe semantic cache boundary with SQLite fallback and Redis adapter.
6. Expand the static dashboard into request/session/cache/settings/integration views.
7. Add richer side-by-side diff and token heatmap display.
8. Add live OpenAI-compatible proxy forwarding with safe fallback to mock mode.
9. Run final integration verification and update docs.

Manual prerequisites for full behavior:

- Install `tiktoken` to get exact OpenAI counts. Without it, tokenizer metadata must report conservative fallback estimates.
- Install and run Redis to exercise the Redis semantic cache. Without it, tests must still pass through the SQLite/local fallback.
- Provide an OpenAI-compatible API key and base URL to test live proxy forwarding. Without it, proxy tests must use mocked upstream HTTP.

## File Structure

Create:

- `promptcompiler/tokenizers.py`: provider/model tokenizer router and adapters.
- `promptcompiler/fingerprints.py`: typed entity fingerprint creation and comparison.
- `promptcompiler/retention.py`: Layer 1 retention scoring helpers.
- `promptcompiler/semantic_cache.py`: safe cache lookup/write boundary with local and Redis adapters.
- `promptcompiler/benchmarks.py`: benchmark runner helpers for golden/adversarial prompts.
- `tests/fixtures/benchmarks/*.json`: golden and adversarial benchmark cases.
- `tests/test_tokenizers.py`: tokenizer routing and metadata tests.
- `tests/test_fingerprints.py`: typed entity fingerprint tests.
- `tests/test_retention.py`: Layer 1 retention tests.
- `tests/test_semantic_cache.py`: safe cache hit/miss tests.
- `tests/test_benchmarks.py`: benchmark suite tests.
- `tests/test_live_proxy.py`: live proxy forwarding tests with mocked upstream HTTP.

Modify:

- `promptcompiler/tokenizer.py`: keep compatibility functions, delegate to router where provider/model context is available.
- `promptcompiler/entities.py`: keep `extract_entities`, add compatibility wrapper over typed fingerprints.
- `promptcompiler/parser.py`: include richer entity data without changing existing segment shape unexpectedly.
- `promptcompiler/analyzer.py`: accept tokenizer metadata and provider/model-aware counts.
- `promptcompiler/compiler.py`: use fingerprints/retention metadata and preserve rollback metadata for non-lossless transforms.
- `promptcompiler/v1.py`: wire tokenizer, retention, semantic cache, metrics, and new dashboard API fields.
- `promptcompiler/cache.py`: keep stable cache-key helper, delegate safe semantic cache logic to `semantic_cache.py`.
- `promptcompiler/storage.py`: store retention/cache metadata without storing raw prompt text in zero-retention mode.
- `promptcompiler/proxy.py`: support live OpenAI-compatible upstream forwarding and streaming decision handling.
- `promptcompiler/server.py`: serve static dashboard routes and proxy live-forwarding responses.
- `web/index.html`: add dashboard navigation panes for overview, requests, sessions, cache, settings, integrations, and side-by-side diff.
- `web/app.js`: add client-side routing, trace/session/cache fetchers, heatmap rendering, richer diff rendering, and settings controls.
- `web/styles.css`: add dashboard route, table, diff, heatmap, and responsive styles.
- `README.md`: document new controls, prerequisites, and verification commands.

## Task 1: Benchmark Fixtures And Runner

**Files:**
- Create: `promptcompiler/benchmarks.py`
- Create: `tests/fixtures/benchmarks/golden_support.json`
- Create: `tests/fixtures/benchmarks/adversarial_entities.json`
- Test: `tests/test_benchmarks.py`

- [ ] **Step 1: Write failing benchmark fixture test**

```python
import unittest

from promptcompiler.benchmarks import load_benchmark_cases, run_benchmark_case


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_case_reports_savings_and_entity_preservation(self):
        cases = load_benchmark_cases("tests/fixtures/benchmarks")
        case = next(item for item in cases if item["id"] == "golden_support_dedupe")

        result = run_benchmark_case(case)

        self.assertGreater(result["token_reduction_percent"], 0)
        self.assertTrue(result["preservation"]["ok"])
        self.assertIn("CASE-123", result["preservation"]["checked_entities"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_benchmarks`

Expected: FAIL with `ModuleNotFoundError: No module named 'promptcompiler.benchmarks'`.

- [ ] **Step 3: Add benchmark fixtures**

Create `tests/fixtures/benchmarks/golden_support.json`:

```json
{
  "id": "golden_support_dedupe",
  "mode": "balanced",
  "input": "@pin Keep CASE-123 exactly.\n\nSource: policy-a\nRefunds over $500 require manager approval.\n\nSource: policy-b\nRefunds over $500 require manager approval.",
  "expected_entities": ["CASE-123", "$500"],
  "minimum_token_reduction_percent": 10
}
```

Create `tests/fixtures/benchmarks/adversarial_entities.json`:

```json
{
  "id": "adversarial_different_dates",
  "mode": "balanced",
  "input": "CASE-123 ships on 2026-05-25.\n\nCASE-123 ships on 2026-05-26.",
  "expected_entities": ["CASE-123", "2026-05-25", "2026-05-26"],
  "minimum_token_reduction_percent": 0
}
```

- [ ] **Step 4: Implement benchmark runner**

Create `promptcompiler/benchmarks.py`:

```python
"""Benchmark helpers for PromptCompiler regression cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compiler import compile_prompt


def load_benchmark_cases(root: str | Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(Path(root).glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            case = json.load(handle)
        case["fixture_path"] = str(path)
        cases.append(case)
    return cases


def run_benchmark_case(case: dict[str, Any]) -> dict[str, Any]:
    result = compile_prompt(
        str(case["input"]),
        mode=str(case.get("mode") or "balanced"),
        target_token_budget=case.get("target_token_budget"),
    )
    return {
        "id": case["id"],
        "fixture_path": case.get("fixture_path"),
        "original_tokens": result["original_tokens"],
        "optimized_tokens": result["optimized_tokens"],
        "token_reduction_percent": (
            round((result["tokens_saved"] / result["original_tokens"]) * 100, 2)
            if result["original_tokens"]
            else 0.0
        ),
        "preservation": result["preservation"],
        "warnings": result["warnings"],
        "transformations": result["plan"]["actions"],
    }
```

- [ ] **Step 5: Run benchmark tests**

Run: `python3 -m unittest tests.test_benchmarks`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add promptcompiler/benchmarks.py tests/test_benchmarks.py tests/fixtures/benchmarks
git commit -m "test: add promptcompiler benchmark fixtures"
```

## Task 2: Real Tokenizer Router

**Files:**
- Create: `promptcompiler/tokenizers.py`
- Modify: `promptcompiler/tokenizer.py`
- Modify: `promptcompiler/parser.py`
- Modify: `promptcompiler/analyzer.py`
- Modify: `promptcompiler/v1.py`
- Test: `tests/test_tokenizers.py`
- Test: `tests/test_v1_api.py`

- [ ] **Step 1: Write failing tokenizer router tests**

```python
import unittest

from promptcompiler.tokenizers import TokenizerRouter


class TokenizerRouterTests(unittest.TestCase):
    def test_openai_model_uses_tiktoken_or_reports_fallback(self):
        result = TokenizerRouter().count_text("hello world", provider="openai", model="gpt-4o-mini")

        self.assertGreater(result.tokens, 0)
        self.assertEqual(result.provider, "openai")
        self.assertIn(result.accuracy, {"exact", "estimated"})
        self.assertTrue(result.tokenizer)

    def test_anthropic_and_gemini_models_return_provider_metadata(self):
        router = TokenizerRouter()

        anthropic = router.count_text("hello", provider="anthropic", model="claude-3-5-sonnet")
        gemini = router.count_text("hello", provider="google", model="gemini-1.5-flash")

        self.assertEqual(anthropic.provider, "anthropic")
        self.assertEqual(gemini.provider, "google")
        self.assertEqual(anthropic.accuracy, "estimated")
        self.assertEqual(gemini.accuracy, "estimated")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_tokenizers`

Expected: FAIL with `ModuleNotFoundError: No module named 'promptcompiler.tokenizers'`.

- [ ] **Step 3: Implement router and result type**

Create `promptcompiler/tokenizers.py`:

```python
"""Provider-aware tokenizer routing with deterministic fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .tokenizer import estimate_text_tokens


@dataclass(frozen=True)
class TokenCount:
    tokens: int
    provider: str
    model: str
    tokenizer: str
    accuracy: str
    warning: str | None = None


class TokenizerAdapter(Protocol):
    provider: str

    def supports(self, provider: str, model: str) -> bool:
        ...

    def count_text(self, text: str, provider: str, model: str) -> TokenCount:
        ...

    def count_messages(self, messages: list[dict[str, Any]], provider: str, model: str) -> TokenCount:
        ...


class OpenAITokenizerAdapter:
    provider = "openai"

    def supports(self, provider: str, model: str) -> bool:
        return provider == "openai" or model.startswith(("gpt-", "o1", "o3", "o4"))

    def count_text(self, text: str, provider: str, model: str) -> TokenCount:
        try:
            import tiktoken  # type: ignore

            encoding = tiktoken.encoding_for_model(model)
            return TokenCount(len(encoding.encode(text)), provider, model, "tiktoken", "exact")
        except Exception:
            return TokenCount(
                estimate_text_tokens(text),
                provider,
                model,
                "promptcompiler-estimator",
                "estimated",
                "tiktoken unavailable or model unknown; used conservative fallback estimate.",
            )

    def count_messages(self, messages: list[dict[str, Any]], provider: str, model: str) -> TokenCount:
        text = "\n".join(str(item.get("content", "")) for item in messages)
        counted = self.count_text(text, provider, model)
        return TokenCount(counted.tokens + (4 * len(messages)), provider, model, counted.tokenizer, counted.accuracy, counted.warning)


class FallbackTokenizerAdapter:
    provider = "fallback"

    def __init__(self, provider_name: str = "fallback") -> None:
        self.provider = provider_name

    def supports(self, provider: str, model: str) -> bool:
        return True

    def count_text(self, text: str, provider: str, model: str) -> TokenCount:
        return TokenCount(
            estimate_text_tokens(text),
            provider,
            model,
            "promptcompiler-estimator",
            "estimated",
            "Exact provider tokenizer unavailable; used conservative fallback estimate.",
        )

    def count_messages(self, messages: list[dict[str, Any]], provider: str, model: str) -> TokenCount:
        text = "\n".join(str(item.get("content", "")) for item in messages)
        return TokenCount(
            estimate_text_tokens(text) + (4 * len(messages)),
            provider,
            model,
            "promptcompiler-estimator",
            "estimated",
            "Exact provider tokenizer unavailable; used conservative fallback estimate.",
        )


class TokenizerRouter:
    def __init__(self, adapters: list[TokenizerAdapter] | None = None) -> None:
        self.adapters = adapters or [
            OpenAITokenizerAdapter(),
            FallbackTokenizerAdapter("anthropic"),
            FallbackTokenizerAdapter("google"),
            FallbackTokenizerAdapter("fallback"),
        ]

    def count_text(self, text: str, provider: str, model: str) -> TokenCount:
        adapter = self._adapter(provider, model)
        return adapter.count_text(text, provider, model)

    def count_messages(self, messages: list[dict[str, Any]], provider: str, model: str) -> TokenCount:
        adapter = self._adapter(provider, model)
        return adapter.count_messages(messages, provider, model)

    def _adapter(self, provider: str, model: str) -> TokenizerAdapter:
        normalized_provider = (provider or "").lower()
        for adapter in self.adapters:
            if adapter.supports(normalized_provider, model):
                return adapter
        return FallbackTokenizerAdapter("fallback")
```

- [ ] **Step 4: Wire router metadata into `/v1/analyze` and `/v1/compile`**

Modify `promptcompiler/v1.py` so `_tokenizer_metadata(request)` calls `TokenizerRouter().count_text(request.raw_input, request.provider, request.model)` and returns:

```python
{
    "provider": request.provider,
    "model": request.model,
    "tokenizer": counted.tokenizer,
    "accuracy": counted.accuracy,
    "warning": counted.warning,
}
```

For outer API fields, preserve current `analysis["total_tokens"]` and compile internals until the compiler is refactored; use router metadata to make accuracy visible without destabilizing existing tests.

- [ ] **Step 5: Add API metadata assertion**

In `tests/test_v1_api.py`, extend the analyze or compile test:

```python
self.assertIn(payload["tokenizer"]["accuracy"], {"exact", "estimated"})
self.assertIn("tokenizer", payload["tokenizer"])
```

- [ ] **Step 6: Run tokenizer and API tests**

Run: `python3 -m unittest tests.test_tokenizers tests.test_v1_api`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add promptcompiler/tokenizers.py promptcompiler/v1.py tests/test_tokenizers.py tests/test_v1_api.py
git commit -m "feat: add provider tokenizer router"
```

## Task 3: Typed Entity Fingerprinting

**Files:**
- Create: `promptcompiler/fingerprints.py`
- Modify: `promptcompiler/entities.py`
- Modify: `promptcompiler/parser.py`
- Modify: `promptcompiler/compiler.py`
- Test: `tests/test_fingerprints.py`
- Test: `tests/test_entities.py`
- Test: `tests/test_compiler.py`

- [ ] **Step 1: Write failing fingerprint tests**

```python
import unittest

from promptcompiler.fingerprints import entity_fingerprint


class FingerprintTests(unittest.TestCase):
    def test_entity_fingerprint_groups_required_values(self):
        text = (
            "Email jane@example.com, visit https://example.com/a, file src/app.py, "
            "call compile_prompt(), status ERROR_42, version v1.2.3, ID CASE-123, "
            "time 14:30, date 2026-05-25, amount $1,250.00, ratio 95%."
        )

        fp = entity_fingerprint(text)

        self.assertIn("jane@example.com", fp["emails"])
        self.assertIn("https://example.com/a", fp["urls"])
        self.assertIn("src/app.py", fp["file_paths"])
        self.assertIn("compile_prompt", fp["function_names"])
        self.assertIn("ERROR_42", fp["error_codes"])
        self.assertIn("v1.2.3", fp["versions"])
        self.assertIn("CASE-123", fp["ids"])
        self.assertIn("14:30", fp["times"])
        self.assertIn("2026-05-25", fp["dates"])
        self.assertIn("$1,250.00", fp["currency"])
        self.assertIn("95%", fp["percentages"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_fingerprints`

Expected: FAIL with `ModuleNotFoundError: No module named 'promptcompiler.fingerprints'`.

- [ ] **Step 3: Implement typed fingerprint extraction**

Create `promptcompiler/fingerprints.py` with deterministic regex categories and first-seen ordering:

```python
"""Typed entity fingerprints for safe compression and cache checks."""

from __future__ import annotations

import re


_PATTERNS: dict[str, re.Pattern[str]] = {
    "urls": re.compile(r"https?://[^\s)\"']+"),
    "emails": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "dates": re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    "times": re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|am|pm)?\b"),
    "uuids": re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    "currency": re.compile(r"[$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?"),
    "percentages": re.compile(r"\b\d+(?:\.\d+)?%"),
    "ids": re.compile(r"\b[A-Z]{2,}[A-Z0-9]*-\d+[A-Z0-9-]*\b"),
    "file_paths": re.compile(r"(?:\.{0,2}/)?(?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+"),
    "function_names": re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    "error_codes": re.compile(r"\b(?:ERROR|ERR|WARN|WARNING|FAIL)[A-Z0-9_-]*\b"),
    "versions": re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9.-]+)?\b"),
    "thresholds": re.compile(r"(?:>=|<=|>|<)\s?\d+(?:\.\d+)?\b"),
}


def entity_fingerprint(text: str) -> dict[str, list[str]]:
    return {name: _unique_matches(pattern, text) for name, pattern in _PATTERNS.items()}


def flattened_entities(text: str) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for matches in entity_fingerprint(text).values():
        for value in matches:
            if value not in seen:
                seen.add(value)
                values.append(value)
    return values


def fingerprint_subset_missing(original: dict[str, list[str]], candidate_text: str) -> dict[str, list[str]]:
    candidate = entity_fingerprint(candidate_text)
    missing: dict[str, list[str]] = {}
    for key, values in original.items():
        absent = [value for value in values if value not in candidate.get(key, [])]
        if absent:
            missing[key] = absent
    return missing


def _unique_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for match in pattern.finditer(text):
        value = (match.group(1) if match.lastindex else match.group(0)).rstrip(".,;:")
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values
```

- [ ] **Step 4: Preserve `extract_entities` compatibility**

Modify `promptcompiler/entities.py`:

```python
from .fingerprints import flattened_entities


def extract_entities(text: str) -> list[str]:
    """Return protected entities in first-seen order."""

    return flattened_entities(text)
```

- [ ] **Step 5: Add preservation metadata to compile result**

Modify `promptcompiler/compiler.py` so preservation contains:

```python
"fingerprint": entity_fingerprint(raw_input),
"missing_fingerprint": fingerprint_subset_missing(entity_fingerprint(raw_input), optimized_text),
```

Keep existing `checked_entities` and `missing_entities` fields for current UI/tests.

- [ ] **Step 6: Run entity and compiler tests**

Run: `python3 -m unittest tests.test_fingerprints tests.test_entities tests.test_compiler`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add promptcompiler/fingerprints.py promptcompiler/entities.py promptcompiler/compiler.py tests/test_fingerprints.py tests/test_entities.py tests/test_compiler.py
git commit -m "feat: add typed entity fingerprints"
```

## Task 4: Layer 1 Retention Scoring

**Files:**
- Create: `promptcompiler/retention.py`
- Modify: `promptcompiler/compiler.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/storage.py`
- Test: `tests/test_retention.py`
- Test: `tests/test_v1_api.py`

- [ ] **Step 1: Write failing retention tests**

```python
import unittest

from promptcompiler.retention import layer1_retention


class RetentionTests(unittest.TestCase):
    def test_layer1_retention_penalizes_missing_entities(self):
        result = layer1_retention("Keep CASE-123 and 2026-05-25.", "Keep CASE-123.")

        self.assertLess(result["score"], 1.0)
        self.assertEqual(result["status"], "failed")
        self.assertIn("2026-05-25", result["missing_entities"])

    def test_layer1_retention_passes_high_overlap_with_entities(self):
        result = layer1_retention("Keep CASE-123 and ship fast.", "Keep CASE-123 and ship fast.")

        self.assertEqual(result["status"], "passed")
        self.assertGreaterEqual(result["score"], 0.95)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_retention`

Expected: FAIL with `ModuleNotFoundError: No module named 'promptcompiler.retention'`.

- [ ] **Step 3: Implement deterministic Layer 1 retention**

Create `promptcompiler/retention.py`:

```python
"""Layer 1 retention scoring for optimized prompts."""

from __future__ import annotations

import re
from typing import Any

from .entities import extract_entities


_WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def layer1_retention(original: str, optimized: str, threshold: float = 0.95) -> dict[str, Any]:
    original_entities = extract_entities(original)
    missing_entities = [entity for entity in original_entities if entity not in optimized]
    lexical = _lexical_overlap(original, optimized)
    entity_score = 1.0 if not original_entities else (len(original_entities) - len(missing_entities)) / len(original_entities)
    score = round(min(1.0, (lexical * 0.45) + (entity_score * 0.55)), 4)
    status = "passed" if score >= threshold and not missing_entities else "failed"
    return {
        "score": score,
        "threshold": threshold,
        "status": status,
        "lexical_overlap": round(lexical, 4),
        "entity_score": round(entity_score, 4),
        "checked_entities": original_entities,
        "missing_entities": missing_entities,
    }


def _lexical_overlap(original: str, optimized: str) -> float:
    original_terms = set(_WORD_PATTERN.findall(original.lower()))
    optimized_terms = set(_WORD_PATTERN.findall(optimized.lower()))
    if not original_terms:
        return 1.0
    return len(original_terms & optimized_terms) / len(original_terms)
```

- [ ] **Step 4: Wire retention into compile responses**

Modify `promptcompiler/compiler.py` to include:

```python
"retention": layer1_retention(raw_input, optimized_text),
```

Modify `promptcompiler/v1.py` evaluation block:

```python
"layer1_retention_score": result["retention"]["score"],
"layer1_status": result["retention"]["status"],
"layer2_status": "disabled_zero_retention" if request.zero_retention else "not_configured",
```

- [ ] **Step 5: Store retention status in trace metadata**

Modify `_record_trace` in `promptcompiler/v1.py` to set `evaluation_status` to `layer1_status` when present, while preserving `disabled_zero_retention` for Layer 2 in response metadata.

- [ ] **Step 6: Run retention and API tests**

Run: `python3 -m unittest tests.test_retention tests.test_v1_api tests.test_storage`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add promptcompiler/retention.py promptcompiler/compiler.py promptcompiler/v1.py promptcompiler/storage.py tests/test_retention.py tests/test_v1_api.py tests/test_storage.py
git commit -m "feat: add layer one retention scoring"
```

## Task 5: Safe Semantic Cache

**Files:**
- Create: `promptcompiler/semantic_cache.py`
- Modify: `promptcompiler/cache.py`
- Modify: `promptcompiler/storage.py`
- Modify: `promptcompiler/v1.py`
- Test: `tests/test_semantic_cache.py`
- Test: `tests/test_cache.py`
- Test: `tests/test_v1_api.py`

- [ ] **Step 1: Write failing safe-cache tests**

```python
import unittest

from promptcompiler.semantic_cache import SafeCacheEntry, safe_cache_hit


class SemanticCacheTests(unittest.TestCase):
    def test_safe_cache_hit_requires_similarity_and_fingerprint_match(self):
        entry = SafeCacheEntry(
            key="cache_1",
            provider="openai",
            model="gpt-4o-mini",
            mode="balanced",
            policy_version=1,
            similarity=0.98,
            entity_fingerprint={"ids": ["CASE-123"]},
            pinned_fingerprint={"ids": ["CASE-123"]},
            response={"optimized_prompt": "Keep CASE-123."},
        )

        result = safe_cache_hit(
            [entry],
            provider="openai",
            model="gpt-4o-mini",
            mode="balanced",
            policy_version=1,
            entity_fingerprint={"ids": ["CASE-123"]},
            pinned_fingerprint={"ids": ["CASE-123"]},
        )

        self.assertTrue(result.hit)
        self.assertEqual(result.response["optimized_prompt"], "Keep CASE-123.")

    def test_safe_cache_misses_on_entity_mismatch(self):
        entry = SafeCacheEntry(
            key="cache_1",
            provider="openai",
            model="gpt-4o-mini",
            mode="balanced",
            policy_version=1,
            similarity=0.99,
            entity_fingerprint={"ids": ["CASE-999"]},
            pinned_fingerprint={"ids": ["CASE-999"]},
            response={"optimized_prompt": "Keep CASE-999."},
        )

        result = safe_cache_hit(
            [entry],
            provider="openai",
            model="gpt-4o-mini",
            mode="balanced",
            policy_version=1,
            entity_fingerprint={"ids": ["CASE-123"]},
            pinned_fingerprint={"ids": ["CASE-123"]},
        )

        self.assertFalse(result.hit)
        self.assertEqual(result.reason, "entity_fingerprint_mismatch")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_semantic_cache`

Expected: FAIL with `ModuleNotFoundError: No module named 'promptcompiler.semantic_cache'`.

- [ ] **Step 3: Implement safe cache comparison**

Create `promptcompiler/semantic_cache.py`:

```python
"""Safe semantic cache guards for compile responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafeCacheEntry:
    key: str
    provider: str
    model: str
    mode: str
    policy_version: int
    similarity: float
    entity_fingerprint: dict[str, list[str]]
    pinned_fingerprint: dict[str, list[str]]
    response: dict[str, Any]


@dataclass(frozen=True)
class SafeCacheResult:
    hit: bool
    reason: str
    response: dict[str, Any]
    key: str | None = None


def safe_cache_hit(
    candidates: list[SafeCacheEntry],
    provider: str,
    model: str,
    mode: str,
    policy_version: int,
    entity_fingerprint: dict[str, list[str]],
    pinned_fingerprint: dict[str, list[str]],
    min_similarity: float = 0.97,
) -> SafeCacheResult:
    last_reason = "miss"
    for candidate in candidates:
        if candidate.similarity < min_similarity:
            last_reason = "similarity_below_threshold"
            continue
        if candidate.provider != provider:
            last_reason = "provider_mismatch"
            continue
        if candidate.model != model:
            last_reason = "model_mismatch"
            continue
        if candidate.mode != mode:
            last_reason = "mode_mismatch"
            continue
        if candidate.policy_version != policy_version:
            last_reason = "policy_version_mismatch"
            continue
        if candidate.entity_fingerprint != entity_fingerprint:
            last_reason = "entity_fingerprint_mismatch"
            continue
        if candidate.pinned_fingerprint != pinned_fingerprint:
            last_reason = "pinned_fingerprint_mismatch"
            continue
        return SafeCacheResult(True, "hit", candidate.response, candidate.key)
    return SafeCacheResult(False, last_reason, {})
```

- [ ] **Step 4: Upgrade local cache metadata**

Modify `promptcompiler/storage.py` compile cache schema to add metadata columns through additive migration statements:

```sql
ALTER TABLE compile_cache ADD COLUMN provider TEXT;
ALTER TABLE compile_cache ADD COLUMN model TEXT;
ALTER TABLE compile_cache ADD COLUMN mode TEXT;
ALTER TABLE compile_cache ADD COLUMN policy_version INTEGER DEFAULT 1;
ALTER TABLE compile_cache ADD COLUMN entity_fingerprint_json TEXT DEFAULT '{}';
ALTER TABLE compile_cache ADD COLUMN pinned_fingerprint_json TEXT DEFAULT '{}';
```

Wrap each `ALTER TABLE` in a helper that ignores duplicate-column errors.

- [ ] **Step 5: Wire zero-retention cache behavior**

Modify `promptcompiler/v1.py`:

- If `request.zero_retention` is true, bypass response caching and return `cache.status = "disabled"`.
- If caching is enabled and zero-retention is false, write response plus fingerprints.
- On hit, return cached response only through `safe_cache_hit`.

- [ ] **Step 6: Add Redis adapter boundary**

Add a class in `semantic_cache.py` named `RedisSemanticCache`. It must import `redis` inside methods, catch import/connection errors, and return miss metadata without failing compile. Tests should mock the adapter instead of requiring Redis.

- [ ] **Step 7: Run cache and API tests**

Run: `python3 -m unittest tests.test_semantic_cache tests.test_cache tests.test_v1_api tests.test_storage`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add promptcompiler/semantic_cache.py promptcompiler/cache.py promptcompiler/storage.py promptcompiler/v1.py tests/test_semantic_cache.py tests/test_cache.py tests/test_v1_api.py tests/test_storage.py
git commit -m "feat: add safe semantic cache guards"
```

## Task 6: Request And Session Dashboard Pages

**Files:**
- Modify: `promptcompiler/server.py`
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Test: `tests/test_static_assets.py`
- Test: `tests/web_e2e_runner.mjs`
- Test: `tests/test_web_e2e.py`

- [ ] **Step 1: Write failing static route test**

Add to `tests/test_static_assets.py`:

```python
def test_dashboard_routes_fall_back_to_index_html(self):
    for route in ["/overview", "/requests", "/sessions", "/cache", "/settings", "/integrations"]:
        self.assertEqual(_static_file_for_request(route), WEB_ROOT / "index.html")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_static_assets`

Expected: FAIL because `_static_file_for_request("/requests")` returns `None`.

- [ ] **Step 3: Serve static dashboard routes**

Modify `promptcompiler/server.py`:

```python
if not candidate.exists() and "/" not in requested and "." not in requested:
    candidate = (WEB_ROOT / "index.html").resolve()
```

Add allowed route guard for: `overview`, `requests`, `sessions`, `cache`, `settings`, `integrations`.

- [ ] **Step 4: Add dashboard navigation HTML**

Modify `web/index.html` to add a compact nav inside the topbar:

```html
<nav class="app-nav" aria-label="Dashboard views">
  <a href="/overview" data-route="overview">Overview</a>
  <a href="/requests" data-route="requests">Requests</a>
  <a href="/sessions" data-route="sessions">Sessions</a>
  <a href="/cache" data-route="cache">Cache</a>
  <a href="/settings" data-route="settings">Settings</a>
  <a href="/integrations" data-route="integrations">Integrations</a>
</nav>
```

Add route panels with stable IDs:

```html
<section id="requestsView" class="panel full-span route-panel" hidden></section>
<section id="sessionsView" class="panel full-span route-panel" hidden></section>
<section id="cacheView" class="panel full-span route-panel" hidden></section>
<section id="settingsView" class="panel full-span route-panel" hidden></section>
<section id="integrationsView" class="panel full-span route-panel" hidden></section>
```

- [ ] **Step 5: Add client-side routing**

Modify `web/app.js`:

```javascript
const routePanels = {
  overview: document.querySelector("#controlPanel"),
  requests: document.querySelector("#requestsView"),
  sessions: document.querySelector("#sessionsView"),
  cache: document.querySelector("#cacheView"),
  settings: document.querySelector("#settingsView"),
  integrations: document.querySelector("#integrationsView"),
};

function currentRoute() {
  return window.location.pathname.replace(/^\\//, "") || "overview";
}

function navigate(route) {
  history.pushState({}, "", `/${route}`);
  renderRoute(route);
}

async function renderRoute(route = currentRoute()) {
  Object.entries(routePanels).forEach(([name, panel]) => {
    if (!panel) return;
    panel.hidden = name !== route;
  });
  document.querySelectorAll("[data-route]").forEach((link) => {
    link.classList.toggle("active", link.dataset.route === route);
  });
  if (route === "requests") await renderRequestsView();
  if (route === "sessions") await renderSessionsView();
  if (route === "cache") await renderCacheView();
  if (route === "settings") renderSettingsView();
  if (route === "integrations") renderIntegrationsView();
}
```

- [ ] **Step 6: Add requests/sessions/cache renderers**

Use existing `/v1/metrics` for overview/cache summaries and `/v1/requests/{trace_id}` for trace lookup. The requests view should include a trace ID input and lookup button. The sessions view should include session ID and target budget inputs that call `/v1/sessions/{id}/context`.

- [ ] **Step 7: Extend browser E2E**

In `tests/web_e2e_runner.mjs`, navigate to `/requests`, `/sessions`, `/cache`, `/settings`, and `/integrations`; assert each view renders a unique heading and no HTTP errors occur.

- [ ] **Step 8: Run UI tests**

Run: `python3 -m unittest tests.test_static_assets tests.test_web_e2e`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add promptcompiler/server.py web/index.html web/app.js web/styles.css tests/test_static_assets.py tests/web_e2e_runner.mjs tests/test_web_e2e.py
git commit -m "feat: add static dashboard routes"
```

## Task 7: Side-By-Side Diff And Token Heatmap

**Files:**
- Modify: `promptcompiler/diff.py`
- Modify: `promptcompiler/compiler.py`
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Test: `tests/test_compiler.py`
- Test: `tests/web_e2e_runner.mjs`

- [ ] **Step 1: Write failing diff metadata test**

Add to `tests/test_compiler.py`:

```python
def test_compile_returns_heatmap_and_side_by_side_diff_metadata(self):
    result = compile_prompt("@pin Keep CASE-123.\n\nrepeat\n\nrepeat", mode="balanced")

    self.assertIn("heatmap", result)
    self.assertTrue(result["heatmap"])
    self.assertIn("side_by_side_diff", result)
    self.assertTrue(any(item["status"] in {"kept", "removed", "changed"} for item in result["side_by_side_diff"]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_compiler.CompilerTests.test_compile_returns_heatmap_and_side_by_side_diff_metadata`

Expected: FAIL because `heatmap` is missing.

- [ ] **Step 3: Add backend heatmap metadata**

Modify `promptcompiler/compiler.py` to produce:

```python
"heatmap": [
    {
        "segment_id": segment.id,
        "type": segment.type,
        "tokens": segment.tokens,
        "relative_share": round(segment.tokens / original_tokens, 4) if original_tokens else 0,
        "pinned": segment.pinned,
        "status": "removed" if segment.id in removed_ids else "retained",
    }
    for segment in original_segments
],
"side_by_side_diff": diff,
```

- [ ] **Step 4: Render side-by-side diff**

Add to `web/index.html`:

```html
<div id="sideBySideDiff" class="side-by-side-diff"></div>
<div id="tokenHeatmap" class="token-heatmap"></div>
```

Add to `web/app.js`:

```javascript
function renderSideBySideDiff(items) {
  sideBySideDiff.innerHTML = items.length
    ? items.map((item) => `
      <div class="diff-row ${escapeHtml(item.status || "kept")}">
        <pre>${escapeHtml(item.original_text || item.text || "")}</pre>
        <pre>${escapeHtml(item.optimized_text || "")}</pre>
      </div>
    `).join("")
    : emptyRow("Compile a prompt to inspect side-by-side changes.");
}

function renderTokenHeatmap(items) {
  tokenHeatmap.innerHTML = items.length
    ? items.map((item) => `
      <div class="heatmap-segment ${item.pinned ? "pinned" : ""}" style="--share:${Math.max(0.05, Number(item.relative_share || 0))}">
        <span>${escapeHtml(item.segment_id)}</span>
        <strong>${escapeHtml(String(item.tokens))}</strong>
      </div>
    `).join("")
    : emptyRow("Compile a prompt to see token heatmap.");
}
```

- [ ] **Step 5: Extend E2E assertions**

Assert `#sideBySideDiff` contains at least one `.diff-row` and `#tokenHeatmap` contains at least one `.heatmap-segment` after compile.

- [ ] **Step 6: Run tests**

Run: `python3 -m unittest tests.test_compiler tests.test_web_e2e`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add promptcompiler/diff.py promptcompiler/compiler.py web/index.html web/app.js web/styles.css tests/test_compiler.py tests/web_e2e_runner.mjs
git commit -m "feat: add side-by-side diff and heatmap"
```

## Task 8: Live OpenAI-Compatible Proxy Forwarding

**Files:**
- Modify: `promptcompiler/proxy.py`
- Modify: `promptcompiler/server.py`
- Modify: `README.md`
- Test: `tests/test_live_proxy.py`
- Test: `tests/test_server.py`

- [ ] **Step 1: Write failing live proxy forwarding test**

```python
import json
import unittest
from unittest.mock import patch

from promptcompiler.proxy import proxy_openai_chat_completions


class LiveProxyTests(unittest.TestCase):
    def test_live_forwarding_posts_optimized_payload_to_upstream(self):
        upstream = {
            "id": "chatcmpl_test",
            "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop", "index": 0}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
        }

        with patch("promptcompiler.proxy._post_openai_compatible") as post:
            post.return_value = upstream
            response, headers = proxy_openai_chat_completions(
                {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "repeat\n\nrepeat"}],
                    "promptcompiler": {
                        "mock_provider": False,
                        "provider_api_key": "test-key",
                        "provider_base_url": "https://api.example.test/v1",
                        "mode": "balanced",
                    },
                }
            )

        self.assertEqual(response["id"], "chatcmpl_test")
        self.assertIn("promptcompiler", response)
        self.assertTrue(headers["X-PromptCompiler-Trace"].startswith("tr_"))
        sent_payload = post.call_args.args[1]
        self.assertIn("messages", sent_payload)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_live_proxy`

Expected: FAIL because live forwarding currently raises `LIVE_PROVIDER_NOT_CONFIGURED`.

- [ ] **Step 3: Implement upstream POST helper**

Add to `promptcompiler/proxy.py`:

```python
import json
import urllib.error
import urllib.request


def _post_openai_compatible(base_url: str, payload: dict[str, Any], api_key: str, timeout: int = 90) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProxyError(f"Upstream provider failed with HTTP {exc.code}: {detail}", status_code=502, code="UPSTREAM_PROVIDER_FAILED") from exc
    except urllib.error.URLError as exc:
        raise ProxyError(f"Upstream provider request failed: {exc.reason}", status_code=502, code="UPSTREAM_PROVIDER_FAILED") from exc
```

- [ ] **Step 4: Reconstruct provider payload**

When `mock_provider` is false:

- Compile request with `compile_v1`.
- Replace outbound `messages` with `compiled["optimized_messages"]` when non-empty.
- Preserve original provider fields such as `temperature`, `max_tokens`, `tools`, `tool_choice`, and `stream`.
- Reject `stream: true` with `STREAMING_NOT_SUPPORTED` until streaming is separately implemented.
- Read API key from `promptcompiler.provider_api_key` or `OPENAI_API_KEY`.
- Read base URL from `promptcompiler.provider_base_url` or `OPENAI_BASE_URL` or `https://api.openai.com/v1`.
- Add `promptcompiler` metadata to the upstream JSON response before returning.

- [ ] **Step 5: Run proxy tests**

Run: `python3 -m unittest tests.test_live_proxy tests.test_server`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add promptcompiler/proxy.py promptcompiler/server.py README.md tests/test_live_proxy.py tests/test_server.py
git commit -m "feat: add live openai proxy forwarding"
```

## Task 9: Final Integration And Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-05-24-prd-trd-platform-roadmap.md`
- Test: full suite

- [ ] **Step 1: Add README section for new capabilities**

Document:

- Tokenizer accuracy metadata and optional `tiktoken`.
- Typed entity fingerprints.
- Layer 1 retention score.
- Safe cache behavior and zero-retention bypass.
- Static dashboard routes.
- Live proxy forwarding environment variables.
- Benchmark command.

- [ ] **Step 2: Add benchmark command**

If a CLI command is not added, document this Python one-liner:

```bash
python3 - <<'PY'
from promptcompiler.benchmarks import load_benchmark_cases, run_benchmark_case
for case in load_benchmark_cases("tests/fixtures/benchmarks"):
    print(run_benchmark_case(case))
PY
```

- [ ] **Step 3: Run targeted verification**

Run:

```bash
python3 -m unittest tests.test_tokenizers tests.test_fingerprints tests.test_retention tests.test_semantic_cache tests.test_benchmarks tests.test_live_proxy
```

Expected: PASS.

- [ ] **Step 4: Run full verification**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 5: Run live local smoke**

Start or reuse server:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN || python3 -m promptcompiler.server
```

Smoke:

```bash
curl -s http://127.0.0.1:8765/api/health
curl -s http://127.0.0.1:8765/v1/metrics
curl -s http://127.0.0.1:8765/requests | head
```

Expected:

- Health returns `{"ok": true, ...}`.
- Metrics returns JSON.
- `/requests` returns HTML containing `PromptCompiler`.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/superpowers/specs/2026-05-24-prd-trd-platform-roadmap.md
git commit -m "docs: document trd gap implementation"
```

## Self-Review

Spec coverage:

- Real tokenizer router: Task 2.
- Better entity fingerprinting: Task 3.
- Layer 1 retention scoring: Task 4.
- Request/session dashboard pages: Task 6.
- Side-by-side diff and heatmap: Task 7.
- Live proxy forwarding: Task 8.
- Semantic cache with safety guards: Task 5.
- Benchmark suite: Task 1 and final verification in Task 9.

Execution risks:

- `tiktoken`, Redis, and provider keys are optional at implementation time. Tests must mock or fall back so the local suite stays green without paid services.
- The dashboard remains static HTML/CSS/JS in this plan. A Next.js migration is not required to complete these eight TRD gaps.
- Live streaming proxy is explicitly rejected with a clear error in this plan; streaming support should be its own follow-up plan because it changes server response handling.

Verification gate:

- Do not mark the plan complete unless `python3 -m unittest discover -s tests` passes and the local server smoke checks return expected JSON/HTML.
