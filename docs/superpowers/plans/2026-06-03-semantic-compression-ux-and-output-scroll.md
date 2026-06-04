# Semantic Compression UX And Output Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make semantic compression understandable and easy to activate in the workbench, show users when no safe compression was found, and fix optimized-output scrolling for long prompts.

**Architecture:** Keep the compiler conservative by default and continue gating embedding-backed semantic compression behind explicit policy or automatic RAG/source detection. Implement UI-facing behavior in small frontend helpers (`src/services/payload.js`, `src/services/report.js`) and keep the existing backend semantic pipeline unchanged except for tests that prove current behavior. Fix scrollability in CSS by giving the optimized prompt its own constrained scroll region inside the output column.

**Tech Stack:** React 19, Vite, Node `node:test`, Python `unittest`, FastAPI/stdlib server test helpers, CSS modules under `src/styles/`, built static assets under `web/`.

---

## File Structure

- Modify `src/services/payload.js`: add an `autoSemantic` control, RAG/source detection helpers, and payload logic that sends `semantic_policy.scorer = "embedding"` when the user explicitly enables deterministic semantic scoring or when auto mode detects RAG/source blocks in `balanced`/`aggressive` modes.
- Modify `src/services/report.js`: add a semantic/no-change explanation helper so unchanged outputs say why they are unchanged instead of appearing broken.
- Modify `src/workbench/PolicyControls.jsx`: move semantic controls into visible core setup, add an auto semantic checkbox, and keep advanced tools focused on tool/session settings.
- Modify `src/workbench/context/CompilerContext.jsx`: thread the semantic/no-change explanation into the optimization report and expose summary rows that show semantic scorer and removed chunk count.
- Modify `src/workbench/OutputPanel.jsx`: render a short explanation panel when the optimized prompt is unchanged or semantic compression was available/active.
- Modify `src/styles/workbench.css`: make `#optimizedOutput` independently scrollable, preserve responsive behavior, and style the explanation panel.
- Modify `tests/frontend_payload.test.mjs`: add test-first coverage for auto semantic detection, explicit semantic override, no-change report messaging, and no false positives for ordinary prompts.
- Modify `tests/test_static_assets.py`: assert visible semantic controls and scroll CSS contracts exist in source.
- Modify `tests/web_e2e_runner.mjs`: verify the output prompt scroll container has real overflow after compiling a long prompt and verify semantic controls are visible without opening advanced groups.
- Build `web/` with `npm run build` after frontend changes.

---

### Task 1: Plan And Baseline Evidence

**Files:**
- Create: `docs/superpowers/plans/2026-06-03-semantic-compression-ux-and-output-scroll.md`
- No production code changes in this task.

- [ ] **Step 1: Save this plan**

Use `apply_patch` to add this file exactly at:

```text
docs/superpowers/plans/2026-06-03-semantic-compression-ux-and-output-scroll.md
```

- [ ] **Step 2: Confirm semantic compression currently works from Python**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_compiler.CompilerTests.test_embedding_semantic_policy_prunes_paraphrased_rag_that_lexical_keeps tests.test_v1_api.V1ApiTests.test_v1_compile_uses_embedding_semantic_policy_for_paraphrased_rag
```

Expected:

```text
Ran 2 tests
OK
```

- [ ] **Step 3: Confirm frontend tests currently pass before adding red tests**

Run:

```bash
npm run test:frontend
```

Expected: current frontend tests pass before new red tests are added.

---

### Task 2: Auto Semantic Payload Detection

**Files:**
- Modify: `tests/frontend_payload.test.mjs`
- Modify: `src/services/payload.js`

- [ ] **Step 1: Write failing frontend tests**

Append tests to `tests/frontend_payload.test.mjs`:

```js
test("buildCompilePayload auto-enables deterministic semantic scoring for RAG/source prompts", () => {
  const controls = {
    ...createDefaultControls(),
    autoSemantic: true,
    deterministicSemantic: false,
  };

  const payload = buildCompilePayload({
    inputValue: [
      "Question: Do refunds over 500 need manager approval?",
      "",
      "Source: doc-a",
      "Refunds over 500 require manager approval.",
      "",
      "Source: doc-b",
      "Reimbursements greater than 500 dollars need supervisor review.",
    ].join("\n"),
    selectedModel: "gpt-4o-mini",
    mode: "balanced",
    controls,
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "embedding",
    reason: "auto_rag_source_detected",
  });
});

test("buildCompilePayload keeps lexical semantic scoring for ordinary prompts in auto mode", () => {
  const payload = buildCompilePayload({
    inputValue: "Write a concise product brief for a local-first prompt compiler.",
    selectedModel: "gpt-4o-mini",
    mode: "balanced",
    controls: createDefaultControls(),
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "lexical",
  });
});

test("explicit deterministic semantic scoring overrides auto detection", () => {
  const controls = {
    ...createDefaultControls(),
    autoSemantic: false,
    deterministicSemantic: true,
  };

  const payload = buildCompilePayload({
    inputValue: "Write a concise product brief.",
    selectedModel: "gpt-4o-mini",
    mode: "lossless",
    controls,
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "embedding",
    reason: "explicit_user_enabled",
  });
});
```

- [ ] **Step 2: Run the red tests**

Run:

```bash
npm run test:frontend
```

Expected: FAIL because `autoSemantic` and semantic-policy reasons are not implemented yet.

- [ ] **Step 3: Implement minimal payload changes**

In `src/services/payload.js`, update defaults:

```js
export function createDefaultControls() {
  return {
    targetTokenBudget: "",
    dryRun: false,
    zeroRetention: true,
    cacheStaticPrefix: false,
    cacheEnabled: false,
    outputFormat: "plain",
    maxWords: "",
    explain: true,
    systemPromptRef: "",
    reuseExpectedCalls: "10",
    includeDecodePrompt: true,
    validationMode: "strict",
    retrievalTopK: "",
    toolCompact: false,
    maxTools: "",
    deterministicSemantic: false,
    autoSemantic: true,
    sessionId: "",
  };
}
```

Add helpers near the bottom:

```js
function semanticPolicyForInput(inputValue, mode, controls) {
  if (controls.deterministicSemantic) {
    return { provider: "deterministic", scorer: "embedding", reason: "explicit_user_enabled" };
  }
  if (controls.autoSemantic && supportsSemanticCompression(inputValue, mode)) {
    return { provider: "deterministic", scorer: "embedding", reason: "auto_rag_source_detected" };
  }
  return { provider: "deterministic", scorer: "lexical" };
}

function supportsSemanticCompression(inputValue, mode) {
  if (!["balanced", "aggressive"].includes(mode)) return false;
  const text = String(inputValue || "");
  return /(^|\n)\s*(source|citation|cite)\s*:/i.test(text);
}
```

Replace the existing `semantic_policy` expression in `buildCompilePayload` with:

```js
semantic_policy: semanticPolicyForInput(inputValue, mode, current),
```

- [ ] **Step 4: Run green frontend tests**

Run:

```bash
npm run test:frontend
```

Expected: PASS.

---

### Task 3: No-Change And Semantic Explanation Reporting

**Files:**
- Modify: `tests/frontend_payload.test.mjs`
- Modify: `src/services/report.js`
- Modify: `src/workbench/context/CompilerContext.jsx`
- Modify: `src/workbench/OutputPanel.jsx`

- [ ] **Step 1: Write failing report tests**

Add this import in `tests/frontend_payload.test.mjs`:

```js
import {
  deriveUsabilityVerdict,
  optimizationInsight,
  proposedPromptForDryRun,
} from "../src/services/report.js";
```

Add tests:

```js
test("optimizationInsight explains unchanged safe prompts", () => {
  const insight = optimizationInsight({
    original_token_count: 20,
    optimized_token_count: 20,
    compile: {
      original_tokens: 20,
      optimized_tokens: 20,
      tokens_saved: 0,
      semantic: { scorer: "lexical", summary: { rag_chunks: 0, removed_chunks: 0 } },
      plan: { actions: [] },
      warnings: [],
    },
  });

  assert.equal(insight.status, "unchanged");
  assert.match(insight.title, /no safe compression/i);
});

test("optimizationInsight explains semantic pruning when chunks are removed", () => {
  const insight = optimizationInsight({
    compile: {
      original_tokens: 48,
      optimized_tokens: 22,
      tokens_saved: 26,
      semantic: {
        scorer: "embedding",
        summary: { rag_chunks: 2, removed_chunks: 1 },
        removed_chunk_ids: ["seg_a_chunk_1"],
      },
      plan: { actions: [{ action: "rag_prune" }] },
      warnings: [],
    },
  });

  assert.equal(insight.status, "semantic");
  assert.match(insight.title, /semantic compression/i);
  assert.match(insight.body, /removed 1/i);
});
```

- [ ] **Step 2: Run red tests**

Run:

```bash
npm run test:frontend
```

Expected: FAIL because `optimizationInsight` does not exist yet.

- [ ] **Step 3: Implement report helper**

Add to `src/services/report.js`:

```js
export function optimizationInsight(result = {}) {
  const compile = result.compile || result || {};
  const original = Number(result.original_token_count ?? compile.original_tokens ?? 0);
  const optimized = Number(result.optimized_token_count ?? compile.optimized_tokens ?? 0);
  const tokensSaved = Number(compile.tokens_saved ?? Math.max(0, original - optimized));
  const semantic = result.semantic || compile.semantic || {};
  const semanticSummary = semantic.summary || {};
  const removedChunks = Number(semanticSummary.removed_chunks ?? semantic.removed_chunk_ids?.length ?? 0);
  const ragChunks = Number(semanticSummary.rag_chunks ?? 0);
  const scorer = semantic.scorer || "lexical";

  if (removedChunks > 0) {
    return {
      status: "semantic",
      title: "Semantic compression applied",
      body: `${scorer} scoring removed ${removedChunks} redundant RAG chunk${removedChunks === 1 ? "" : "s"} while preserving protected values.`,
    };
  }

  if (tokensSaved <= 0) {
    if (ragChunks > 0 && scorer !== "embedding") {
      return {
        status: "unchanged",
        title: "No safe compression found",
        body: "The compiler found RAG/source context, but lexical scoring did not identify a redundant chunk. Enable semantic scoring for paraphrase-aware pruning.",
      };
    }
    return {
      status: "unchanged",
      title: "No safe compression found",
      body: "This prompt did not contain duplicate blocks, budget pressure, compactable tool/log output, or redundant RAG chunks, so the safe output matches the input.",
    };
  }

  return null;
}
```

- [ ] **Step 4: Thread insight into report state**

In `src/workbench/context/CompilerContext.jsx`, import `optimizationInsight`:

```js
import { deriveUsabilityVerdict, optimizationInsight, proposedPromptForDryRun } from "../../services/report.js";
```

Inside `_buildReport`, add:

```js
const insight = optimizationInsight(result);
const semantic = result.semantic || compile.semantic || {};
const semanticSummary = semantic.summary || {};
```

Add to the returned object:

```js
insight,
```

Add summary rows before `Before cost`:

```js
["Semantic", semantic.scorer || "lexical"],
["RAG removed", semanticSummary.removed_chunks ?? 0],
```

- [ ] **Step 5: Render insight panel**

In `src/workbench/OutputPanel.jsx`, render the insight after the usability verdict:

```jsx
<OptimizationInsight insight={report?.insight} />
```

Add component:

```jsx
function OptimizationInsight({ insight }) {
  if (!insight) return null;
  return (
    <section id="optimizationInsight" className={`optimization-insight insight-${insight.status || "info"}`}>
      <strong>{insight.title}</strong>
      <span>{insight.body}</span>
    </section>
  );
}
```

- [ ] **Step 6: Run green tests**

Run:

```bash
npm run test:frontend
```

Expected: PASS.

---

### Task 4: Visible Semantic Controls

**Files:**
- Modify: `tests/test_static_assets.py`
- Modify: `src/workbench/PolicyControls.jsx`
- Modify: `src/styles/workbench.css`

- [ ] **Step 1: Add failing static test**

In `tests/test_static_assets.py`, add:

```python
    def test_semantic_controls_are_visible_in_core_setup(self):
        policy = (ROOT / "src" / "workbench" / "PolicyControls.jsx").read_text()
        css = (ROOT / "src" / "styles" / "workbench.css").read_text()

        self.assertIn('className="semantic-quick-controls"', policy)
        self.assertIn('id="autoSemanticInput"', policy)
        self.assertIn('id="deterministicSemanticInput"', policy)
        self.assertIn(".semantic-quick-controls", css)
```

- [ ] **Step 2: Run red static test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets.StaticAssetTests.test_semantic_controls_are_visible_in_core_setup
```

Expected: FAIL because controls are not visible in core setup.

- [ ] **Step 3: Move controls into core setup**

In `src/workbench/PolicyControls.jsx`, insert after `Mode` or `Target token budget`:

```jsx
<div className="semantic-quick-controls" aria-label="Semantic compression controls">
  <label style={checkboxLabelStyle}>
    <input
      id="autoSemanticInput"
      type="checkbox"
      checked={controls.autoSemantic}
      onChange={setBool("autoSemantic")}
    />
    Auto semantic for RAG
  </label>
  <label style={checkboxLabelStyle}>
    <input
      id="deterministicSemanticInput"
      type="checkbox"
      checked={controls.deterministicSemantic}
      onChange={setBool("deterministicSemantic")}
    />
    Force semantic scoring
  </label>
  <p>Auto mode enables local embedding scoring only when source/citation context is detected.</p>
</div>
```

Remove the old `deterministicSemanticInput` label from `Tools + trace` to avoid duplicate IDs.

- [ ] **Step 4: Add styling**

Add to `src/styles/workbench.css`:

```css
.semantic-quick-controls {
  display: grid;
  gap: 0.2rem;
  margin: 0.4rem 0 0.65rem;
  padding: 0.55rem;
  border: 1px solid color-mix(in srgb, var(--accent-lime) 28%, var(--line));
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--accent-lime) 7%, transparent);
}
.semantic-quick-controls p {
  margin: 0.1rem 0 0;
  color: var(--muted);
  font-size: 0.66rem;
  line-height: 1.35;
}
```

- [ ] **Step 5: Run green static test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets.StaticAssetTests.test_semantic_controls_are_visible_in_core_setup
```

Expected: PASS.

---

### Task 5: Output Prompt Scroll Fix

**Files:**
- Modify: `tests/test_static_assets.py`
- Modify: `src/styles/workbench.css`

- [ ] **Step 1: Add failing static scroll contract test**

In `tests/test_static_assets.py`, add:

```python
    def test_optimized_output_has_own_scroll_region(self):
        css = (ROOT / "src" / "styles" / "workbench.css").read_text()

        self.assertIn(".optimized-output-scroll", css)
        self.assertIn("overflow: auto", css)
        self.assertIn("overscroll-behavior: contain", css)
        self.assertIn("#optimizedOutput", (ROOT / "src" / "workbench" / "OutputPanel.jsx").read_text())
```

- [ ] **Step 2: Run red static test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets.StaticAssetTests.test_optimized_output_has_own_scroll_region
```

Expected: FAIL because the dedicated scroll class is missing.

- [ ] **Step 3: Wrap optimized output in scroll container**

In `src/workbench/OutputPanel.jsx`, replace:

```jsx
<pre id="optimizedOutput" className="optimized-output-text">{optimizedOutput}</pre>
```

with:

```jsx
<div className="optimized-output-scroll" aria-label="Scrollable optimized prompt">
  <pre id="optimizedOutput" className="optimized-output-text">{optimizedOutput}</pre>
</div>
```

- [ ] **Step 4: Implement CSS scroll region**

In `src/styles/workbench.css`, update output area and optimized output styles:

```css
.output-area {
  flex: 1;
  overflow: hidden;
  padding: 0;
  min-height: 0;
  background: var(--surface-dark);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.6;
  white-space: pre-wrap;
  display: flex;
  flex-direction: column;
}
.optimized-output-scroll {
  flex: 1 1 220px;
  min-height: 180px;
  overflow: auto;
  overscroll-behavior: contain;
  border-bottom: 1px solid var(--line);
}
.optimized-output-text {
  margin: 0;
  min-height: 100%;
  padding: 1rem;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-mono);
}
```

- [ ] **Step 5: Run green static test**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets.StaticAssetTests.test_optimized_output_has_own_scroll_region
```

Expected: PASS.

---

### Task 6: Browser E2E Verification

**Files:**
- Modify: `tests/web_e2e_runner.mjs`
- Build: `web/index.html`, `web/assets/*`

- [ ] **Step 1: Add E2E assertions**

In `tests/web_e2e_runner.mjs`, after loading the workbench and before/after compile flow, assert:

```js
const semanticControls = await evalExpr(cdp, `(() => ({
  autoVisible: !!document.querySelector('#autoSemanticInput'),
  forceVisible: !!document.querySelector('#deterministicSemanticInput'),
  scrollRegion: !!document.querySelector('.optimized-output-scroll')
}))()`);
assert(semanticControls.autoVisible, "auto semantic control is not visible");
assert(semanticControls.forceVisible, "force semantic control is not visible");
assert(semanticControls.scrollRegion, "optimized output scroll region missing");
```

After compiling a long prompt, assert:

```js
const scrollState = await evalExpr(cdp, `(() => {
  const el = document.querySelector('.optimized-output-scroll');
  return { scrollHeight: el?.scrollHeight || 0, clientHeight: el?.clientHeight || 0, overflowY: getComputedStyle(el).overflowY };
})()`);
assert(scrollState.scrollHeight > scrollState.clientHeight, "optimized output does not have vertical overflow");
assert(scrollState.overflowY === "auto", "optimized output scroll region should use overflow auto");
```

- [ ] **Step 2: Run E2E red or focused verification**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_web_e2e.WebE2ETests.test_browser_ui_flow_and_responsive_contract
```

Expected: PASS after implementation. If it fails before implementation, the failure should identify the missing controls/scroll region.

- [ ] **Step 3: Rebuild frontend**

Run:

```bash
npm run build
```

Expected: Vite build succeeds and updates `web/`.

---

### Task 7: Full Verification And Website Pass

**Files:**
- No new files beyond changed source, tests, and built assets.

- [ ] **Step 1: Run frontend tests**

Run:

```bash
npm run test:frontend
```

Expected: all frontend tests pass.

- [ ] **Step 2: Run static tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_static_assets
```

Expected: all static asset tests pass.

- [ ] **Step 3: Run compiler/API semantic regression tests**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests.test_compiler.CompilerTests.test_embedding_semantic_policy_prunes_paraphrased_rag_that_lexical_keeps tests.test_v1_api.V1ApiTests.test_v1_compile_uses_embedding_semantic_policy_for_paraphrased_rag
```

Expected: both semantic compression regressions pass.

- [ ] **Step 4: Run full Python test suite**

Run:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover tests
```

Expected: all tests pass.

- [ ] **Step 5: Run browser website pass**

Start or reuse a local server, open `/workbench`, verify:

```text
Semantic controls are visible in Core Setup.
Long optimized output scrolls independently.
Ordinary unchanged prompts show "No safe compression found".
RAG paraphrases with auto semantic enabled show semantic compression evidence.
No browser console errors appear.
```

- [ ] **Step 6: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

---

## Self-Review

- Spec coverage: The plan covers the requested implementation plan, output scroll bug, semantic-compression visibility, auto semantic activation, and no-change messaging.
- Placeholder scan: No task uses unresolved placeholders. Each code-facing task includes concrete snippets and commands.
- Type consistency: `autoSemantic`, `deterministicSemantic`, `semantic_policy`, `optimizationInsight`, `report.insight`, and CSS class names are consistent across tests, implementation, and E2E checks.
- Scope control: The plan intentionally does not change backend semantic pruning semantics. It makes existing semantic compression easier to trigger and understand while preserving the default conservative compiler path.
