# Roadmap

## Sprint 1: Security Hygiene And Trust Basics

### Goals

- Remove immediate security hygiene issues.
- Make privacy behavior clear.
- Stabilize verification commands.

### Tasks

- Rotate and purge the previously tracked secret if the repository was shared.
- Keep `config/secret_key`, `config/logs/`, and `*.log` ignored.
- Change default public-bind examples to localhost-only or add explicit warnings.
- Add a browser history retention toggle.
- Make zero-retention mode clear browser history and skip local prompt persistence.
- Add `npm run check` or equivalent full verification command.
- Add Python vulnerability scanning setup.

### Success Metrics

- No tracked secrets or logs.
- Full verification command passes.
- Zero-retention tests prove no raw prompt persistence in browser history, traces, sessions, or cache.
- Users can see and control local history retention.

## Sprint 2: Quality Gates, Architecture, And Performance

### Goals

- Reduce technical debt.
- Add automated code quality gates.
- Improve large-prompt performance confidence.

### Tasks

- Add ESLint and frontend accessibility linting.
- Add Python linting with Ruff or equivalent.
- Add Python type checking for critical modules.
- Consolidate duplicate storage responsibilities.
- Split oversized API/compiler orchestration files.
- Add bundle-size tracking.
- Add large-prompt performance tests.
- Disable public production source maps or split local/prod build modes.

### Success Metrics

- CI or local check catches lint, test, build, and dependency failures.
- Storage behavior has one authoritative implementation.
- Large prompt compile latency has a documented baseline.
- Production build artifacts are smaller and less revealing.

## Sprint 3: Product Clarity And Semantic Compression

### Goals

- Make optimization behavior understandable.
- Improve perceived and actual savings.
- Preserve user trust while adding smarter compression.

### Tasks

- Add a "Why did this change?" explanation panel.
- Add before/after diff categories for redundancy removal, wording normalization, semantic grouping, and unchanged protected content.
- Add semantic compression confidence labels.
- Add mode presets: simple, balanced, aggressive, and audit-safe.
- Add examples showing why re-pasted optimized prompts can tokenize differently.
- Improve empty states and onboarding around token accounting.

### Success Metrics

- Users can explain why output changed or did not change.
- Support confusion around token counts drops.
- Semantic compression never runs without confidence/meaning-risk feedback.
- Workbench feels simpler on first use.

## Sprint 4: Scale, Reliability, And Polish

### Goals

- Prepare for wider use.
- Improve reliability and operational visibility.
- Polish the product experience.

### Tasks

- Add auth/rate limiting if any network exposure is planned.
- Add request size limits.
- Add cache/session pruning controls.
- Add deployment documentation for local, preview, and future production modes.
- Add browser-based mobile and accessibility regression tests.
- Add exportable optimization reports.
- Add SDK/API examples as executable tests.

### Success Metrics

- Safe default deployment story is documented.
- API cannot be accidentally exposed without warnings or protection.
- Mobile and accessibility checks pass.
- Optimization reports are clear enough to share with stakeholders.
