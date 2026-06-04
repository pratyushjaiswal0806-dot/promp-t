# UX Review

## Overall UX Assessment

The product has a strong workbench concept and useful trust/clarity feedback, but the interface still feels dense. The core user journey is understandable after exploration, yet new users may not immediately know which controls matter, why an optimization changed or did not change text, and whether privacy settings cover local browser history.

## Navigation

### Strengths

- Main site navigation is straightforward.
- Workbench keeps input, output, controls, and analytics close together.
- Drawer/tab patterns help hide secondary information.

### Friction Points

- The workbench can feel crowded because many advanced concepts are visible near the primary prompt flow.
- Some secondary tabs compete with the main input/output comparison.
- It is not always obvious which mode is best for a new user.

### Recommendations

- Default to a simple mode with only input, optimize, output, savings, and trust summary.
- Move policy details, export, history, and diagnostics into progressive disclosure.
- Add "Beginner", "Balanced", and "Advanced" workbench modes.

## Responsiveness And Mobile

### Strengths

- The React UI is responsive and uses modern layout patterns.
- Output panel scrollability has improved in the current iteration.

### Friction Points

- Dense analytics and policy panels can still dominate smaller screens.
- Long optimized prompts need very predictable scrolling and copy affordances.

### Recommendations

- Keep output sticky or prioritized on mobile after compile.
- Collapse analytics by default on small screens.
- Add a clear "copy optimized prompt" affordance near the output header.

## Accessibility

### Strengths

- The product uses semantic UI patterns in many areas.
- Contrast and hierarchy are generally intentional.

### Gaps

- No automated accessibility suite was found.
- Advanced controls may need stronger keyboard/focus validation.
- Motion should respect reduced-motion preferences everywhere.

### Recommendations

- Add axe-based accessibility checks.
- Add keyboard-only browser tests for the workbench.
- Audit focus states for drawer, tabs, dialogs, and copy/export actions.

## Error Handling

### Strengths

- The UI has API wrappers and error boundaries.
- Provider/NIM flows include explicit user confirmation.

### Friction Points

- FastAPI errors can contain structured `detail`, while the frontend may surface a generic request failure.
- Errors should explain whether the issue is local server, provider key, invalid prompt, or unsupported provider mode.

### Recommendations

- Normalize API errors in `src/services/api.js`.
- Add error categories and short recovery instructions.
- Make unsupported live-provider proxy behavior explicit in the UI.

## Loading States

### Strengths

- Compile and generation actions have state handling.

### Gaps

- Long prompts and provider calls need better progress expectations.
- Users should know when deterministic optimization is happening locally versus when an external provider is involved.

### Recommendations

- Add "local deterministic" and "external provider" badges.
- Add skeleton or step indicators for analyze, compress, verify, and report generation phases.

## Empty States

### Strengths

- Sample prompts and copy help users start.

### Gaps

- Empty history and analytics states could better teach the product.

### Recommendations

- Use empty states to explain token savings, semantic compression, and trust scoring.
- Add one guided sample that demonstrates why optimized output may look similar but count differently.

## User Onboarding

### Friction Points

- Users may not understand how optimization happens or why token counts can differ after re-pasting optimized prompts.
- The distinction between deterministic compression, semantic compression, and LLM generation needs clearer product language.

### Recommendations

- Add a compact "How optimization works" explainer inside the workbench.
- Add before/after diff markers for removed redundancy, normalized phrasing, and preserved meaning.
- Add a "Why did this change?" panel for each compile result.

## Highest-Impact UX Fixes

1. Add a simple default mode and hide advanced controls until requested.
2. Add stronger explanation for token accounting and semantic compression behavior.
3. Add local privacy controls for browser history.
4. Improve API error messages and recovery guidance.
5. Add mobile-first workbench verification.
