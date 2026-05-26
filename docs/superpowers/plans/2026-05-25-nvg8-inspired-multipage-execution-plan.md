# NVG8 Inspired Multipage Frontend Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a frontend-only, premium multipage PromptCompiler experience that explains the product clearly while preserving the existing compile workbench.

**Architecture:** Keep the existing React/Vite app and Python API surface. Add a structured content module that feeds page components, then render dark immersive pages with motion-led transitions, dense product cards, and a focused workbench route. Inspiration is https://nvg8.io/ for premium spatial hierarchy, dark contrast, and motion-led storytelling only; do not copy its content, code, layout, brand, imagery, or assets.

**Tech Stack:** React, Vite, vanilla CSS in `src/styles.css`, existing PromptCompiler HTTP APIs, existing frontend verification commands.

---

## File Ownership

- Create: `src/data/siteContent.js`
  - Owns concise, structured content for navigation, hero copy, value pillars, pipeline journey, platform sections, security sections, use cases, docs sections, motion stats, and page metadata.
- Modify later: `src/App.jsx`
  - Consume the content module and render page state. Do not change backend behavior.
- Modify later: `src/styles.css`
  - Add premium dark visual system, responsive layout, motion states, and workbench polish.
- Optional later: focused component/page files under `src/components/` and `src/pages/`
  - Split UI only if it keeps App.jsx readable.

## Phase 1: Content Model

- [x] **Step 1: Create `src/data/siteContent.js`**

Add named exports:

```js
navItems
homeHero
valuePillars
pipelineJourney
platformSections
securitySections
useCases
docsSections
motionStats
pageMeta
```

Content acceptance:

- Explains parse, protect, compile, measure.
- Mentions local-first defaults and zero-retention trace posture.
- Covers workbench controls, RAG/semantic pruning, cache/routing, API/SDK/proxy, and inspectable diffs/analytics.
- Uses plain ASCII and card-sized copy.
- Does not copy content or assets from nvg8.io.

- [ ] **Step 2: Verify module syntax**

Run:

```bash
node --input-type=module -e "import('./src/data/siteContent.js').then((m) => console.log(Object.keys(m).sort().join('\n')))"
```

Expected: exports include all required content keys.

## Phase 2: Multipage React Shell

- [ ] **Step 1: Add page state**

In `src/App.jsx`, keep the existing workbench behavior and add a page state such as:

```jsx
const [activePage, setActivePage] = useState("home");
```

Use `navItems` from `src/data/siteContent.js` to render navigation. Keep route changes client-side so compile state is not lost during page switches.

- [ ] **Step 2: Render core pages**

Add page views for:

- Home
- Workbench
- How It Works
- Platform
- Security
- Use Cases
- Docs

Acceptance:

- Each page uses `pageMeta`.
- Home uses `homeHero`, `valuePillars`, and `motionStats`.
- How It Works uses `pipelineJourney`.
- Platform uses `platformSections`.
- Security uses `securitySections`.
- Use Cases uses `useCases`.
- Docs uses `docsSections`.
- Workbench preserves existing compile, analyze, lint, sample, import, copy, export, history, metrics, segment, diff, and semantic panels.

## Phase 3: Premium Visual System

- [ ] **Step 1: Apply the dark immersive art direction**

Update `src/styles.css` with a premium but original visual system:

- Dark base with restrained contrast.
- Editorial headings without oversized dashboard text.
- Motion-led hover and page transition states.
- Depth from borders, subtle shadows, and animated lines instead of copied assets.
- Clear focus states and readable controls.

Acceptance:

- No nvg8.io assets, screenshots, SVGs, copy, or brand elements are used.
- UI remains product-specific to PromptCompiler.
- Text does not overflow on mobile or desktop.
- Workbench controls stay dense and usable.

- [ ] **Step 2: Keep workbench first-class**

Polish the existing app surface so the product still works as a tool:

- Input and optimized output remain prominent.
- Compile mode, model selection, sample loading, and run actions are visible.
- Diffs, analytics, semantic scores, and history are inspectable after a run.
- Empty states explain what panel will show without long marketing text.

## Phase 4: Verification

- [ ] **Step 1: Static build**

Run:

```bash
npm run build
```

Expected: Vite build completes.

- [ ] **Step 2: Existing test gate**

Run the repository frontend/static verification that is available in this checkout:

```bash
npm run verify
```

If that command is too broad for the current worker scope, run the existing focused frontend/static tests and record the exact command.

- [ ] **Step 3: Browser smoke**

Start the local app if needed, then verify:

- Home loads with the premium hero and no blank canvas area.
- Navigation reaches every page.
- Workbench can load a sample.
- Analyze and compile still return metrics.
- Diffs, semantic signals, and history render when returned by the API.
- Mobile width has no horizontal overflow.

## Final Acceptance Checks

- [ ] Required content exports exist in `src/data/siteContent.js`.
- [ ] The multipage frontend explains how PromptCompiler works: parse, protect, compile, measure.
- [ ] Local-first defaults, workbench controls, RAG/semantic pruning, cache/routing, API/SDK/proxy, and inspectable diffs/analytics are visible in page copy.
- [ ] The visual direction is dark, immersive, premium, and motion-led, inspired by nvg8.io without copying content or assets.
- [ ] Existing compile flow remains functional.
- [ ] Build and chosen verification commands pass, or failures are documented with exact output and owner.
