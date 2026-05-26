# Token Consumption Reduction Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the practical token-consumption reduction techniques that fit PromptCompiler's local-first architecture: reusable prompt state, compact inputs, better session memory, retrieval controls, schema slimming, routing, caching, and token-waste linting.

**Architecture:** Keep PromptCompiler as a Python standard-library server with static web UI, SDK, and OpenAI-compatible proxy. Add focused modules that normalize and shrink context before the existing compiler runs, then expose those policies through `/v1/*`, SDK options, proxy metadata, and tests.

**Tech Stack:** Python standard library, `unittest`, SQLite, static HTML/CSS/JavaScript, existing PromptCompiler parser/compiler/semantic/storage/proxy/SDK layers.

---

## Scope Map

These user-listed techniques are implementable in this repo:

| # | Technique | Implementation status after this roadmap |
|---|---|---|
| 1 | Huge system prompts | Phase 1: system prompt registry and reusable prompt references |
| 2 | Sending entire chat history | Phase 2: sliding window, rolling summaries, compact session context API |
| 3 | Overly verbose responses | Phase 1: output budget policy and response-shape hints |
| 4 | Large models for simple tasks | Phase 6: local model/task routing policy |
| 5 | Sending raw documents | Phase 3 and Phase 4: document/log chunking plus retrieval budget |
| 6 | Poor RAG design | Phase 4: top-k, reranking, semantic filtering, compression budget |
| 7 | Repeating context | Phase 2: server-side session state and pinned facts |
| 8 | Not using caching | Phase 6: local compile cache and provider cache hints |
| 9 | Asking multiple things together | Phase 7: token-waste lint rules and decomposition recommendations |
| 10 | Markdown overhead | Phase 3: markdown-to-plain internal compaction |
| 11 | JSON bloat | Phase 3: JSON minification, key aliasing, structural normalization |
| 12 | Long function schemas/tool definitions | Phase 5: schema slimming and dynamic tool selection |
| 13 | Too many retrieved search results | Phase 4: result budget, dedupe, compress-before-inject |
| 14 | Bad agent frameworks | Phase 7: agent-loop linting and optional reflection stripping |
| 15 | Natural language instead of structured inputs | Phase 3: structured input envelopes and compact serialization |
| Advanced: context compression | Phase 2 and Phase 4 |
| Advanced: semantic memory | Phase 2 and Phase 4 |
| Advanced: hybrid routing | Phase 6 |

Not planned here:

- Speculative decoding. That belongs inside inference runtimes such as `vLLM`, `TensorRT-LLM`, or a provider backend, not inside a prompt optimizer. PromptCompiler can later document/runtime-detect it, but it should not fake this optimization.

## Existing Foundation

Already implemented and should not be rewritten:

- `promptcompiler/compiler.py`: lossless/balanced/aggressive compile modes, duplicate removal, repeated-line compaction, tool/RAG summarization, pinned budget cap, preservation checks.
- `promptcompiler/semantic.py`: local chunking, lexical scoring, source-aware RAG pruning.
- `promptcompiler/storage.py`: SQLite traces, session turns, 70 percent budget compaction.
- `promptcompiler/v1.py`: `/v1/analyze`, `/v1/compile`, sessions, metrics, trace metadata.
- `promptcompiler/proxy.py`: OpenAI-compatible local proxy wrapper with token headers.
- `promptcompiler/sdk.py`: `PromptCompilerClient` and OpenAI-like wrapper.

## Phase Order

1. Prompt policy and reusable system prompts.
2. Session context builder and semantic memory foundation.
3. Payload minification and structured input normalization.
4. Retrieval, RAG, document, and search-result budgeting.
5. Tool schema slimming and dynamic tool selection.
6. Model routing, hybrid routing, and caching.
7. Token-waste linting and agent-framework guardrails.
8. Web/SDK documentation pass and full verification.

Each phase is independently shippable. Stop after any phase if tests fail or if the public API shape needs product review.

---

## Phase 1: Prompt Policy And Reusable System Prompts

**Implements:** huge system prompts, overly verbose responses, beginning of prompt caching compatibility.

**Files:**
- Create: `promptcompiler/policies.py`
- Create: `promptcompiler/prompt_registry.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/proxy.py`
- Modify: `promptcompiler/sdk.py`
- Modify: `promptcompiler/server.py`
- Test: `tests/test_policies.py`
- Test: `tests/test_v1_api.py`
- Test: `tests/test_sdk.py`

### Task 1.1: Add policy dataclasses and normalization

- [ ] **Step 1: Write tests for output and prompt policies**

Add to `tests/test_policies.py`:

```python
import unittest

from promptcompiler.policies import normalize_context_policy, normalize_output_policy


class PolicyTests(unittest.TestCase):
    def test_output_policy_normalizes_compact_defaults(self):
        policy = normalize_output_policy({"max_words": "80", "format": "json", "explain": False})

        self.assertEqual(policy["max_words"], 80)
        self.assertEqual(policy["format"], "json")
        self.assertEqual(policy["instruction"], "Answer in <=80 words. Return JSON only. No explanation unless asked.")

    def test_context_policy_accepts_system_prompt_ref(self):
        policy = normalize_context_policy({"system_prompt_ref": "json_only", "cache_static_prefix": True})

        self.assertEqual(policy["system_prompt_ref"], "json_only")
        self.assertTrue(policy["cache_static_prefix"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing policy tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_policies.py
```

Expected: fail because `promptcompiler.policies` does not exist.

- [ ] **Step 3: Implement policy normalization**

Create `promptcompiler/policies.py`:

```python
"""Request policy helpers for compact prompt and output behavior."""

from __future__ import annotations

from typing import Any


_ALLOWED_OUTPUT_FORMATS = {"plain", "json", "bullets"}


def normalize_output_policy(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    max_words = _positive_int(raw.get("max_words"), default=None)
    output_format = str(raw.get("format") or "plain").strip().lower()
    if output_format not in _ALLOWED_OUTPUT_FORMATS:
        output_format = "plain"
    explain = bool(raw.get("explain", output_format != "json"))
    parts: list[str] = []
    if max_words:
        parts.append(f"Answer in <={max_words} words.")
    if output_format == "json":
        parts.append("Return JSON only.")
    elif output_format == "bullets":
        parts.append("Return bullet points only.")
    if not explain:
        parts.append("No explanation unless asked.")
    return {
        "max_words": max_words,
        "format": output_format,
        "explain": explain,
        "instruction": " ".join(parts),
    }


def normalize_context_policy(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "system_prompt_ref": _optional_string(raw.get("system_prompt_ref")),
        "cache_static_prefix": bool(raw.get("cache_static_prefix", False)),
        "sliding_window_turns": _positive_int(raw.get("sliding_window_turns"), default=None),
        "summary_token_budget": _positive_int(raw.get("summary_token_budget"), default=None),
        "retrieval_top_k": _positive_int(raw.get("retrieval_top_k"), default=None),
    }


def _positive_int(value: Any, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
```

- [ ] **Step 4: Run policy tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_policies.py
```

Expected: pass.

### Task 1.2: Add reusable system prompt registry

- [ ] **Step 1: Write registry tests**

Extend `tests/test_policies.py`:

```python
from promptcompiler.prompt_registry import expand_system_prompt_ref, list_system_prompts


class PromptRegistryTests(unittest.TestCase):
    def test_builtin_prompt_ref_expands_to_short_instruction(self):
        expanded = expand_system_prompt_ref("json_only")

        self.assertEqual(expanded["id"], "json_only")
        self.assertIn("Return JSON only", expanded["content"])
        self.assertLess(len(expanded["content"].split()), 10)

    def test_registry_lists_builtin_prompt_ids(self):
        prompts = list_system_prompts()

        self.assertTrue(any(item["id"] == "concise" for item in prompts))
        self.assertTrue(any(item["id"] == "json_only" for item in prompts))
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_policies.py
```

Expected: fail because `promptcompiler.prompt_registry` does not exist.

- [ ] **Step 3: Implement registry**

Create `promptcompiler/prompt_registry.py`:

```python
"""Small local registry for reusable system prompt instructions."""

from __future__ import annotations

from typing import Any


_BUILTINS: dict[str, str] = {
    "concise": "Be concise.",
    "json_only": "Return JSON only.",
    "bullets_only": "Return bullet points only.",
    "no_explanation": "No explanation unless asked.",
}


def list_system_prompts() -> list[dict[str, str]]:
    return [{"id": key, "content": value} for key, value in sorted(_BUILTINS.items())]


def expand_system_prompt_ref(prompt_ref: str | None) -> dict[str, Any] | None:
    if not prompt_ref:
        return None
    key = str(prompt_ref).strip()
    if not key:
        return None
    if key not in _BUILTINS:
        raise ValueError(f"Unknown system_prompt_ref: {key}")
    return {"id": key, "content": _BUILTINS[key], "source": "builtin"}
```

- [ ] **Step 4: Run registry tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_policies.py
```

Expected: pass.

### Task 1.3: Wire policies into `/v1/analyze` and `/v1/compile`

- [ ] **Step 1: Add API tests**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_compile_expands_system_prompt_ref_and_output_policy(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Give status for CASE-123."}],
                "context_policy": {"system_prompt_ref": "json_only", "cache_static_prefix": True},
                "output_policy": {"max_words": 50, "format": "json", "explain": False},
                "mode": "balanced",
                "zero_retention": True,
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["context_policy"]["system_prompt_ref"], "json_only")
        self.assertTrue(payload["context_policy"]["cache_static_prefix"])
        self.assertEqual(payload["output_policy"]["max_words"], 50)
        self.assertIn("Return JSON only", payload["optimized_prompt"])
        self.assertIn("Answer in <=50 words", payload["optimized_prompt"])
```

- [ ] **Step 2: Run failing API test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_v1_api.py::V1ApiTests.test_v1_compile_expands_system_prompt_ref_and_output_policy
```

If unittest does not accept `::`, run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_v1_api.V1ApiTests.test_v1_compile_expands_system_prompt_ref_and_output_policy
```

Expected: fail because policy fields are ignored.

- [ ] **Step 3: Extend normalized request**

Modify `promptcompiler/v1.py`:

```python
from .policies import normalize_context_policy, normalize_output_policy
from .prompt_registry import expand_system_prompt_ref
```

Add fields to `NormalizedV1Request`:

```python
    context_policy: dict[str, Any]
    output_policy: dict[str, Any]
```

In `normalize_v1_request()`, compute:

```python
    context_policy = normalize_context_policy(payload.get("context_policy"))
    output_policy = normalize_output_policy(payload.get("output_policy"))
    raw_input = _apply_prompt_policies(raw_input, context_policy, output_policy)
```

Return those fields in the dataclass.

- [ ] **Step 4: Add prompt policy application helper**

Add to `promptcompiler/v1.py`:

```python
def _apply_prompt_policies(
    raw_input: str,
    context_policy: dict[str, Any],
    output_policy: dict[str, Any],
) -> str:
    prefix_parts: list[str] = []
    expanded = expand_system_prompt_ref(context_policy.get("system_prompt_ref"))
    if expanded:
        prefix_parts.append(str(expanded["content"]))
    instruction = str(output_policy.get("instruction") or "").strip()
    if instruction:
        prefix_parts.append(instruction)
    if not prefix_parts:
        return raw_input
    prefix = "\n".join(prefix_parts)
    return f"{prefix}\n\n{raw_input}" if raw_input.strip() else prefix
```

- [ ] **Step 5: Return policies in v1 responses**

Add to both analyze and compile responses:

```python
        "context_policy": request.context_policy,
        "output_policy": request.output_policy,
```

- [ ] **Step 6: Run API test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_v1_api.V1ApiTests.test_v1_compile_expands_system_prompt_ref_and_output_policy
```

Expected: pass.

### Task 1.4: Wire policies through SDK and proxy

- [ ] **Step 1: Add SDK wrapper test**

Add to `tests/test_sdk.py`:

```python
    def test_wrap_forwards_policy_options_to_promptcompiler(self):
        fake = FakeOpenAIClient()
        wrapped = promptcompiler.wrap(fake, base_url=self.base_url, mode="balanced")

        response = wrapped.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Give short JSON for CASE-123."}],
            promptcompiler={
                "context_policy": {"system_prompt_ref": "json_only"},
                "output_policy": {"max_words": 20, "format": "json", "explain": False},
            },
        )

        forwarded = fake.chat.completions.calls[0]
        self.assertIn("Return JSON only", forwarded["messages"][0]["content"])
        self.assertEqual(response.promptcompiler["output_policy"]["max_words"], 20)
```

- [ ] **Step 2: Run failing SDK test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_sdk.SDKTests.test_wrap_forwards_policy_options_to_promptcompiler
```

Expected: fail until SDK forwards policy options and stores metadata.

- [ ] **Step 3: Update SDK payload construction**

Modify `promptcompiler/sdk.py` so wrapper/client compile payloads include:

```python
if options.get("context_policy"):
    payload["context_policy"] = options["context_policy"]
if options.get("output_policy"):
    payload["output_policy"] = options["output_policy"]
```

Ensure response metadata copied into `response.promptcompiler` includes:

```python
"context_policy": compiled.get("context_policy", {}),
"output_policy": compiled.get("output_policy", {}),
```

- [ ] **Step 4: Update proxy payload construction**

Modify `promptcompiler/proxy.py` compile payload:

```python
        "context_policy": options.get("context_policy", {}),
        "output_policy": options.get("output_policy", {}),
```

Include both policy objects in the returned `promptcompiler` metadata.

- [ ] **Step 5: Run policy, API, SDK tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_policies.py tests/test_v1_api.py tests/test_sdk.py
```

Expected: pass.

- [ ] **Step 6: Commit Phase 1**

Run:

```bash
git add promptcompiler/policies.py promptcompiler/prompt_registry.py promptcompiler/v1.py promptcompiler/proxy.py promptcompiler/sdk.py tests/test_policies.py tests/test_v1_api.py tests/test_sdk.py
git commit -m "feat: add compact prompt policies"
```

---

## Phase 2: Session Context Builder And Semantic Memory Foundation

**Implements:** sliding window memory, summaries, repeated context avoidance, semantic memory foundation, context compression.

**Files:**
- Create: `promptcompiler/session_context.py`
- Modify: `promptcompiler/storage.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/server.py`
- Test: `tests/test_session_context.py`
- Test: `tests/test_v1_api.py`

### Task 2.1: Add compact session context builder

- [ ] **Step 1: Write session context tests**

Create `tests/test_session_context.py`:

```python
import unittest

from promptcompiler.session_context import build_compact_session_context


class SessionContextTests(unittest.TestCase):
    def test_keeps_pinned_recent_and_summary_within_budget(self):
        turns = [
            {"id": "1", "role": "system", "content": "@pin Keep CASE-123.", "token_count": 8, "pinned": 1, "is_summary": 0},
            {"id": "2", "role": "user", "content": "old detail " * 20, "token_count": 40, "pinned": 0, "is_summary": 0},
            {"id": "3", "role": "assistant", "content": "older reply " * 20, "token_count": 40, "pinned": 0, "is_summary": 0},
            {"id": "4", "role": "system", "content": "[session summary] user wants compact prompts", "token_count": 10, "pinned": 0, "is_summary": 1},
            {"id": "5", "role": "user", "content": "current question", "token_count": 6, "pinned": 0, "is_summary": 0},
        ]

        context = build_compact_session_context(turns, target_token_budget=55, sliding_window_turns=1)

        text = "\n".join(item["content"] for item in context["messages"])
        self.assertIn("CASE-123", text)
        self.assertIn("[session summary]", text)
        self.assertIn("current question", text)
        self.assertLessEqual(context["token_count"], 55)
        self.assertEqual(context["strategy"], "pinned_summary_recent")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing context test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_session_context.py
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement builder**

Create `promptcompiler/session_context.py`:

```python
"""Build compact session context from stored turns."""

from __future__ import annotations

from typing import Any


def build_compact_session_context(
    turns: list[dict[str, Any]],
    target_token_budget: int | None,
    sliding_window_turns: int = 4,
) -> dict[str, Any]:
    budget = target_token_budget or sum(int(row.get("token_count") or 0) for row in turns)
    non_summary = [row for row in turns if not row.get("is_summary")]
    recent_ids = {str(row["id"]) for row in non_summary[-max(1, sliding_window_turns):]}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in turns:
        row_id = str(row["id"])
        if row.get("pinned") or row.get("is_summary") or row_id in recent_ids:
            if row_id not in seen:
                selected.append(row)
                seen.add(row_id)

    trimmed: list[dict[str, Any]] = []
    used = 0
    for row in selected:
        tokens = int(row.get("token_count") or 0)
        if row.get("pinned") or used + tokens <= budget:
            trimmed.append(row)
            used += tokens

    return {
        "strategy": "pinned_summary_recent",
        "token_count": used,
        "messages": [
            {
                "role": str(row.get("role") or "user"),
                "content": str(row.get("content") or ""),
                "source_turn_id": str(row.get("id")),
                "token_count": int(row.get("token_count") or 0),
                "pinned": bool(row.get("pinned")),
                "is_summary": bool(row.get("is_summary")),
            }
            for row in trimmed
            if row.get("content")
        ],
    }
```

- [ ] **Step 4: Run context tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_session_context.py
```

Expected: pass.

### Task 2.2: Add `/v1/sessions/{id}/context`

- [ ] **Step 1: Add API test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_session_context_returns_compact_messages(self):
        for index in range(3):
            status, _ = post_v1(
                "/v1/sessions/sess_context/append",
                {
                    "turn": {"role": "user", "content": f"turn {index} CASE-123 " + ("older " * 20)},
                    "target_token_budget": 90,
                    "zero_retention": False,
                },
            )
            self.assertEqual(status, 200)

        status, response = handle_api_request(
            "GET",
            "/v1/sessions/sess_context/context?target_token_budget=80&sliding_window_turns=1",
            b"",
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual(payload["session_id"], "sess_context")
        self.assertEqual(payload["context"]["strategy"], "pinned_summary_recent")
        self.assertLessEqual(payload["context"]["token_count"], 80)
        self.assertTrue(payload["context"]["messages"])
```

- [ ] **Step 2: Add store method**

Modify `promptcompiler/storage.py`:

```python
    def session_context(
        self,
        session_id: str,
        target_token_budget: int | None,
        sliding_window_turns: int,
    ) -> dict[str, Any]:
        from .session_context import build_compact_session_context

        turns = self.session_turn_rows(session_id)
        return build_compact_session_context(
            turns,
            target_token_budget=target_token_budget,
            sliding_window_turns=sliding_window_turns,
        )
```

- [ ] **Step 3: Add v1 helper**

Modify `promptcompiler/v1.py`:

```python
def session_context_v1(session_id: str, filters: dict[str, str]) -> dict[str, Any]:
    target = _target_budget(filters.get("target_token_budget"))
    window = int(filters.get("sliding_window_turns") or 4)
    return {
        "session_id": session_id,
        "target_token_budget": target,
        "sliding_window_turns": window,
        "context": get_store().session_context(session_id, target, window),
    }
```

- [ ] **Step 4: Route endpoint in server**

Modify `promptcompiler/server.py` to route:

```python
GET /v1/sessions/<session_id>/context
```

to `session_context_v1(session_id, query_params)`.

- [ ] **Step 5: Run API tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_session_context.py tests/test_v1_api.py
```

Expected: pass.

- [ ] **Step 6: Commit Phase 2**

Run:

```bash
git add promptcompiler/session_context.py promptcompiler/storage.py promptcompiler/v1.py promptcompiler/server.py tests/test_session_context.py tests/test_v1_api.py
git commit -m "feat: add compact session context builder"
```

---

## Phase 3: Payload Minification And Structured Input Normalization

**Implements:** markdown overhead reduction, JSON bloat reduction, raw document/log pre-compaction, natural-language-to-structured-envelope support.

**Files:**
- Create: `promptcompiler/minify.py`
- Modify: `promptcompiler/compiler.py`
- Modify: `promptcompiler/v1.py`
- Test: `tests/test_minify.py`
- Test: `tests/test_compiler.py`
- Test: `tests/test_v1_api.py`

### Task 3.1: Add minification primitives

- [ ] **Step 1: Write minify tests**

Create `tests/test_minify.py`:

```python
import unittest

from promptcompiler.minify import compact_json_text, compact_markdown_text, structured_input_to_text


class MinifyTests(unittest.TestCase):
    def test_compact_json_text_minifies_and_aliases_keys(self):
        raw = '{ "user_information": { "current_project_name": "HospiFlo" } }'

        compacted = compact_json_text(raw, aliases={"user_information": "user", "current_project_name": "project"})

        self.assertEqual(compacted, '{"user":{"project":"HospiFlo"}}')

    def test_compact_markdown_text_removes_internal_heading_markup(self):
        raw = "# Heading\n## Subheading\n- One\n- Two"

        compacted = compact_markdown_text(raw)

        self.assertEqual(compacted, "Heading\nSubheading\nOne\nTwo")

    def test_structured_input_to_text_uses_minified_json(self):
        text = structured_input_to_text({"age_gt": 20, "product": "shoes", "month": "last"})

        self.assertEqual(text, '{"age_gt":20,"product":"shoes","month":"last"}')


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_minify.py
```

Expected: fail because module does not exist.

- [ ] **Step 3: Implement minifier**

Create `promptcompiler/minify.py`:

```python
"""Local payload minification helpers."""

from __future__ import annotations

import json
import re
from typing import Any


def compact_json_text(text: str, aliases: dict[str, str] | None = None) -> str:
    value = json.loads(text)
    value = _alias_keys(value, aliases or {})
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def compact_markdown_text(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = re.sub(r"^[-*+]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def structured_input_to_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def maybe_compact_text(text: str, aliases: dict[str, str] | None = None) -> tuple[str, str | None]:
    stripped = text.strip()
    if not stripped:
        return text, None
    if stripped.startswith(("{", "[")):
        try:
            return compact_json_text(stripped, aliases=aliases), "json_minify"
        except json.JSONDecodeError:
            return text, None
    if any(line.lstrip().startswith(("#", "-", "*", "+")) for line in text.splitlines()):
        compacted = compact_markdown_text(text)
        return (compacted, "markdown_plaintext") if len(compacted) < len(text) else (text, None)
    return text, None


def _alias_keys(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            aliases.get(str(key), str(key)): _alias_keys(item, aliases)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_alias_keys(item, aliases) for item in value]
    return value
```

- [ ] **Step 4: Run minify tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_minify.py
```

Expected: pass.

### Task 3.2: Integrate minification into compile and v1 structured input

- [ ] **Step 1: Add compiler test**

Add to `tests/test_compiler.py`:

```python
    def test_balanced_mode_minifies_json_and_markdown_segments(self):
        payload = '{ "user_information": { "current_project_name": "HospiFlo" } }\n\n# Heading\n- Keep CASE-123'

        result = compile_prompt(payload, mode="balanced")

        self.assertIn('"current_project_name":"HospiFlo"', result["optimized_text"])
        self.assertIn("Heading\nKeep CASE-123", result["optimized_text"])
        self.assertTrue(any(action["action"] in {"json_minify", "markdown_plaintext"} for action in result["plan"]["actions"]))
```

- [ ] **Step 2: Add v1 structured input test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_compile_accepts_structured_input(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "structured_input": {"age_gt": 20, "product": "shoes", "month": "last"},
                "mode": "balanced",
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn('{"age_gt":20,"month":"last","product":"shoes"}', payload["optimized_prompt"])
```

- [ ] **Step 3: Modify compiler compact segment**

In `promptcompiler/compiler.py`, import:

```python
from .minify import maybe_compact_text
```

At the start of `_compact_segment()` after action initialization:

```python
    normalized_text, minify_action = maybe_compact_text(segment.text)
    minify_removed = max(0, estimate_text_tokens(segment.text) - estimate_text_tokens(normalized_text))
    if minify_action and mode != "lossless":
        actions.append(
            {
                "action": minify_action,
                "segment_ids": [segment.id],
                "reason": "Compacted structured or markdown input before model injection.",
                "estimated_tokens_saved": minify_removed,
            }
        )
    else:
        normalized_text = segment.text
        minify_removed = 0
```

Then run repeated-line compaction on `normalized_text` instead of `segment.text`, and include `minify_removed` in `removed`.

- [ ] **Step 4: Modify v1 raw input normalization**

In `promptcompiler/v1.py`, import:

```python
from .minify import structured_input_to_text
```

In `_raw_input_from_payload()`, before `input`:

```python
    if "structured_input" in payload:
        return structured_input_to_text(payload.get("structured_input")), "structured_input", []
```

- [ ] **Step 5: Run phase tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_minify.py tests/test_compiler.py tests/test_v1_api.py
```

Expected: pass.

- [ ] **Step 6: Commit Phase 3**

Run:

```bash
git add promptcompiler/minify.py promptcompiler/compiler.py promptcompiler/v1.py tests/test_minify.py tests/test_compiler.py tests/test_v1_api.py
git commit -m "feat: compact structured prompt payloads"
```

---

## Phase 4: Retrieval, RAG, Document, And Search-Result Budgeting

**Implements:** chunking instead of raw documents, better RAG, too many retrieved search results, context compression.

**Files:**
- Create: `promptcompiler/retrieval.py`
- Modify: `promptcompiler/semantic.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/server.py`
- Test: `tests/test_retrieval.py`
- Test: `tests/test_v1_api.py`

### Task 4.1: Add retrieval budgeter

- [ ] **Step 1: Write retrieval tests**

Create `tests/test_retrieval.py`:

```python
import unittest

from promptcompiler.retrieval import select_retrieval_context


class RetrievalTests(unittest.TestCase):
    def test_selects_top_k_under_token_budget_and_dedupes(self):
        chunks = [
            {"id": "a", "source": "doc-a", "text": "refund approval over 500 manager", "tokens": 20},
            {"id": "b", "source": "doc-b", "text": "refund approval over 500 manager", "tokens": 20},
            {"id": "c", "source": "doc-c", "text": "shipping delay policy", "tokens": 20},
        ]

        result = select_retrieval_context(
            query="refund over 500",
            chunks=chunks,
            top_k=3,
            max_tokens=35,
            similarity_threshold=0.8,
        )

        ids = [item["id"] for item in result["chunks"]]
        self.assertEqual(ids, ["a"])
        self.assertEqual(result["tokens"], 20)
        self.assertIn("b", result["removed_chunk_ids"])
```

- [ ] **Step 2: Implement retrieval selector**

Create `promptcompiler/retrieval.py`:

```python
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
        if any(_jaccard(_tokens(str(item.get("text") or "")), _tokens(str(chunk.get("text") or ""))) >= similarity_threshold for item in selected):
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
```

- [ ] **Step 3: Run retrieval tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_retrieval.py
```

Expected: pass.

### Task 4.2: Add `/v1/retrieve`

- [ ] **Step 1: Add API test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_retrieve_budgets_rag_chunks(self):
        status, response = post_v1(
            "/v1/retrieve",
            {
                "query": "refund over 500",
                "rag_chunks": [
                    {"id": "a", "source": "doc-a", "text": "refund approval over 500 manager"},
                    {"id": "b", "source": "doc-b", "text": "refund approval over 500 manager"},
                    {"id": "c", "source": "doc-c", "text": "shipping policy"},
                ],
                "top_k": 2,
                "max_tokens": 12,
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in payload["chunks"]], ["a"])
        self.assertIn("b", payload["removed_chunk_ids"])
```

- [ ] **Step 2: Add v1 helper**

Modify `promptcompiler/v1.py`:

```python
from .retrieval import select_retrieval_context
from .tokenizer import estimate_text_tokens
```

Add:

```python
def retrieve_v1(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query") or "")
    chunks = []
    for index, item in enumerate(payload.get("rag_chunks") or []):
        if isinstance(item, dict):
            text = _content_to_text(item.get("text", item.get("content", "")))
            chunks.append({
                "id": str(item.get("id") or item.get("source") or f"chunk_{index + 1}"),
                "source": str(item.get("source") or item.get("id") or f"chunk_{index + 1}"),
                "text": text,
                "tokens": estimate_text_tokens(text),
            })
    return select_retrieval_context(
        query=query,
        chunks=chunks,
        top_k=int(payload.get("top_k") or 5),
        max_tokens=int(payload.get("max_tokens") or 1200),
    )
```

- [ ] **Step 3: Route endpoint**

Modify `promptcompiler/server.py` to route `POST /v1/retrieve` to `retrieve_v1()`.

- [ ] **Step 4: Run phase tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_retrieval.py tests/test_v1_api.py
```

Expected: pass.

- [ ] **Step 5: Commit Phase 4**

Run:

```bash
git add promptcompiler/retrieval.py promptcompiler/v1.py promptcompiler/server.py tests/test_retrieval.py tests/test_v1_api.py
git commit -m "feat: add budgeted retrieval context"
```

---

## Phase 5: Tool Schema Slimming And Dynamic Tool Selection

**Implements:** long function schema/tool definition reduction and dynamic loading of only needed tools.

**Files:**
- Create: `promptcompiler/tools.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/proxy.py`
- Test: `tests/test_tools.py`
- Test: `tests/test_v1_api.py`

### Task 5.1: Add schema compaction and selection

- [ ] **Step 1: Write tool tests**

Create `tests/test_tools.py`:

```python
import unittest

from promptcompiler.tools import compact_tool_schema, select_tools_for_query


class ToolTests(unittest.TestCase):
    def test_compact_tool_schema_removes_verbose_fields(self):
        tool = {
            "name": "lookup_refund_policy",
            "description": "Use this tool to look up the refund policy. " * 8,
            "examples": ["example " * 20],
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "Ticket id such as CASE-123."},
                },
            },
        }

        compacted = compact_tool_schema(tool)

        self.assertIn("name", compacted)
        self.assertIn("parameters", compacted)
        self.assertNotIn("examples", compacted)
        self.assertLess(len(str(compacted)), len(str(tool)))

    def test_select_tools_for_query_keeps_relevant_names(self):
        tools = [
            {"name": "lookup_refund_policy", "description": "refund manager approval"},
            {"name": "book_flight", "description": "travel booking"},
        ]

        selected = select_tools_for_query("Can we approve this refund?", tools, max_tools=1)

        self.assertEqual(selected[0]["name"], "lookup_refund_policy")
```

- [ ] **Step 2: Implement tools module**

Create `promptcompiler/tools.py`:

```python
"""Tool schema compaction and relevance selection."""

from __future__ import annotations

import re
from typing import Any


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def compact_tool_schema(tool: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key in ("type", "name", "function"):
        if key in tool:
            compacted[key] = tool[key]
    if "description" in tool:
        compacted["description"] = _shorten(str(tool["description"]), 160)
    if "parameters" in tool:
        compacted["parameters"] = _compact_parameters(tool["parameters"])
    return compacted


def select_tools_for_query(query: str, tools: list[dict[str, Any]], max_tools: int = 8) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored = []
    for index, tool in enumerate(tools):
        haystack = f"{tool.get('name', '')} {tool.get('description', '')}"
        score = len(query_tokens & _tokens(haystack))
        scored.append((score, index, compact_tool_schema(tool)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [tool for score, _, tool in scored[:max_tools] if score > 0] or [tool for _, _, tool in scored[:max_tools]]


def _compact_parameters(value: Any) -> Any:
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            if key in {"examples", "example", "$comment"}:
                continue
            if key == "description" and isinstance(item, str):
                output[key] = _shorten(item, 120)
            else:
                output[key] = _compact_parameters(item)
        return output
    if isinstance(value, list):
        return [_compact_parameters(item) for item in value]
    return value


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "."


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}
```

- [ ] **Step 3: Run tool tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_tools.py
```

Expected: pass.

### Task 5.2: Wire tool selection into v1 payload normalization

- [ ] **Step 1: Add API test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_compile_compacts_and_selects_tools(self):
        status, response = post_v1(
            "/v1/compile",
            {
                "messages": [{"role": "user", "content": "Need refund policy for CASE-123."}],
                "tools": [
                    {"name": "lookup_refund_policy", "description": "refund manager approval " * 20, "examples": ["long"]},
                    {"name": "book_flight", "description": "travel booking " * 20, "examples": ["long"]},
                ],
                "tool_policy": {"max_tools": 1, "compact": True},
                "mode": "balanced",
            },
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertIn("lookup_refund_policy", payload["optimized_prompt"])
        self.assertNotIn("book_flight", payload["optimized_prompt"])
        self.assertIn("tool_policy", payload)
```

- [ ] **Step 2: Modify v1 tool normalization**

In `promptcompiler/v1.py`, import:

```python
from .tools import select_tools_for_query
```

Add `tool_policy` to `NormalizedV1Request`, normalize `payload.get("tool_policy")`, and pass it into `_raw_input_from_payload()`.

Update `_tools_to_text()` to accept `query` and `tool_policy`; when `tool_policy.get("compact")` is true, call `select_tools_for_query(query, tool_objects, max_tools=int(tool_policy.get("max_tools") or 8))` before serializing.

- [ ] **Step 3: Return tool policy metadata**

Add to analyze and compile responses:

```python
        "tool_policy": request.tool_policy,
```

- [ ] **Step 4: Run phase tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_tools.py tests/test_v1_api.py
```

Expected: pass.

- [ ] **Step 5: Commit Phase 5**

Run:

```bash
git add promptcompiler/tools.py promptcompiler/v1.py promptcompiler/proxy.py tests/test_tools.py tests/test_v1_api.py
git commit -m "feat: compact and select tool schemas"
```

---

## Phase 6: Model Routing, Hybrid Routing, And Caching

**Implements:** smaller models for simple tasks, hybrid routing, provider prompt-cache hints, local compile cache.

**Files:**
- Create: `promptcompiler/routing.py`
- Create: `promptcompiler/cache.py`
- Modify: `promptcompiler/storage.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/proxy.py`
- Test: `tests/test_routing.py`
- Test: `tests/test_cache.py`
- Test: `tests/test_v1_api.py`

### Task 6.1: Add local model router

- [ ] **Step 1: Write routing tests**

Create `tests/test_routing.py`:

```python
import unittest

from promptcompiler.routing import choose_model_route


class RoutingTests(unittest.TestCase):
    def test_routes_simple_formatting_to_small_model(self):
        route = choose_model_route({"task_type": "formatting", "total_tokens": 200})

        self.assertEqual(route["tier"], "small")
        self.assertEqual(route["reason"], "simple_task")

    def test_routes_large_complex_prompt_to_primary_model(self):
        route = choose_model_route({"task_type": "analysis", "total_tokens": 12000})

        self.assertEqual(route["tier"], "primary")
        self.assertEqual(route["reason"], "complex_or_large_task")
```

- [ ] **Step 2: Implement router**

Create `promptcompiler/routing.py`:

```python
"""Simple local model routing policy."""

from __future__ import annotations

from typing import Any


_SIMPLE_TASKS = {"grammar", "regex", "summarization", "classification", "formatting", "json_repair"}


def choose_model_route(features: dict[str, Any]) -> dict[str, str]:
    task_type = str(features.get("task_type") or "").strip().lower()
    total_tokens = int(features.get("total_tokens") or 0)
    if task_type in _SIMPLE_TASKS and total_tokens <= 2000:
        return {"tier": "small", "reason": "simple_task", "model_hint": "small"}
    if total_tokens <= 800 and task_type:
        return {"tier": "small", "reason": "short_task", "model_hint": "small"}
    return {"tier": "primary", "reason": "complex_or_large_task", "model_hint": "primary"}
```

- [ ] **Step 3: Run routing tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_routing.py
```

Expected: pass.

### Task 6.2: Add compile cache

- [ ] **Step 1: Write cache tests**

Create `tests/test_cache.py`:

```python
import unittest

from promptcompiler.cache import cache_key_for_compile


class CacheTests(unittest.TestCase):
    def test_cache_key_is_stable_for_same_compile_inputs(self):
        first = cache_key_for_compile("hello", {"mode": "balanced", "model": "gpt-4o-mini"})
        second = cache_key_for_compile("hello", {"model": "gpt-4o-mini", "mode": "balanced"})

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("pcache_"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement cache key helper**

Create `promptcompiler/cache.py`:

```python
"""PromptCompiler cache helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def cache_key_for_compile(raw_input: str, policy: dict[str, Any]) -> str:
    payload = {
        "raw_input": raw_input,
        "policy": policy,
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "pcache_" + hashlib.sha256(encoded).hexdigest()
```

- [ ] **Step 3: Add SQLite compile cache table**

Modify `promptcompiler/storage.py` `_initialize()`:

```sql
CREATE TABLE IF NOT EXISTS compile_cache (
    cache_key TEXT PRIMARY KEY,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

Add methods:

```python
    def get_compile_cache(self, cache_key: str) -> dict[str, Any] | None:
        row = self._fetchone("SELECT response_json FROM compile_cache WHERE cache_key = ?", (cache_key,))
        return json.loads(row["response_json"]) if row else None

    def set_compile_cache(self, cache_key: str, response: dict[str, Any]) -> None:
        self._execute(
            "INSERT OR REPLACE INTO compile_cache (cache_key, response_json, created_at) VALUES (?, ?, ?)",
            (cache_key, json.dumps(response, ensure_ascii=True), _now()),
        )
```

- [ ] **Step 4: Wire cache into `compile_v1()`**

In `promptcompiler/v1.py`, compute a cache key when `payload.get("cache_policy", {}).get("enabled")` is true. Check `get_store().get_compile_cache(cache_key)` before compiling. On hit, return cached response with:

```python
response["cache"] = {"status": "hit", "key": cache_key}
```

On miss, compile normally, set:

```python
response["cache"] = {"status": "miss", "key": cache_key}
```

and store the response.

- [ ] **Step 5: Add API cache/routing test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_compile_cache_hit_and_route_metadata(self):
        payload = {
            "messages": [{"role": "user", "content": "format this json"}],
            "mode": "balanced",
            "task_type": "formatting",
            "cache_policy": {"enabled": True},
        }
        first_status, first_response = post_v1("/v1/compile", payload)
        second_status, second_response = post_v1("/v1/compile", payload)

        first = json.loads(first_response)
        second = json.loads(second_response)
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)
        self.assertEqual(first["cache"]["status"], "miss")
        self.assertEqual(second["cache"]["status"], "hit")
        self.assertEqual(second["route"]["tier"], "small")
```

- [ ] **Step 6: Add route metadata in compile**

In `compile_v1()`, call:

```python
route = choose_model_route({"task_type": payload.get("task_type"), "total_tokens": result["original_tokens"]})
```

Return:

```python
"route": route,
"provider_cache_hints": {
    "static_prefix_cacheable": request.context_policy.get("cache_static_prefix", False),
    "cache_key": cache_key,
},
```

- [ ] **Step 7: Run phase tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_routing.py tests/test_cache.py tests/test_v1_api.py
```

Expected: pass.

- [ ] **Step 8: Commit Phase 6**

Run:

```bash
git add promptcompiler/routing.py promptcompiler/cache.py promptcompiler/storage.py promptcompiler/v1.py promptcompiler/proxy.py tests/test_routing.py tests/test_cache.py tests/test_v1_api.py
git commit -m "feat: add routing and compile cache"
```

---

## Phase 7: Token-Waste Linting And Agent Guardrails

**Implements:** multi-task decomposition guidance, bad agent-framework loop detection, repeated reasoning/reflection detection, general token-waste advice.

**Files:**
- Create: `promptcompiler/lint.py`
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/server.py`
- Modify: `web/app.js`
- Test: `tests/test_lint.py`
- Test: `tests/test_v1_api.py`

### Task 7.1: Add lint rules

- [ ] **Step 1: Write lint tests**

Create `tests/test_lint.py`:

```python
import unittest

from promptcompiler.lint import lint_token_waste


class LintTests(unittest.TestCase):
    def test_detects_multi_task_prompt(self):
        findings = lint_token_waste("Analyze this code, explain it, optimize it, write tests, generate docs")

        self.assertTrue(any(item["code"] == "MULTI_TASK_REQUEST" for item in findings))

    def test_detects_agent_reflection_loops(self):
        findings = lint_token_waste("Thought: check\nReflection: maybe retry\nSelf critique: retry again")

        self.assertTrue(any(item["code"] == "AGENT_REFLECTION_OVERHEAD" for item in findings))

    def test_detects_large_system_prompt(self):
        findings = lint_token_waste("You are the world's best AI assistant. " * 200)

        self.assertTrue(any(item["code"] == "HUGE_SYSTEM_PROMPT" for item in findings))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement lint module**

Create `promptcompiler/lint.py`:

```python
"""Token waste linting rules."""

from __future__ import annotations

from .tokenizer import estimate_text_tokens


def lint_token_waste(text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    lowered = text.lower()
    tokens = estimate_text_tokens(text)
    if tokens > 1200 and ("you are" in lowered or "assistant" in lowered[:500]):
        findings.append({
            "code": "HUGE_SYSTEM_PROMPT",
            "severity": "high",
            "message": "Large reusable instruction block should move to a prompt_ref or server-side policy.",
        })
    multi_markers = sum(1 for marker in ("analyze", "explain", "optimize", "write tests", "generate docs") if marker in lowered)
    if multi_markers >= 3:
        findings.append({
            "code": "MULTI_TASK_REQUEST",
            "severity": "medium",
            "message": "Split this request into sequential compile/analyze/test/doc steps.",
        })
    if any(marker in lowered for marker in ("reflection:", "self critique", "self-critique", "thought:")):
        findings.append({
            "code": "AGENT_REFLECTION_OVERHEAD",
            "severity": "medium",
            "message": "Remove recursive agent reasoning and reflection blocks before provider calls.",
        })
    if lowered.count("source:") > 10:
        findings.append({
            "code": "TOO_MANY_RETRIEVED_RESULTS",
            "severity": "high",
            "message": "Apply top-k retrieval and chunk compression before injection.",
        })
    return findings
```

- [ ] **Step 3: Run lint tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_lint.py
```

Expected: pass.

### Task 7.2: Add `/v1/lint`

- [ ] **Step 1: Add API test**

Add to `tests/test_v1_api.py`:

```python
    def test_v1_lint_returns_token_waste_findings(self):
        status, response = post_v1(
            "/v1/lint",
            {"input": "Analyze this code, explain it, optimize it, write tests, generate docs"},
        )

        payload = json.loads(response)
        self.assertEqual(status, 200)
        self.assertTrue(any(item["code"] == "MULTI_TASK_REQUEST" for item in payload["findings"]))
```

- [ ] **Step 2: Implement v1 lint helper**

Modify `promptcompiler/v1.py`:

```python
from .lint import lint_token_waste
```

Add:

```python
def lint_v1(payload: dict[str, Any]) -> dict[str, Any]:
    raw_input, payload_kind, _ = _raw_input_from_payload(payload)
    return {
        "payload_kind": payload_kind,
        "findings": lint_token_waste(raw_input),
    }
```

- [ ] **Step 3: Route endpoint**

Modify `promptcompiler/server.py` to route `POST /v1/lint` to `lint_v1()`.

- [ ] **Step 4: Add UI lint panel**

Modify `web/app.js` to call `/v1/lint` after analysis and render findings in the existing analytics/changes area. Keep the UI terse: finding code, severity, message.

- [ ] **Step 5: Run phase tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_lint.py tests/test_v1_api.py tests/test_web_e2e.py
```

Expected: pass.

- [ ] **Step 6: Commit Phase 7**

Run:

```bash
git add promptcompiler/lint.py promptcompiler/v1.py promptcompiler/server.py web/app.js tests/test_lint.py tests/test_v1_api.py
git commit -m "feat: add token waste linting"
```

---

## Phase 8: Documentation, Web Controls, And Full Verification

**Implements:** makes all token-saving controls discoverable and verifies the whole product story.

**Files:**
- Modify: `README.md`
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `tests/web_e2e_runner.mjs`
- Test: `tests/test_static_assets.py`
- Test: `tests/test_web_e2e.py`

### Task 8.1: Add docs and examples

- [ ] **Step 1: Update README token-saving section**

Add a section to `README.md`:

```markdown
## Token Reduction Controls

PromptCompiler can reduce provider input tokens through:

- `context_policy.system_prompt_ref` for reusable instructions.
- `output_policy` for short JSON, bullet, or plain responses.
- `structured_input` for compact machine-readable inputs.
- `tool_policy` for schema compaction and relevant-tool selection.
- `/v1/retrieve` for top-k retrieval under a token budget.
- `/v1/sessions/{id}/context` for pinned + summary + recent session context.
- `cache_policy.enabled` for local compile cache metadata.
- `/v1/lint` for token-waste findings before a request is sent.
```

- [ ] **Step 2: Add cURL examples**

Add examples for `/v1/compile` with policies, `/v1/retrieve`, `/v1/lint`, and `/v1/sessions/{id}/context`.

### Task 8.2: Add web controls without clutter

- [ ] **Step 1: Add compact controls**

Modify `web/index.html`:

- Add mode/policy controls only in the existing settings/control area.
- Add fields for system prompt ref, output format, max words, retrieval top-k, cache enabled, and lint action.
- Keep labels short.

- [ ] **Step 2: Wire payload in `web/app.js`**

Compile payload should include:

```javascript
context_policy: {
  system_prompt_ref: systemPromptRef.value || null,
  cache_static_prefix: cacheStaticPrefix.checked,
},
output_policy: {
  max_words: Number(maxWordsInput.value) || null,
  format: outputFormatSelect.value,
  explain: explainToggle.checked,
},
cache_policy: {
  enabled: cacheEnabled.checked,
}
```

- [ ] **Step 3: Render metadata**

Render route tier, cache status, provider cache hints, lint findings, policy summary, and token savings without adding tutorial text inside the app.

### Task 8.3: End-to-end verification

- [ ] **Step 1: Run focused unit tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest \
  tests/test_policies.py \
  tests/test_session_context.py \
  tests/test_minify.py \
  tests/test_retrieval.py \
  tests/test_tools.py \
  tests/test_routing.py \
  tests/test_cache.py \
  tests/test_lint.py
```

Expected: pass.

- [ ] **Step 2: Run API and SDK tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_v1_api.py tests/test_sdk.py tests/test_proxy.py
```

If `tests/test_proxy.py` does not exist, run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_v1_api.py tests/test_sdk.py
```

Expected: pass.

- [ ] **Step 3: Run static and browser tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_static_assets.py tests/test_web_e2e.py
```

Expected: pass.

- [ ] **Step 4: Run full test suite**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests
```

Expected: pass.

- [ ] **Step 5: Manual smoke**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m promptcompiler.server
```

Open `http://127.0.0.1:8765`, compile a prompt with repeated JSON/markdown/RAG/tool content, and confirm the page shows optimized tokens, route tier, cache status, transformations, and lint findings.

- [ ] **Step 6: Commit Phase 8**

Run:

```bash
git add README.md web/index.html web/app.js web/styles.css tests/web_e2e_runner.mjs tests/test_static_assets.py tests/test_web_e2e.py
git commit -m "docs: document token reduction controls"
```

---

## Final Acceptance Criteria

- `/v1/compile` accepts and returns `context_policy`, `output_policy`, `tool_policy`, `cache_policy`, `route`, and provider cache hints.
- `/v1/sessions/{id}/context` returns pinned + summary + recent context under a budget.
- `/v1/retrieve` returns top-k deduped chunks under a token budget.
- `/v1/lint` detects large prompts, multi-task prompts, agent reflection overhead, and excessive retrieved results.
- SDK and proxy can pass all policies through without leaking raw payloads when zero retention is enabled.
- Metrics continue to report original tokens, optimized tokens, tokens saved, mode usage, cache status, and session compactions.
- Full suite passes with:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests
```

## Execution Notes

- Implement phases in order. Later phases assume earlier request policy fields exist.
- Keep every phase backward-compatible with existing payloads.
- Preserve `@pin` content exactly.
- Never store raw prompt payloads in traces.
- Treat provider prompt caching as metadata/hints until live upstream forwarding is added.
- Do not implement speculative decoding inside this repo.
