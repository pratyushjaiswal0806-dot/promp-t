# Testing Gaps

## Existing Coverage

The project has meaningful test coverage for an early-stage local product:

- Python `unittest` coverage for compiler behavior, policies, CLI behavior, v1 API behavior, server static assets, and related modules.
- Frontend Node tests for payload/report behavior.
- Browser runner script for local web flow verification.
- Static asset fallback tests for SPA routes.

Prior verification showed:

- Python suite: 160 tests when run through `python3 -m unittest discover tests`.
- Frontend suite: 15 tests through `npm run test:frontend`.

## Known Test Behavior

Running Python static asset tests concurrently with `npm run build` can produce false failures because Vite temporarily mutates the `web/` directory. The targeted SPA fallback test passes when run after the build is complete.

Recommendation:

- Do not run frontend build and Python static asset tests concurrently against the same `web/` directory.
- Add a temporary build output directory for tests or isolate static fallback tests from mutable build artifacts.

## Missing Coverage

### Security

- No automated secret scan.
- No dependency vulnerability scan for Python requirements.
- No tests proving zero-retention prevents raw prompt persistence.
- No tests for browser localStorage privacy behavior.
- No auth/rate-limit tests because auth/rate limiting do not exist yet.
- No tests for unsafe external provider base URL warnings.

### Backend

- Limited stress tests for very large prompts.
- Limited tests for compile cache eviction and pruning.
- Limited tests for session growth and storage cleanup.
- Limited tests for malformed JSON and oversized request bodies.
- Limited tests for concurrent compile/session writes.

### Frontend

- No component tests for the workbench panels.
- No accessibility test suite.
- No keyboard-navigation regression tests.
- No mobile viewport tests.
- No tests for loading, empty, and error states across all panels.

### Integration

- No full CLI-to-server-to-frontend integration test.
- No test that validates generated static assets and API routes in one running server.
- No production-like deployment smoke test.
- No test that confirms the mock proxy behavior is clearly returned when live provider support is unavailable.

### Quality Gates

- No ESLint.
- No Python linting.
- No Python type checking.
- No frontend type checking.
- No bundle-size threshold.
- No CI configuration found.

## Recommended New Tests

### Critical

- Secret scan test or CI step that fails on committed keys.
- Zero-retention persistence test covering traces, sessions, cache, and browser history.
- API request size limit tests once limits are added.

### High

- Workbench browser smoke test covering input, compile, output scroll, analytics, history, and export.
- Large prompt performance regression test.
- SQLite cache/session pruning tests.
- API error normalization tests so frontend users see useful errors.

### Medium

- Accessibility checks with axe or equivalent.
- Mobile viewport browser tests.
- Dependency audit CI job.
- Bundle-size check for Vite output.

### Nice To Have

- Snapshot tests for generated trust/clarity reports.
- SDK usage examples as executable tests.
- Contract tests for v1 API response shapes.
