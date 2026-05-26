# Phase 1 Dashboard MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the PRD/TRD-visible PromptCompiler website experience on the current Python/static-web foundation.

**Architecture:** Keep the existing standard-library Python server and static browser UI. Re-expose already implemented backend capabilities in the website, add small compatibility API improvements where needed, and keep all state local to the browser for Phase 1.

**Tech Stack:** Python 3.11+ standard library, `unittest`, static HTML/CSS/JavaScript, browser `localStorage`, existing NVIDIA NIM API client.

---

### Task 1: Add API Support Tests For Dashboard Data

**Files:**
- Modify: `tests/test_models_and_api.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Add a full export contract test**

Add this test to `tests/test_models_and_api.py`:

```python
def test_export_endpoint_returns_compile_report_for_dashboard_json_export(self):
    status, body = handle_api_request(
        "POST",
        "/api/export",
        json.dumps({"input": "@pin Keep CASE-123.\n\nrepeat\n\nrepeat"}).encode("utf-8"),
    )

    payload = json.loads(body)
    self.assertEqual(status, 200)
    self.assertEqual(payload["optimized_text"], "@pin Keep CASE-123.\n\nrepeat")
    self.assertIn("compile", payload)
    self.assertIn("diff", payload["compile"])
    self.assertIn("preservation", payload["compile"])
```

- [ ] **Step 2: Add an analyze endpoint dashboard-shape test**

Add this test to `tests/test_server.py`:

```python
def test_analyze_endpoint_returns_dashboard_fields(self):
    body = json.dumps(
        {
            "input": (
                '{"messages":['
                '{"role":"system","content":"@pin Follow CASE-123."},'
                '{"role":"user","content":"Summarize this support ticket."}'
                "]}"
            )
        }
    ).encode("utf-8")

    status, response = handle_api_request("POST", "/api/analyze", body)

    payload = json.loads(response)
    self.assertEqual(status, 200)
    self.assertEqual(payload["segment_count"], 2)
    self.assertIn("segments", payload)
    self.assertIn("by_type", payload)
    self.assertIn("by_role", payload)
    self.assertIn("protected_entities", payload)
    self.assertIn("compression_opportunity", payload)
```

- [ ] **Step 3: Run the focused API tests**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_models_and_api.py tests/test_server.py`

Expected: pass if existing endpoints already provide enough data; fail only if a route contract regressed.

### Task 2: Add Browser E2E Coverage For The PRD/TRD Workbench

**Files:**
- Modify: `tests/web_e2e_runner.mjs`
- Modify: `tests/test_web_e2e.py`

- [ ] **Step 1: Update the E2E runner to verify advanced controls**

In `tests/web_e2e_runner.mjs`, make the browser flow assert these selectors exist:

```javascript
const requiredSelectors = [
  "#promptInput",
  "#analyzeButton",
  "#compileButton",
  "#modelSelect",
  "#sampleSelect",
  "#importInput",
  "#exportTextButton",
  "#exportJsonButton",
  "#historyList",
  "#segmentsTable",
  "#diffList",
  "#nimButton",
];

for (const selector of requiredSelectors) {
  const exists = await page.$(selector);
  if (!exists) {
    throw new Error(`Missing required dashboard selector: ${selector}`);
  }
}
```

Then add flow checks:

```javascript
await page.selectOption("#sampleSelect", { index: 1 });
await page.click("#loadSampleButton");
await page.click("#analyzeButton");
await page.waitForSelector("#segmentsTable tbody tr");
await page.click("#compileButton");
await page.waitForFunction(() => {
  const output = document.querySelector("#optimizedOutput");
  return output && output.textContent && !output.textContent.includes("No optimized prompt yet");
});

const historyCount = await page.$$eval("#historyList button", (items) => items.length);
if (historyCount < 1) {
  throw new Error("Expected compile history to contain at least one item");
}
```

- [ ] **Step 2: Keep the responsive overflow assertion**

Keep or add this check in the mobile viewport section:

```javascript
const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
if (horizontalOverflow) {
  throw new Error("Mobile layout has horizontal overflow");
}
```

- [ ] **Step 3: Run the E2E test and confirm it fails before UI work**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_web_e2e.py`

Expected before implementation: fail with missing selectors such as `#analyzeButton` or `#modelSelect`.

### Task 3: Rebuild The Dashboard HTML Surface

**Files:**
- Modify: `web/index.html`

- [ ] **Step 1: Replace the simplified page with a dashboard layout**

Implement these stable element IDs in `web/index.html`:

```html
<select id="modelSelect" aria-label="Model"></select>
<input id="modelSearch" type="search" placeholder="Search models" aria-label="Search models" />
<select id="sampleSelect" aria-label="Sample prompt"></select>
<button id="loadSampleButton" type="button">Load Sample</button>
<input id="importInput" type="file" accept=".txt,.json,.md" aria-label="Import prompt file" />
<button id="analyzeButton" type="button">Analyze</button>
<button id="compileButton" class="primary" type="button">Compile &amp; Optimize</button>
<button id="nimButton" type="button">NIM Summarize</button>
<button id="copyButton" type="button" disabled>Copy</button>
<button id="exportTextButton" type="button" disabled>Export Text</button>
<button id="exportJsonButton" type="button" disabled>Export JSON</button>
<textarea id="promptInput" spellcheck="false" aria-label="Prompt to compile"></textarea>
<pre id="optimizedOutput" aria-live="polite">No optimized prompt yet.</pre>
<div id="metrics" class="metric-grid"></div>
<div id="breakdown" class="stack-list"></div>
<div id="entities" class="stack-list"></div>
<div id="changes" class="stack-list"></div>
<table id="segmentsTable"><tbody></tbody></table>
<div id="diffList"></div>
<div id="historyList"></div>
<div id="errorBox" hidden></div>
```

- [ ] **Step 2: Organize the page into PRD/TRD dashboard sections**

Use section IDs:

```html
<section id="controlPanel"></section>
<section id="inputPanel"></section>
<section id="outputPanel"></section>
<section id="analyticsPanel"></section>
<section id="inspectorPanel"></section>
<section id="historyPanel"></section>
```

- [ ] **Step 3: Run static asset tests**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_static_assets.py`

Expected: pass.

### Task 4: Implement Dashboard State And API Calls

**Files:**
- Modify: `web/app.js`

- [ ] **Step 1: Add state variables**

Use this state shape:

```javascript
let lastAnalyze = null;
let lastCompile = null;
let models = [];
let samples = [];
let selectedModel = "nvidia/llama-3.1-nemotron-nano-8b-v1";
const HISTORY_KEY = "promptcompiler.history.v1";
```

- [ ] **Step 2: Boot health, models, samples, and empty state**

Implement `boot()` so it:

```javascript
async function boot() {
  renderEmptyState();
  try {
    const [health, modelPayload, samplePayload] = await Promise.all([
      fetchJson("/api/health"),
      fetchJson("/api/models"),
      fetchJson("/api/samples"),
    ]);
    models = modelPayload.models || [];
    samples = samplePayload.samples || [];
    selectedModel = modelPayload.default_model || health.default_model || selectedModel;
    renderModels(models);
    renderSamples(samples);
    renderHistory();
    appStatus.textContent = health.nim_configured ? "Ready + NIM" : "Ready";
    appStatus.className = "status-chip ready";
  } catch (error) {
    appStatus.textContent = "Server unavailable";
    appStatus.className = "status-chip missing";
  }
}
```

- [ ] **Step 3: Add Analyze action**

Implement:

```javascript
async function analyzePrompt() {
  const prompt = input.value.trim();
  if (!prompt) {
    showError("Paste a prompt before analyzing.");
    input.focus();
    return;
  }
  await runAction(analyzeButton, async () => {
    const result = await postJson("/api/analyze", { input: input.value, model: selectedModel });
    lastAnalyze = result;
    renderAnalyze(result);
    clearError();
  });
}
```

- [ ] **Step 4: Add Compile action**

Implement compile so it posts to `/api/compile`, renders output, enables exports, and saves local history:

```javascript
async function compilePrompt() {
  const prompt = input.value.trim();
  if (!prompt) {
    showError("Paste a prompt before compiling.");
    input.focus();
    return;
  }
  await runAction(compileButton, async () => {
    const result = await postJson("/api/compile", { input: input.value, model: selectedModel });
    lastCompile = result;
    renderCompile(result);
    saveHistory(input.value, result);
    clearError();
  });
}
```

- [ ] **Step 5: Add JSON export**

Implement:

```javascript
async function exportJson() {
  if (!input.value.trim()) return;
  const payload = await postJson("/api/export", { input: input.value, model: selectedModel });
  download("promptcompiler-export.json", JSON.stringify(payload, null, 2), "application/json");
}
```

- [ ] **Step 6: Add NIM confirmation**

Implement:

```javascript
async function summarizeWithNim() {
  if (!input.value.trim()) {
    showError("Paste a prompt before using NIM summarization.");
    return;
  }
  const approved = window.confirm("This sends the current prompt text to NVIDIA NIM. Continue?");
  if (!approved) return;
  await runAction(nimButton, async () => {
    const result = await postJson("/api/nim/summarize", { text: input.value, model: selectedModel });
    optimizedOutput.textContent = result.summary || "";
    renderEntities(result.preservation?.checked_entities || []);
    clearError();
  });
}
```

- [ ] **Step 7: Wire all event listeners**

Register:

```javascript
analyzeButton.addEventListener("click", analyzePrompt);
compileButton.addEventListener("click", compilePrompt);
exportJsonButton.addEventListener("click", exportJson);
nimButton.addEventListener("click", summarizeWithNim);
modelSearch.addEventListener("input", () => renderModels(filterModels(modelSearch.value)));
modelSelect.addEventListener("change", () => { selectedModel = modelSelect.value || selectedModel; });
loadSampleButton.addEventListener("click", loadSelectedSample);
importInput.addEventListener("change", importPromptFile);
```

### Task 5: Implement Dashboard Rendering

**Files:**
- Modify: `web/app.js`

- [ ] **Step 1: Render analysis**

Implement `renderAnalyze(result)`:

```javascript
function renderAnalyze(result) {
  renderMetrics([
    ["Original", result.total_tokens],
    ["Segments", result.segment_count],
    ["Opportunity", `${Math.round((result.compression_opportunity || 0) * 100)}%`],
    ["Model", result.model || selectedModel],
  ]);
  renderBreakdown(result.by_type || {});
  renderEntities(result.protected_entities || []);
  renderSegments(result.segments || []);
}
```

- [ ] **Step 2: Render compile result**

Implement `renderCompile(result)`:

```javascript
function renderCompile(result) {
  optimizedOutput.textContent = result.optimized_text || "";
  copyButton.disabled = !result.optimized_text;
  exportTextButton.disabled = !result.optimized_text;
  exportJsonButton.disabled = !result.optimized_text;
  renderMetrics([
    ["Original", result.original_tokens],
    ["Optimized", result.optimized_tokens],
    ["Saved", result.tokens_saved],
    ["Savings", `${Math.round(result.savings_ratio * 100)}%`],
  ]);
  renderBreakdownFromDiff(result.diff || []);
  renderEntities(result.preservation?.checked_entities || []);
  renderChanges(result.changes || []);
  renderDiff(result.diff || []);
}
```

- [ ] **Step 3: Render segment table**

Implement:

```javascript
function renderSegments(segments) {
  const tbody = segmentsTable.querySelector("tbody");
  tbody.innerHTML = segments.length
    ? segments.map((segment) => `
      <tr>
        <td>${escapeHtml(segment.id)}</td>
        <td>${escapeHtml(segment.type)}</td>
        <td>${escapeHtml(segment.role)}</td>
        <td>${escapeHtml(String(segment.tokens))}</td>
        <td>${segment.pinned ? "Pinned" : "Open"}</td>
        <td>${escapeHtml((segment.entities || []).join(", "))}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="6">Analyze a prompt to inspect segments.</td></tr>`;
}
```

- [ ] **Step 4: Render diff list**

Implement:

```javascript
function renderDiff(items) {
  diffList.innerHTML = items.length
    ? items.map((item) => `
      <div class="diff-item ${escapeHtml(item.status || "kept")}">
        <strong>${escapeHtml(item.segment_id || item.id || "segment")}</strong>
        <span>${escapeHtml(item.status || "kept")}</span>
        <p>${escapeHtml(item.reason || item.type || "No change reason provided.")}</p>
      </div>
    `).join("")
    : emptyRow("Compile a prompt to inspect the diff.");
}
```

### Task 6: Style The Dashboard Responsively

**Files:**
- Modify: `web/styles.css`

- [ ] **Step 1: Add dashboard grid styles**

Use a restrained operational dashboard style:

```css
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 16px;
  align-items: start;
}

.full-span {
  grid-column: 1 / -1;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
```

- [ ] **Step 2: Add table and diff styles**

Add:

```css
.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

th,
td {
  border-bottom: 1px solid var(--line);
  padding: 9px 8px;
  text-align: left;
  vertical-align: top;
}

.diff-item {
  border: 1px solid var(--line);
  border-radius: 7px;
  padding: 10px;
  background: #fff;
}

.diff-item.removed {
  border-color: rgba(180, 59, 68, 0.3);
  background: #fff5f5;
}
```

- [ ] **Step 3: Add mobile layout rules**

Add:

```css
@media (max-width: 820px) {
  .app-shell {
    padding: 14px;
  }

  .workspace,
  .toolbar-grid {
    grid-template-columns: 1fr;
  }

  .panel-heading,
  .button-row {
    flex-direction: column;
    align-items: stretch;
  }

  button,
  select,
  input {
    width: 100%;
  }
}
```

### Task 7: Verify Phase 1

**Files:**
- Modify only if verification reveals a bug in files already touched by this plan.

- [ ] **Step 1: Run focused frontend/API tests**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest tests/test_models_and_api.py tests/test_server.py tests/test_static_assets.py tests/test_web_e2e.py`

Expected: pass.

- [ ] **Step 2: Run full suite**

Run: `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests`

Expected: pass.

- [ ] **Step 3: Start the local server**

Run: `python3 -m promptcompiler.server`

Expected: server prints `PromptCompiler running at http://127.0.0.1:8765`.

- [ ] **Step 4: Browser smoke test**

Open `http://127.0.0.1:8765` and verify:

- Models load.
- Samples load.
- Analyze fills segment table.
- Compile fills optimized output, diff, changes, and history.
- Text export and JSON export produce files.
- Mobile viewport has no horizontal overflow.

### Self-Review Notes

- This plan intentionally keeps Phase 1 inside the existing Python/static architecture.
- FastAPI, Next.js, Redis, Supabase/PostgreSQL, ClickHouse, SDK, proxy, RBAC, and quotas are deferred to later phases in the roadmap.
- Phase 1 exposes currently hidden backend features and adds browser-local workflow state without adding persistent server storage.
