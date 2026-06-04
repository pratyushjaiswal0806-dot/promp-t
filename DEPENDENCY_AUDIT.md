# Dependency Audit

## Frontend Dependencies

Command:

```bash
npm audit --json
```

Result:

- 0 vulnerabilities.

Command:

```bash
npm outdated --json
```

Result:

- Several packages have newer patch/minor/major versions available.

## Frontend Dependency Review

| Dependency | Used | Notes | Recommendation |
| --- | --- | --- | --- |
| `@vitejs/plugin-react` | Yes | Used by `vite.config.js`. Latest major is newer than installed range. | Keep; upgrade with Vite in a planned build-tool pass. |
| `vite` | Yes | Core frontend build tool. Patch and major updates available. | Keep; upgrade carefully after checking Node compatibility and build output. |
| `react` | Yes | Core UI dependency. Patch update available. | Keep; patch update is low risk after tests. |
| `react-dom` | Yes | Required by React DOM rendering. Patch update available. | Keep; patch update with React. |
| `framer-motion` | Yes | Used in motion/UI components. | Keep if motion remains part of the design language. |
| `lucide-react` | Yes | Used for icons. | Keep. |
| `react-router-dom` | No source usage found | `depcheck` reported it as unused. The app appears to use a custom router hook instead. | Remove after one final import/search verification. |

## Frontend Dependency Tool Notes

`depcheck` also reported a missing `@emotion/is-prop-valid` reference from generated `web/assets`. That appears to be generated bundle noise, not a source dependency issue. Dependency tools should exclude `web/` build output.

## Python Dependencies

Command:

```bash
python3 -m pip check
```

Result:

- Passed.
- No broken requirements found.

Command:

```bash
python3 -m pip list --outdated --format=json
```

Observed outdated packages included:

- `certifi`
- `click`
- `fastapi`
- `idna`
- `pip`
- `platformdirs`
- `pydantic`
- `pydantic_core`
- `starlette`
- `uvicorn`

Command:

```bash
python3 -m pip_audit -r requirements.txt --format json
```

Result:

- Failed because `pip_audit` is not installed.

## Python Dependency Review

| Dependency | Used | Notes | Recommendation |
| --- | --- | --- | --- |
| `fastapi` | Yes | Main API framework. | Keep; patch update after tests. |
| `httpx` | Not clearly used in reviewed source | May be planned or used indirectly in tests/docs. | Verify with source search, remove if unused. |
| `pydantic-settings` | Yes | Used for environment/settings modeling. | Keep. |
| `uvicorn[standard]` | Yes | Runtime server dependency. | Keep; patch update after tests. |

## Dependency Risks

- No CI vulnerability scan was found.
- Python vulnerability audit tooling is missing.
- Generated build output makes dependency scanning noisier.
- Build-tool versions are modern, but Vite/plugin major upgrades should be treated as a coordinated change.

## Recommended Actions

1. Add dependency scanning to CI.
2. Install and run `pip-audit` or an equivalent Python vulnerability scanner.
3. Exclude `web/` from dependency usage scans.
4. Remove `react-router-dom` after final verification.
5. Review whether `httpx` is actually needed.
6. Plan a patch update pass for React, React DOM, FastAPI, Starlette, Uvicorn, Pydantic, and certificate-related dependencies.
