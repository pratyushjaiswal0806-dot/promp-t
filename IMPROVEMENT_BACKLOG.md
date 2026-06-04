# Improvement Backlog

## Critical

### Rotate And Purge Previously Tracked Secret

Description: A tracked local secret existed before this audit.

Why it matters: If it was pushed or shared, the secret is compromised even though it has now been removed from the current tree.

Estimated effort: 1 to 3 hours if local only; 0.5 to 1 day if Git history cleanup and remote coordination are required.

Expected impact: Removes the most serious security hygiene risk.

### Enforce Local-Only API Defaults

Description: Keep server defaults bound to `127.0.0.1` and warn on `0.0.0.0`.

Why it matters: The API has no auth or rate limiting.

Estimated effort: 0.5 to 1 day.

Expected impact: Prevents accidental network exposure.

### Align Privacy And Retention Behavior

Description: Make retention controls cover browser history, request traces, sessions, and compile cache.

Why it matters: Users may paste sensitive prompts and expect zero retention.

Estimated effort: 1 to 2 days.

Expected impact: Improves trust and reduces data exposure.

## High Impact

### Add Real Quality Gates

Description: Add ESLint, Python linting, and a single full verification command.

Why it matters: Current scripts do not provide enough automated guardrails.

Estimated effort: 1 day.

Expected impact: Reduces regressions and review overhead.

### Consolidate Storage Modules

Description: Reduce duplication between `storage.py` and `storage_v1.py`.

Why it matters: Duplicated persistence logic causes drift and privacy bugs.

Estimated effort: 2 to 4 days.

Expected impact: Cleaner architecture and safer retention behavior.

### Improve Token Accounting Explanation

Description: Add user-facing explanation for why optimized prompts may look similar while token counts differ.

Why it matters: Trust is a product feature for prompt optimization.

Estimated effort: 1 day.

Expected impact: Reduces confusion and support burden.

### Add Semantic Compression Confidence Controls

Description: Surface when semantic compression is deterministic, approximate, or meaning-risky.

Why it matters: Compression that changes meaning can damage user trust.

Estimated effort: 2 to 3 days.

Expected impact: Higher confidence in savings and better product differentiation.

## Medium Impact

### Disable Public Production Source Maps

Description: Keep source maps for local debugging but not public release builds.

Why it matters: Reduces artifact size and source exposure.

Estimated effort: 0.5 day.

Expected impact: Better production hygiene.

### Remove Unused Dependencies

Description: Remove `react-router-dom` if final search confirms it is unused.

Why it matters: Smaller dependency surface and cleaner package manifest.

Estimated effort: 0.5 day.

Expected impact: Cleaner build and dependency audit.

### Normalize API Error Responses In Frontend

Description: Improve parsing of FastAPI `detail` errors and provider errors.

Why it matters: Users need actionable recovery guidance.

Estimated effort: 0.5 to 1 day.

Expected impact: Better UX and lower frustration.

### Add Bundle And Performance Tracking

Description: Track Vite bundle size and long-prompt compile latency.

Why it matters: Prompt workloads can grow quickly.

Estimated effort: 1 day.

Expected impact: Prevents slow regressions.

## Nice To Have

### Add Architecture Decision Records

Description: Record decisions for local-first mode, provider integration, retention, and deterministic compression.

Why it matters: Helps future contributors understand tradeoffs.

Estimated effort: 0.5 day.

Expected impact: Better onboarding and maintainability.

### Add Guided Product Tour

Description: Build a short interactive walkthrough for first-time users.

Why it matters: The workbench has advanced controls that can overwhelm new users.

Estimated effort: 1 to 2 days.

Expected impact: Better activation.

### Add Exportable Audit Report

Description: Generate a user-facing optimization audit with savings, semantic risk, and changes made.

Why it matters: Makes optimization results easier to share and trust.

Estimated effort: 2 days.

Expected impact: Stronger product value.
