# NIM-First PromptCompiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first PromptCompiler workbench with deterministic prompt analysis/compile and optional NVIDIA NIM summarization.

**Architecture:** A Python standard-library server exposes JSON endpoints and serves a static browser UI. Core prompt logic lives in small Python modules that are easy to test without a network or paid model API.

**Tech Stack:** Python 3.11+ standard library, `unittest`, static HTML/CSS/JavaScript, NVIDIA NIM OpenAI-compatible HTTP API.

---

### Task 1: Test Core Parsing And Analysis

**Files:**
- Create: `tests/test_analyzer.py`
- Create: `tests/test_entities.py`

- [ ] **Step 1: Write failing tests for raw and OpenAI-compatible analysis**

```python
from promptcompiler.analyzer import analyze_prompt


def test_analyze_openai_messages_breaks_down_roles_and_pins():
    payload = '{"messages":[{"role":"system","content":"@pin Follow policy CASE-123."},{"role":"user","content":"Hello Hello"}]}'
    result = analyze_prompt(payload)
    assert result["segment_count"] == 2
    assert result["by_role"]["system"] > 0
    assert result["by_role"]["user"] > 0
    assert result["segments"][0]["pinned"] is True
    assert "CASE-123" in result["protected_entities"]


def test_analyze_detects_duplicate_plain_text_paragraphs():
    result = analyze_prompt("repeat me\n\nrepeat me\n\nunique")
    assert result["segment_count"] == 3
    assert result["duplicate_groups"][0]["count"] == 2
```

- [ ] **Step 2: Write failing tests for protected entity extraction**

```python
from promptcompiler.entities import extract_entities


def test_extract_entities_finds_values_that_should_survive_compile():
    text = "Visit https://example.com on 2026-05-23 for CASE-123, $49.99, and 95%."
    entities = extract_entities(text)
    assert "https://example.com" in entities
    assert "2026-05-23" in entities
    assert "CASE-123" in entities
    assert "$49.99" in entities
    assert "95%" in entities
```

- [ ] **Step 3: Run tests and verify they fail because modules do not exist**

Run: `python3 -m unittest tests/test_analyzer.py tests/test_entities.py`

Expected: import failure for `promptcompiler`.

### Task 2: Implement Analyzer Core

**Files:**
- Create: `promptcompiler/__init__.py`
- Create: `promptcompiler/parser.py`
- Create: `promptcompiler/tokenizer.py`
- Create: `promptcompiler/entities.py`
- Create: `promptcompiler/analyzer.py`

- [ ] **Step 1: Implement parser, tokenizer, entity extraction, and analyzer**

Use dataclass segments, parse JSON messages or plain paragraphs, estimate tokens with regex, extract protected entities with regex, and report duplicate normalized text groups.

- [ ] **Step 2: Run analyzer tests**

Run: `python3 -m unittest tests/test_analyzer.py tests/test_entities.py`

Expected: pass.

### Task 3: Test Deterministic Compile

**Files:**
- Create: `tests/test_compiler.py`

- [ ] **Step 1: Write failing compile tests**

```python
from promptcompiler.compiler import compile_prompt


def test_compile_removes_duplicate_unpinned_segments_but_preserves_pin():
    payload = "@pin Keep CASE-123 exactly.\n\nremove me\n\nremove me"
    result = compile_prompt(payload)
    assert "@pin Keep CASE-123 exactly." in result["optimized_text"]
    assert result["optimized_text"].count("remove me") == 1
    assert result["tokens_saved"] > 0
    assert any(change["type"] == "duplicate_removed" for change in result["changes"])


def test_compile_compacts_repeated_log_lines():
    payload = "ERROR same failure\nERROR same failure\nERROR same failure\nnext line"
    result = compile_prompt(payload)
    assert "[repeated 2 more times]" in result["optimized_text"]
    assert "next line" in result["optimized_text"]
```

- [ ] **Step 2: Run tests and verify they fail because compiler does not exist**

Run: `python3 -m unittest tests/test_compiler.py`

Expected: import failure for `promptcompiler.compiler`.

### Task 4: Implement Deterministic Compiler

**Files:**
- Create: `promptcompiler/compiler.py`

- [ ] **Step 1: Implement compile pipeline**

Remove exact duplicate unpinned segments, compact repeated adjacent lines, preserve pinned segments exactly, and report token savings.

- [ ] **Step 2: Run compiler tests**

Run: `python3 -m unittest tests/test_compiler.py`

Expected: pass.

### Task 5: Test And Implement NIM Client

**Files:**
- Create: `tests/test_nim.py`
- Create: `promptcompiler/nim.py`

- [ ] **Step 1: Write failing tests for missing key and payload construction**

```python
import os
import unittest
from unittest.mock import patch

from promptcompiler.nim import NimClient, NimConfigError


class NimClientTests(unittest.TestCase):
    def test_missing_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NimConfigError):
                NimClient.from_env()

    def test_builds_openai_compatible_payload(self):
        client = NimClient(api_key="test-key")
        payload = client.build_summarize_payload("Preserve CASE-123.", "openai/gpt-oss-20b")
        self.assertEqual(payload["model"], "openai/gpt-oss-20b")
        self.assertEqual(payload["temperature"], 0.1)
        self.assertIn("Preserve CASE-123.", payload["messages"][-1]["content"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test and verify it fails because NIM module is missing**

Run: `python3 -m unittest tests/test_nim.py`

Expected: import failure for `promptcompiler.nim`.

- [ ] **Step 3: Implement NIM client**

Use `urllib.request` with `Authorization: Bearer <key>`, endpoint `https://integrate.api.nvidia.com/v1/chat/completions`, and structured errors.

- [ ] **Step 4: Run NIM tests**

Run: `python3 -m unittest tests/test_nim.py`

Expected: pass.

### Task 6: Build Local Server And UI

**Files:**
- Create: `promptcompiler/server.py`
- Create: `web/index.html`
- Create: `web/styles.css`
- Create: `web/app.js`
- Create: `README.md`

- [ ] **Step 1: Implement local API server**

Expose `GET /api/health`, `POST /api/analyze`, `POST /api/compile`, `POST /api/nim/summarize`, and static file serving.

- [ ] **Step 2: Implement workbench UI**

Create an editor, model input, Analyze and Compile buttons, metric panels, segment table, change report, optimized output, and NIM status/action.

- [ ] **Step 3: Run full tests**

Run: `python3 -m unittest discover -s tests`

Expected: all tests pass.

- [ ] **Step 4: Start the app**

Run: `python3 -m promptcompiler.server`

Expected: server listens on `http://127.0.0.1:8765`.

- [ ] **Step 5: Browser smoke test**

Open `http://127.0.0.1:8765`, run Analyze and Compile on repeated sample input, and verify the UI shows token metrics and optimized output.
