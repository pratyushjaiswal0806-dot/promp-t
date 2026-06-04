# Security Audit

## Scope

This is a thorough in-session repository security audit. It is not a full multi-agent Codex Security ledger scan. The review covered source code, config files, dependency manifests, storage behavior, API exposure, frontend sinks, and environment handling.

## Findings

### Critical: Tracked Local Secret File

Severity: Critical

Evidence:

- `config/secret_key` existed as a tracked file before this audit.

Impact:

- If the repository was pushed or shared, the secret should be considered compromised.
- Removing it from the current tree does not remove it from Git history.

Fix:

- Implemented during this audit: deleted `config/secret_key` from the current tree.
- Implemented during this audit: added `config/secret_key` to `.gitignore`.
- Required follow-up: rotate the secret if it was ever used.
- Required follow-up: purge the secret from Git history if the repository is public or shared.

### High: Prompt And Output Data Stored In Browser localStorage

Severity: High

Evidence:

- `src/services/history.js` stores prompt/result history in localStorage.

Impact:

- Sensitive prompts can remain in the browser after a session.
- This can contradict zero-retention expectations if users assume local compile history is not persisted.
- Browser extensions, local users, or compromised profiles may read stored prompt data.

Fix:

- Add an explicit retention setting for local browser history.
- Default to session-only or off for sensitive modes.
- Show a visible privacy notice when local history is enabled.
- Clear local history automatically when zero-retention mode is active.

### High: No Authentication Or Rate Limiting On API Routes

Severity: High if exposed beyond localhost; Medium for strictly local use.

Evidence:

- No first-party auth flow was found.
- V1 and legacy API routes are callable without authentication.

Impact:

- If bound to a public or LAN-accessible interface, anyone who can reach the server can analyze prompts, compile prompts, query traces, append session content, and potentially exhaust local resources.

Fix:

- Keep default server binding to `127.0.0.1`.
- Add token-based local auth or signed session tokens before production exposure.
- Add request size limits and rate limiting.

### High: `0.0.0.0` Hypercorn Bind Conflicts With Local-Only Assumption

Severity: High when used on shared networks.

Evidence:

- `config/hypercorn.toml` binds to `0.0.0.0:9810`.

Impact:

- A local-only tool can become reachable from other machines if started with this config.

Fix:

- Change default bind examples to `127.0.0.1`.
- Add a comment requiring explicit opt-in for `0.0.0.0`.
- Add startup warnings when non-localhost binding is detected.

### Medium: NIM Base URL Override Can Redirect Provider Key

Severity: Medium

Evidence:

- `NVIDIA_NIM_BASE_URL` can override the provider base URL.

Impact:

- If environment variables are compromised or misconfigured, the API key can be sent to an unintended endpoint.

Fix:

- Add an allowlist or warning for non-NVIDIA hosts.
- Log only hostnames, never API keys.
- Require explicit unsafe-provider opt-in for arbitrary base URLs.

### Medium: Compile Cache And Session Storage May Persist Raw Content

Severity: Medium

Evidence:

- SQLite storage persists traces, sessions, turns, and compile cache responses.

Impact:

- Local databases may contain sensitive prompt data.
- Zero-retention behavior is not enough if browser history, session turns, or caches persist related data.

Fix:

- Define a single retention model covering traces, sessions, cache, and browser history.
- Add tests proving zero-retention does not store raw prompt content.
- Add pruning and clear-data controls.

### Medium: Production Source Maps Expose Source Structure

Severity: Medium for public deployments.

Evidence:

- Vite build generated large `.js.map` files under `web/assets`.

Impact:

- Public source maps reveal internal source structure and implementation details.
- They increase artifact size.

Fix:

- Disable source maps for production public builds.
- Keep source maps only for local/debug builds.

### Low: External `window.open` Without Explicit `noopener`

Severity: Low

Evidence:

- `src/components/PremiumPageLayout.jsx` opens action links using `window.open(action.href, '_blank')`.

Impact:

- External pages may retain access to `window.opener` in some browser contexts.

Fix:

- Use `window.open(url, '_blank', 'noopener,noreferrer')`.
- For anchor links, use `rel="noopener noreferrer"`.

### Low: Tracked Log File

Severity: Low

Evidence:

- `config/logs/codex.log` existed as a tracked file before this audit.

Impact:

- Logs can accidentally capture sensitive operational data.

Fix:

- Implemented during this audit: deleted `config/logs/codex.log` from the current tree.
- Implemented during this audit: added `config/logs/` and `*.log` to `.gitignore`.

## Dependency Security

- `npm audit` reported 0 vulnerabilities.
- Python dependency vulnerability audit could not run because `pip_audit` is not installed.
- `pip check` reported no broken requirements.

## Security Recommendations

1. Rotate and purge the previously tracked secret if this repo has been pushed.
2. Make `127.0.0.1` the only default bind for local use.
3. Add retention controls that cover browser history, SQLite traces, sessions, and cache together.
4. Add auth/rate limiting before any network exposure.
5. Add dependency vulnerability scanning to CI.
6. Add tests for zero-retention and local history behavior.
