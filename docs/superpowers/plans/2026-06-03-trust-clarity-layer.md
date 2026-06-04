# Trust Clarity Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PromptCompiler visibly trustworthy by explaining token accounting, prompt type, optimization confidence, unchanged outputs, and when users should use distillation instead of safe compression.

**Architecture:** Add a backend token-accounting contract that uses the same segmented estimate for original input and optimized output, then expose accounting metadata through compiler and `/v1` responses. Keep UX explanation logic in focused frontend helpers so the workbench can display trust badges, prompt-type recommendations, pasted-back estimates, and concise what-changed/what-skipped explanations without changing the deterministic compiler pipeline.

**Tech Stack:** Python 3.11 `unittest`, deterministic compiler modules under `promptcompiler/`, React 19/Vite frontend under `src/`, Node `node:test`, static browser E2E, built assets under `web/`.

---

## File Structure

- Modify `promptcompiler/compiler.py`: add segmented token-accounting metadata, make optimized token counts use the same prompt-segment method as original counts, and include pasted-back/reuse estimates.
- Modify `promptcompiler/v1.py`: expose `token_accounting` and trust-facing token metadata in `/v1/compile` responses.
- Modify `src/services/report.js`: add trust-profile helpers for token accounting, prompt type, optimization confidence, compression-vs-distillation recommendation, and explanation rows.
- Modify `src/workbench/context/CompilerContext.jsx`: pass the original prompt into report building and expose trust metadata in report state and metric rows.
- Modify `src/workbench/OutputPanel.jsx`: render trust badge, prompt recommendation, token accounting, and explanation rows above/below optimized output.
- Modify `src/workbench/AnalyticsPanel.jsx`: add a compact trust/accounting section in the Metrics drawer.
- Modify `src/styles/workbench.css`: style trust badges, token-accounting cards, prompt recommendation cards, and explanation rows.
- Modify `tests/test_compiler.py`: verify consistent token accounting and pasted-back optimized-token estimate.
- Modify `tests/test_v1_api.py`: verify `/v1/compile` exposes token-accounting metadata.
- Modify `tests/frontend_payload.test.mjs`: verify report helpers classify creative prompts, RAG prompts, unchanged outputs, and token-accounting explanations.
- Modify `tests/test_static_assets.py`: assert source contracts for trust UI selectors/classes.
- Modify `tests/web_e2e_runner.mjs`: browser-check trust badge, prompt recommendation, and token-accounting display after compile.
- Rebuild `web/` with `npm run build` after frontend changes.

---

### Task 1: Backend Token Accounting Contract

**Files:**
- Modify: `tests/test_compiler.py`
- Modify: `promptcompiler/compiler.py`

- [ ] **Step 1: Write failing compiler tests**

Add tests that compile a multi-section prompt and assert:

```python
def test_compile_uses_segmented_accounting_for_optimized_reuse_estimate(self):
    payload = "alpha beta gamma\n\nalpha beta gamma\n\nunique requirement"

    result = compile_prompt(payload, mode="balanced")

    accounting = result["token_accounting"]
    self.assertEqual(accounting["method"], "segmented_prompt_estimate")
    self.assertEqual(accounting["original_tokens"], result["original_tokens"])
    self.assertEqual(accounting["optimized_tokens"], result["optimized_tokens"])
    self.assertEqual(accounting["optimized_reuse_tokens"], result["optimized_tokens"])
    self.assertGreater(accounting["segment_overhead_tokens"], 0)
    self.assertLess(result["optimized_tokens"], result["original_tokens"])
```

- [ ] **Step 2: Run the failing compiler test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_compiler.CompilerTests.test_compile_uses_segmented_accounting_for_optimized_reuse_estimate
```

Expected: FAIL because `token_accounting` is not implemented.

- [ ] **Step 3: Implement segmented token accounting**

In `promptcompiler/compiler.py`, add:

```python
def _segmented_token_count(text: str) -> int:
    return sum(segment.tokens for segment in parse_prompt(text))


def _token_accounting(
    raw_input: str,
    optimized_text: str,
    original_tokens: int,
    optimized_tokens: int,
) -> dict[str, Any]:
    original_segments = parse_prompt(raw_input)
    optimized_segments = parse_prompt(optimized_text)
    original_raw_tokens = estimate_text_tokens(raw_input)
    optimized_raw_tokens = estimate_text_tokens(optimized_text)
    optimized_reuse_tokens = sum(segment.tokens for segment in optimized_segments)
    return {
        "method": "segmented_prompt_estimate",
        "tokenizer": "estimated",
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "optimized_reuse_tokens": optimized_reuse_tokens,
        "original_raw_text_tokens": original_raw_tokens,
        "optimized_raw_text_tokens": optimized_raw_tokens,
        "original_segments": len(original_segments),
        "optimized_segments": len(optimized_segments),
        "segment_overhead_tokens": max(0, original_tokens - original_raw_tokens),
        "optimized_segment_overhead_tokens": max(0, optimized_reuse_tokens - optimized_raw_tokens),
        "note": "Counts use segmented prompt estimates so optimized output is measured the same way when reused as input.",
    }
```

Update `_token_metrics_for_output` so changed optimized text also uses `_segmented_token_count(optimized_text)`.

- [ ] **Step 4: Attach accounting to compile result**

After active output is selected in `compile_prompt`, add:

```python
token_accounting = _token_accounting(
    raw_input,
    active_optimized_text,
    original_tokens,
    active_optimized_tokens,
)
```

Add `"token_accounting": token_accounting` to the result dictionary.

- [ ] **Step 5: Run compiler tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_compiler
```

Expected: all compiler tests pass.

---

### Task 2: V1 API Trust Metadata

**Files:**
- Modify: `tests/test_v1_api.py`
- Modify: `promptcompiler/v1.py`

- [ ] **Step 1: Write failing V1 test**

Add assertions to `test_v1_compile_returns_optimized_messages_and_transformations`:

```python
self.assertIn("token_accounting", payload)
self.assertEqual(payload["token_accounting"]["method"], "segmented_prompt_estimate")
self.assertEqual(payload["token_accounting"]["original_tokens"], payload["original_token_count"])
self.assertEqual(payload["token_accounting"]["optimized_tokens"], payload["optimized_token_count"])
self.assertIn("optimized_reuse_tokens", payload["token_accounting"])
```

- [ ] **Step 2: Run failing V1 test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_v1_api.V1ApiTests.test_v1_compile_returns_optimized_messages_and_transformations
```

Expected: FAIL because the response does not expose `token_accounting`.

- [ ] **Step 3: Expose metadata**

In `/v1/compile` response construction, add:

```python
"token_accounting": result.get("token_accounting", {}),
```

- [ ] **Step 4: Run V1 tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_v1_api
```

Expected: all V1 tests pass.

---

### Task 3: Frontend Trust Profile Helpers

**Files:**
- Modify: `tests/frontend_payload.test.mjs`
- Modify: `src/services/report.js`

- [ ] **Step 1: Write failing frontend helper tests**

Add tests for:

```js
import { buildTrustProfile } from "../src/services/report.js";

test("buildTrustProfile recommends distillation for creative website prompts with low safe savings", () => {
  const profile = buildTrustProfile({
    inputValue: "Create a modern responsive portfolio website with hero, about, skills, projects, experience, testimonials, blog, and contact sections.",
    mode: "balanced",
    result: {
      original_token_count: 120,
      optimized_token_count: 118,
      token_accounting: {
        method: "segmented_prompt_estimate",
        original_tokens: 120,
        optimized_tokens: 118,
        optimized_reuse_tokens: 122,
        segment_overhead_tokens: 12,
      },
      compile: { tokens_saved: 2, semantic: { scorer: "lexical", summary: { rag_chunks: 0, removed_chunks: 0 } }, warnings: [] },
    },
  });

  assert.equal(profile.promptType, "Creative build prompt");
  assert.equal(profile.bestOptimization, "Distill");
  assert.equal(profile.safeCompressionPotential, "low");
  assert.match(profile.accounting.note, /segmented/i);
});
```

Also add RAG and duplicate-removal confidence tests.

- [ ] **Step 2: Run failing frontend tests**

Run:

```bash
npm run test:frontend
```

Expected: FAIL because `buildTrustProfile` is missing.

- [ ] **Step 3: Implement helpers**

In `src/services/report.js`, export:

```js
export function buildTrustProfile({ inputValue = "", mode = "balanced", result = {} } = {}) {
  const compile = result.compile || result || {};
  const accounting = result.token_accounting || compile.token_accounting || {};
  const promptType = classifyPromptType(inputValue, compile);
  const tokensSaved = Number(compile.tokens_saved ?? Math.max(0, Number(result.original_token_count || 0) - Number(result.optimized_token_count || 0)));
  const warnings = compile.warnings || result.warnings || [];
  const semantic = result.semantic || compile.semantic || {};
  const removedChunks = Number(semantic.summary?.removed_chunks ?? semantic.removed_chunk_ids?.length ?? 0);
  const safeCompressionPotential = compressionPotential(promptType, tokensSaved, removedChunks, inputValue);
  const bestOptimization = promptType === "Creative build prompt" && safeCompressionPotential === "low" ? "Distill" : "Compress";
  return {
    promptType,
    safeCompressionPotential,
    bestOptimization,
    confidence: trustConfidence({ tokensSaved, warnings, removedChunks, promptType }),
    accounting: accountingProfile(accounting),
    explanationRows: explanationRows({ promptType, tokensSaved, warnings, removedChunks, semantic, bestOptimization }),
  };
}
```

Implement small local helper functions for prompt classification, potential, confidence, accounting text, and rows.

- [ ] **Step 4: Run frontend tests**

Run:

```bash
npm run test:frontend
```

Expected: all frontend tests pass.

---

### Task 4: Workbench Trust UI

**Files:**
- Modify: `src/workbench/context/CompilerContext.jsx`
- Modify: `src/workbench/OutputPanel.jsx`
- Modify: `src/workbench/AnalyticsPanel.jsx`
- Modify: `src/styles/workbench.css`
- Modify: `tests/test_static_assets.py`

- [ ] **Step 1: Write failing static tests**

Assert source includes:

```python
for selector in (
    "trustBadge",
    "promptRecommendation",
    "tokenAccountingPanel",
    "trustExplanationRows",
):
    self.assertIn(f'id="{selector}"', source)
```

Assert CSS includes:

```python
self.assertIn(".trust-badge", css)
self.assertIn(".token-accounting-panel", css)
self.assertIn(".prompt-recommendation-card", css)
```

- [ ] **Step 2: Run failing static tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets.StaticAssetTests.test_workbench_exposes_trust_clarity_selectors
```

Expected: FAIL because selectors/classes are missing.

- [ ] **Step 3: Thread trust profile into report**

In `CompilerContext.jsx`, import `buildTrustProfile`, pass `prompt` to `_buildReport`, and include:

```js
const trustProfile = buildTrustProfile({ inputValue: prompt, mode, result });
```

Return `trustProfile` in the report and add summary rows:

```js
["Prompt type", trustProfile.promptType],
["Trust", trustProfile.confidence.label],
["Best mode", trustProfile.bestOptimization],
```

- [ ] **Step 4: Render trust UI**

In `OutputPanel.jsx`, render:

```jsx
<TrustBadge profile={report?.trustProfile} />
<PromptRecommendation profile={report?.trustProfile} />
<TokenAccountingPanel accounting={report?.trustProfile?.accounting} />
<TrustExplanationRows rows={report?.trustProfile?.explanationRows} />
```

- [ ] **Step 5: Add AnalyticsPanel trust summary**

Read `report` from context and show a compact `trustMetrics` block with prompt type, best optimization, confidence, counting method, and pasted-back estimate.

- [ ] **Step 6: Style trust UI**

Add CSS for `.trust-badge`, `.prompt-recommendation-card`, `.token-accounting-panel`, and `.trust-explanation-rows`.

- [ ] **Step 7: Run static and frontend tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets
npm run test:frontend
```

Expected: all tests pass.

---

### Task 5: Browser E2E Trust Verification

**Files:**
- Modify: `tests/web_e2e_runner.mjs`
- Modify: `tests/test_web_e2e.py` only if command wiring is needed.

- [ ] **Step 1: Add browser assertions**

After the long creative prompt compile, assert:

```js
const trust = await evalExpr(cdp, `JSON.stringify({
  badge: document.querySelector('#trustBadge')?.innerText || '',
  recommendation: document.querySelector('#promptRecommendation')?.innerText || '',
  accounting: document.querySelector('#tokenAccountingPanel')?.innerText || '',
  rows: document.querySelector('#trustExplanationRows')?.innerText || ''
})`);
```

Require text containing:

- `Creative build prompt`
- `Distill`
- `segmented`
- `No safe compression` or `low`

- [ ] **Step 2: Run E2E test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_web_e2e.WebE2ETests.test_browser_ui_flow_and_responsive_contract
```

Expected: pass.

---

### Task 6: Build And Full Verification

**Files:**
- Modify generated `web/` assets through `npm run build`.

- [ ] **Step 1: Build static web assets**

Run:

```bash
npm run build
```

Expected: Vite build succeeds and `web/` assets update.

- [ ] **Step 2: Run full suite**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover tests
npm run test:frontend
git diff --check
```

Expected: all tests pass and whitespace check is clean.

- [ ] **Step 3: Browser pass**

Open the local workbench and verify:

- trust badge appears after compile
- prompt type/recommendation appears
- token accounting panel shows segmented method and pasted-back estimate
- output scroll still works
- browser console has no app errors

---

## Self-Review

- Spec coverage: token consistency, pasted-back estimate, prompt type detection, compression-vs-distillation recommendation, explanation cards, trust badge, UI metrics, E2E verification, and rebuilt assets are covered.
- Placeholder scan: no `TBD`, `TODO`, or unspecified test steps remain.
- Type consistency: frontend uses `trustProfile`, `accounting`, `confidence`, `promptType`, `bestOptimization`, `safeCompressionPotential`, and `explanationRows` consistently across helper, context, and components.
