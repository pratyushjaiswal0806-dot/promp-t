# Phase 2 Compression Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PRD/TRD compression modes, target budgets, dry-run planning, pinned quota enforcement, and local balanced/aggressive compaction.

**Architecture:** Keep the existing Python/static architecture. Extend `compile_prompt()` with policy parameters and return planning metadata, then expose those controls through `/api/compile`, `/api/export`, and the dashboard.

**Tech Stack:** Python standard library, `unittest`, static HTML/CSS/JavaScript.

---

### Task 1: Add Compiler Policy Tests

**Files:**
- Modify: `tests/test_compiler.py`

- [ ] **Step 1: Add tests for default lossless behavior and metadata**

```python
def test_compile_defaults_to_lossless_mode_and_returns_plan_metadata(self):
    result = compile_prompt("@pin Keep CASE-123.\n\nrepeat\n\nrepeat")

    self.assertEqual(result["mode"], "lossless")
    self.assertFalse(result["dry_run"])
    self.assertIn("plan", result)
    self.assertEqual(result["plan"]["mode"], "lossless")
    self.assertTrue(any(action["action"] == "dedupe" for action in result["plan"]["actions"]))
```

- [ ] **Step 2: Add tests for dry run**

```python
def test_compile_dry_run_returns_plan_without_activating_output(self):
    result = compile_prompt("alpha\n\nalpha", dry_run=True)

    self.assertTrue(result["dry_run"])
    self.assertEqual(result["optimized_text"], "alpha\n\nalpha")
    self.assertGreater(result["proposed_tokens_saved"], 0)
    self.assertTrue(any(action["action"] == "dedupe" for action in result["plan"]["actions"]))
```

- [ ] **Step 3: Add tests for pinned quota**

```python
def test_compile_rejects_pinned_content_over_target_budget_cap(self):
    with self.assertRaises(CompilePolicyError) as raised:
        compile_prompt("@pin one two three four five six seven eight", target_token_budget=8)

    self.assertEqual(raised.exception.status_code, 413)
    self.assertEqual(raised.exception.error_code, "PINNED_BUDGET_EXCEEDED")
```

- [ ] **Step 4: Add tests for balanced and aggressive savings**

```python
def test_balanced_mode_compacts_tool_output_more_than_lossless(self):
    payload = "ERROR noisy line\n" * 95 + "CASE-123 must stay\n" + "tail line\n" * 20

    lossless = compile_prompt(payload, mode="lossless")
    balanced = compile_prompt(payload, mode="balanced")

    self.assertIn("CASE-123", balanced["optimized_text"])
    self.assertLess(balanced["optimized_tokens"], lossless["optimized_tokens"])
    self.assertTrue(any(action["action"] == "tool_summary" for action in balanced["plan"]["actions"]))


def test_aggressive_mode_returns_warning_when_target_cannot_be_met_safely(self):
    result = compile_prompt("@pin Keep CASE-123 exactly.\n\n" + ("word " * 80), mode="aggressive", target_token_budget=8)

    self.assertIn("@pin Keep CASE-123 exactly.", result["optimized_text"])
    self.assertTrue(result["warnings"])
```

### Task 2: Implement Compiler Policy Core

**Files:**
- Modify: `promptcompiler/compiler.py`

- [ ] **Step 1: Add `CompilePolicyError`**

```python
class CompilePolicyError(ValueError):
    def __init__(self, message: str, status_code: int, error_code: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
```

- [ ] **Step 2: Extend `compile_prompt()` signature**

```python
def compile_prompt(
    raw_input: str,
    model: str = DEFAULT_NIM_MODEL,
    mode: str = "lossless",
    target_token_budget: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
```

- [ ] **Step 3: Add mode validation and pinned quota enforcement**

Allowed modes are `lossless`, `balanced`, and `aggressive`. Pinned quota uses `target_token_budget` when present, otherwise original token count. If pinned tokens exceed 25 percent of that budget, raise `CompilePolicyError`.

- [ ] **Step 4: Add planning metadata**

Return:

```python
"mode": mode,
"target_token_budget": target_token_budget,
"dry_run": dry_run,
"proposed_optimized_text": proposed_text,
"proposed_tokens_saved": proposed_tokens_saved,
"plan": {
    "mode": mode,
    "target_token_budget": target_token_budget,
    "risk_level": "low|medium|high",
    "actions": actions,
},
"warnings": warnings,
"evaluation_status": "not_configured",
"cache_status": "bypass",
```

- [ ] **Step 5: Implement local balanced/aggressive transforms**

Balanced and aggressive keep pinned content exact and preserve protected entities. Balanced compresses verbose tool/RAG segments harder than lossless and summarizes older unpinned history. Aggressive applies stronger budget-driven truncation and returns warnings when the target remains unmet.

### Task 3: Expose Policy Through The Server

**Files:**
- Modify: `promptcompiler/server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Add server tests**

```python
def test_compile_endpoint_accepts_mode_budget_and_dry_run(self):
    status, response = handle_api_request(
        "POST",
        "/api/compile",
        json.dumps({"input": "repeat\n\nrepeat", "mode": "balanced", "target_token_budget": 20, "dry_run": True}).encode("utf-8"),
    )

    payload = json.loads(response)
    self.assertEqual(status, 200)
    self.assertEqual(payload["mode"], "balanced")
    self.assertTrue(payload["dry_run"])
    self.assertIn("plan", payload)


def test_compile_endpoint_returns_413_for_pinned_quota(self):
    status, response = handle_api_request(
        "POST",
        "/api/compile",
        json.dumps({"input": "@pin one two three four five six seven eight", "target_token_budget": 8}).encode("utf-8"),
    )

    payload = json.loads(response)
    self.assertEqual(status, 413)
    self.assertEqual(payload["code"], "PINNED_BUDGET_EXCEEDED")
```

- [ ] **Step 2: Parse policy payload fields**

Add helpers for mode, target token budget, and dry run, and pass them into `compile_prompt()` for `/api/compile` and `/api/export`.

- [ ] **Step 3: Catch `CompilePolicyError`**

Return the error status, code, message, and details as JSON.

### Task 4: Add Dashboard Controls

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `tests/web_e2e_runner.mjs`

- [ ] **Step 1: Add controls**

Add `#modeSelect`, `#targetBudgetInput`, and `#dryRunInput` to the control panel.

- [ ] **Step 2: Include policy in compile and export payloads**

`compilePrompt()` and `exportJson()` should send:

```javascript
{
  input: input.value,
  model: selectedModel,
  mode: modeSelect.value,
  target_token_budget: Number(targetBudgetInput.value) || null,
  dry_run: dryRunInput.checked
}
```

- [ ] **Step 3: Render plan and warnings**

Show `plan.actions`, `warnings`, mode, and target budget in existing metrics/changes/diff sections.

- [ ] **Step 4: Extend E2E checks**

The browser test should set `balanced`, a target budget, click compile, and verify the plan/action text appears.

### Task 5: Verify Phase 2

**Files:**
- Modify only if verification reveals issues in files touched by this plan.

- [ ] **Step 1: Run focused tests**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_compiler.py tests/test_server.py tests/test_web_e2e.py`

Expected: pass.

- [ ] **Step 2: Run full suite**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests`

Expected: pass.

- [ ] **Step 3: Browser smoke**

Open `http://127.0.0.1:8765`, choose Balanced mode, set a target budget, compile a sample, and confirm plan actions and warnings render.

### Self-Review Notes

- This phase intentionally avoids embeddings, Redis, LLM judges, and proxy forwarding.
- The implementation must preserve `@pin` text exactly in every mode.
- The default compile call remains compatible with existing callers by using `lossless`, no target budget, and active compile mode.
