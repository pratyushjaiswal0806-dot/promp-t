# Premium Multipage Frontend Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the React/Vite PromptCompiler site into a premium, informative multipage product experience while preserving the current working compile flow.

**Architecture:** Keep the Python server as the API/static host and keep Vite building into `web/`. Build a React component system under `src/`, add a lightweight client-side page model, and split the experience into product education pages plus a focused workbench page. Keep API calls relative (`/api/*`, `/v1/*`) so Python serving, Vite dev proxy, and browser E2E tests continue to work.

**Tech Stack:** React 19, Vite 7, vanilla CSS modules-by-convention in `src/styles.css`, Python `http.server` backend, unittest + headless Chrome CDP E2E.

---

## Target Experience

The site should feel like a premium product microsite and a serious local workbench, not a generic dashboard. It should have:

- A cinematic home page that explains the product in the first screen.
- Multiple React-rendered pages/sections: `Home`, `Workbench`, `How It Works`, `Platform`, `Security`, `Use Cases`, and `Docs`.
- A visible product story: parse raw context, protect pinned/critical values, compile against a policy, measure savings, and inspect traces.
- A preserved workbench: one main input, optimized output before analytics, compile modes, sample loading, model selection, lint/analyze/compile, inspector, semantic signals, history.
- Premium design language: editorial scale, real spatial hierarchy, dark/light contrast, precise motion, canvas/data visuals, dense but scannable controls.
- Mobile-first polish: no horizontal overflow, clear CTAs, readable workbench controls, and screenshots that show content rather than cropped text.

## File Structure

- Modify: `src/App.jsx`
  - Keep it as the route/page orchestrator only. Move large page and workbench sections out of this file.
- Create: `src/data/siteContent.js`
  - Structured content for navigation, pages, pipeline stages, proof cards, use cases, FAQs, metrics, and docs links.
- Create: `src/components/SiteShell.jsx`
  - Shared top navigation, mobile navigation, page chrome, status chip, and footer.
- Create: `src/components/HeroVisual.jsx`
  - Canvas signal map and animation lifecycle.
- Create: `src/components/Workbench.jsx`
  - Current prompt compile UI and all API-driven workbench state.
- Create: `src/components/AnalyticsPanels.jsx`
  - Metrics, breakdown, protected values, changes, lint, segments, diff, semantic signals, and history.
- Create: `src/pages/HomePage.jsx`
  - Premium landing/product story page.
- Create: `src/pages/WorkbenchPage.jsx`
  - Focused app surface containing the workbench.
- Create: `src/pages/HowItWorksPage.jsx`
  - Pipeline explanation with visual stages and examples.
- Create: `src/pages/PlatformPage.jsx`
  - API, SDK, proxy, sessions, metrics, trace, and local storage explanation.
- Create: `src/pages/SecurityPage.jsx`
  - Local-first, zero-retention, protected values, NIM boundary, and `.env` guidance.
- Create: `src/pages/UseCasesPage.jsx`
  - Agent logs, RAG pruning, support/RMA, prompt generation, model-routing examples.
- Create: `src/pages/DocsPage.jsx`
  - Practical command/API snippets and local setup.
- Modify: `src/styles.css`
  - Split into clearly labeled sections: reset, tokens, shell, pages, workbench, data panels, responsive.
- Modify: `tests/test_static_assets.py`
  - Assert the multipage source files exist and the content model defines all pages.
- Modify: `tests/web_e2e_runner.mjs`
  - Add route navigation checks and preserve compile-flow checks.

## Phase 1: Page Model And Shell

- [ ] **Step 1: Add source-level route tests**

Add a test in `tests/test_static_assets.py`:

```python
def test_premium_multipage_source_structure_exists(self):
    required = [
        ROOT / "src" / "data" / "siteContent.js",
        ROOT / "src" / "components" / "SiteShell.jsx",
        ROOT / "src" / "components" / "Workbench.jsx",
        ROOT / "src" / "pages" / "HomePage.jsx",
        ROOT / "src" / "pages" / "WorkbenchPage.jsx",
        ROOT / "src" / "pages" / "HowItWorksPage.jsx",
        ROOT / "src" / "pages" / "PlatformPage.jsx",
        ROOT / "src" / "pages" / "SecurityPage.jsx",
        ROOT / "src" / "pages" / "UseCasesPage.jsx",
        ROOT / "src" / "pages" / "DocsPage.jsx",
    ]
    self.assertTrue(all(path.exists() for path in required))
```

- [ ] **Step 2: Run the source test and verify RED**

Run:

```bash
python3 -m unittest tests.test_static_assets.StaticAssetTests.test_premium_multipage_source_structure_exists
```

Expected: FAIL because the page/component files do not exist yet.

- [ ] **Step 3: Add `src/data/siteContent.js`**

Create structured content:

```jsx
export const navItems = [
  { id: "home", label: "Home" },
  { id: "workbench", label: "Workbench" },
  { id: "how-it-works", label: "How It Works" },
  { id: "platform", label: "Platform" },
  { id: "security", label: "Security" },
  { id: "use-cases", label: "Use Cases" },
  { id: "docs", label: "Docs" },
];

export const pipelineStages = [
  { title: "Parse", body: "Segments raw context into roles, RAG chunks, tool output, pins, and repeated blocks." },
  { title: "Protect", body: "Preserves pinned instructions and protected values such as case IDs, URLs, and identifiers." },
  { title: "Compile", body: "Applies lossless, balanced, or aggressive policy-aware prompt transformations." },
  { title: "Measure", body: "Reports token savings, diffs, lint findings, semantic chunks, trace IDs, and cache hints." },
];
```

- [ ] **Step 4: Add `SiteShell.jsx`**

Create a shell that receives `activePage`, `setActivePage`, `appStatus`, and `children`. Render nav buttons, not full page reload links, so state is preserved.

- [ ] **Step 5: Update `App.jsx` to use `SiteShell`**

Keep active page in React state:

```jsx
const [activePage, setActivePage] = useState("home");
```

Render the selected page from a simple map. No `react-router` is needed for this phase.

- [ ] **Step 6: Run source tests**

Run:

```bash
python3 -m unittest tests.test_static_assets
```

Expected: PASS for source structure tests.

## Phase 2: Split The Workbench Without Changing Behavior

- [ ] **Step 1: Move canvas into `HeroVisual.jsx`**

Move the current `startSignalCanvas` logic into a component that owns its ref and cleanup. Keep `id="signalCanvas"` for E2E compatibility.

- [ ] **Step 2: Move workbench logic into `Workbench.jsx`**

Move state and functions for:

- input
- model search/select
- samples/import
- compile mode/policies
- lint/analyze/compile/NIM
- output/export/copy
- metrics and inspector state
- history

Keep these selectors stable:

```text
#promptInput
#compileButton
#analyzeButton
#sampleSelect
#loadSampleButton
#optimizedOutput
#metrics
#segmentsTable
#diffList
#semanticScores
#historyList
```

- [ ] **Step 3: Move analytics renderers into `AnalyticsPanels.jsx`**

Export reusable components: `MetricsGrid`, `StackList`, `EntityList`, `ChangeList`, `LintList`, `SegmentsTable`, `DiffList`, `SemanticList`, `HistoryList`.

- [ ] **Step 4: Run existing E2E**

Run:

```bash
npm run build
python3 -m unittest tests.test_web_e2e
```

Expected: PASS. This proves the split did not break product behavior.

## Phase 3: Build The Informative Pages

- [ ] **Step 1: Create `HomePage.jsx`**

Include:

- H1: “Compile long LLM context before it reaches the model.”
- Supporting copy explaining local-first prompt compression.
- CTAs: Workbench, How It Works.
- Hero visual using `HeroVisual`.
- Three proof metrics: modes, retention posture, visible pipeline.

- [ ] **Step 2: Create `HowItWorksPage.jsx`**

Include sections:

- “1. Parse messy context”
- “2. Protect critical values”
- “3. Compile with a policy”
- “4. Measure the run”
- Example before/after prompt cards.

- [ ] **Step 3: Create `PlatformPage.jsx`**

Explain:

- `/v1/analyze`
- `/v1/compile`
- `/v1/retrieve`
- `/v1/lint`
- `/v1/metrics`
- `/v1/requests/{trace_id}`
- Python SDK wrapper and mock OpenAI-compatible proxy.

- [ ] **Step 4: Create `SecurityPage.jsx`**

Explain:

- Local-first serving.
- `.env` behavior.
- NVIDIA NIM boundary.
- Protected values.
- Zero-retention trace wording.
- Difference between request traces and cache-enabled compile entries.

- [ ] **Step 5: Create `UseCasesPage.jsx`**

Use cards for:

- Coding-agent logs.
- RAG chunk pruning.
- Support/RMA chat context.
- Prompt generation for websites/apps.
- Context budget triage.

- [ ] **Step 6: Create `DocsPage.jsx`**

Add practical snippets:

```bash
python3 -m promptcompiler.server
npm run dev
npm run build
python3 -m unittest discover -s tests
```

Include small API examples for `/v1/compile` and `/v1/lint`.

- [ ] **Step 7: Add E2E navigation assertions**

In `tests/web_e2e_runner.mjs`, click or programmatically activate each page and assert unique text appears:

```js
for (const label of ["Platform", "Security", "Use Cases", "Docs"]) {
  // navigate and assert the page heading exists
}
```

## Phase 4: Premium Visual System

- [ ] **Step 1: Define page-level design tokens**

In `src/styles.css`, keep tokens explicit:

```css
:root {
  --bg: #f3f1ea;
  --surface: #fffdf6;
  --surface-dark: #10120f;
  --accent-lime: #c7f85a;
  --accent-coral: #ff6f4e;
  --accent-blue: #3f8cff;
}
```

- [ ] **Step 2: Add page transitions without routing risk**

Use CSS-only transitions on `.page-view`:

```css
.page-view {
  animation: page-enter 240ms ease both;
}

@keyframes page-enter {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

Respect reduced motion.

- [ ] **Step 3: Add premium content modules**

Create reusable classes/components:

- `EditorialHero`
- `SignalStrip`
- `ExplainerGrid`
- `CodePanel`
- `ComparisonPanel`
- `ProofCard`
- `UseCaseCard`
- `FAQAccordion`

- [ ] **Step 4: Mobile polish**

Verify at 390px:

- body scroll width equals viewport width.
- nav is usable.
- CTAs fit.
- workbench controls stack cleanly.
- tables scroll inside wrappers only.

## Phase 5: Verification And Release Gate

- [ ] **Step 1: Build**

Run:

```bash
npm run build
```

Expected: Vite build succeeds and writes hashed assets to `web/assets/`.

- [ ] **Step 2: Source/static tests**

Run:

```bash
python3 -m unittest tests.test_static_assets
```

Expected: PASS.

- [ ] **Step 3: Full test suite**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 4: Live browser E2E**

Start or reuse the server:

```bash
python3 -m promptcompiler.server
```

Run:

```bash
node tests/web_e2e_runner.mjs http://127.0.0.1:8765
```

Expected: PASS with no HTTP 400/500 static asset failures and no mobile overflow.

- [ ] **Step 5: Screenshot proof**

Capture:

- Desktop home page.
- Mobile home page.
- Workbench after compile.
- Platform/docs page.

Store in `artifacts/` with descriptive names.

## Acceptance Criteria

- React/Vite remains the only frontend stack.
- `npm run build` produces the Python-served `web/` output.
- The workbench still compiles sample prompts and preserves `CASE-123` in E2E.
- The optimized output remains visually before analytics.
- The product has at least seven informative page views.
- Every page explains a real product capability, not generic marketing copy.
- No horizontal overflow at 390px.
- Full `python3 -m unittest discover -s tests` passes.
