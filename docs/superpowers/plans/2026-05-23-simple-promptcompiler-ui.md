# Simple PromptCompiler UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the complex PromptCompiler workbench UI with a single paste-to-compile flow where optimized output appears before analytics.

**Architecture:** Keep the existing vanilla HTML/CSS/JS app and Python API. Simplify the DOM in `web/index.html`, simplify client state and event handling in `web/app.js`, and restyle the page in `web/styles.css` for a single-column task flow.

**Tech Stack:** Python `unittest`, vanilla JavaScript, HTML, CSS, existing Chrome DevTools Protocol E2E runner.

---

### Task 1: Browser Contract Test

**Files:**
- Modify: `tests/web_e2e_runner.mjs`
- Test: `tests/test_web_e2e.py`

- [ ] **Step 1: Write the failing test**

Update `tests/web_e2e_runner.mjs` so the boot assertions require the simple UI:

```js
const boot = JSON.parse(
  await evalExpr(
    cdp,
    `JSON.stringify((() => ({
      promptExists: Boolean(document.querySelector('#promptInput')),
      primaryText: document.querySelector('#compileButton')?.textContent || '',
      outputIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'outputPanel'),
      analyticsIndex: [...document.querySelectorAll('main section')].findIndex((section) => section.id === 'analyticsPanel'),
      hiddenAdvanced: ['#modelSearch', '#sampleSelect', '#importInput', '#nimButton', '#segmentsPanel', '#diffPanel', '#historyPanel'].every((selector) => !document.querySelector(selector))
    }))())`,
  ),
);
assert(boot.promptExists, "prompt input is missing");
assert(boot.primaryText.trim() === "Compile & Optimize", "primary action is not simplified");
assert(boot.outputIndex !== -1 && boot.analyticsIndex !== -1 && boot.outputIndex < boot.analyticsIndex, "output must appear before analytics");
assert(boot.hiddenAdvanced, "advanced controls are still visible in the main UI");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_web_e2e.WebE2ETests.test_browser_ui_flow_and_responsive_contract`

Expected: FAIL because the current UI still exposes workflow, model search, samples, NIM, segments, diff, and history.

### Task 2: Simplify Markup and Client Flow

**Files:**
- Modify: `web/index.html`
- Modify: `web/app.js`
- Test: `tests/test_web_e2e.py`

- [ ] **Step 1: Write minimal implementation**

Change `web/index.html` to keep only the header, one input section, one optimized output section, one analytics section, changes, and error display. Change `web/app.js` to bind only the remaining elements, use `/api/compile` for the primary action, render output before analytics, and use the default model internally.

- [ ] **Step 2: Run focused E2E**

Run: `python3 -m unittest tests.test_web_e2e.WebE2ETests.test_browser_ui_flow_and_responsive_contract`

Expected: PASS.

### Task 3: Simplify Styling and Verify Suite

**Files:**
- Modify: `web/styles.css`
- Test: `tests`

- [ ] **Step 1: Restyle the simplified layout**

Remove unused styles for advanced controls and use a single-column layout with stable responsive widths. Keep cards only for repeated metric/change items, not for nested page sections.

- [ ] **Step 2: Run full verification**

Run: `python3 -m unittest discover -s tests`

Expected: all tests pass.
