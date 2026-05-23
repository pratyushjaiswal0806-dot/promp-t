# NIM-First PromptCompiler Design

## Objective

Build a local-first PromptCompiler MVP that analyzes prompt token usage, safely compiles obvious context waste, and optionally uses NVIDIA NIM APIs when `NVIDIA_API_KEY` is available.

## Approved Direction

The product is NIM-assisted, not NIM-dependent. The deterministic analyzer and compiler must work without any paid API key. NVIDIA NIM is used only for explicit assisted summarization actions.

## Architecture

The app uses a Python standard-library HTTP server, a focused Python core package, and a static browser UI. There is no database, auth system, Redis, ClickHouse, or production proxy in the MVP.

Core modules:

- `parser.py`: turns raw text or OpenAI-compatible messages into segments.
- `tokenizer.py`: deterministic local token estimator.
- `entities.py`: extracts values that should be preserved.
- `analyzer.py`: computes token breakdowns, duplicate groups, and opportunity scores.
- `compiler.py`: removes exact duplicates and compacts log/tool output while preserving pins and entities.
- `nim.py`: optional OpenAI-compatible NVIDIA NIM client.
- `server.py`: local JSON API and static file server.

## Data Flow

User input enters the browser workbench and is posted to `/api/analyze` or `/api/compile`. The server parses the input, estimates tokens, extracts protected entities, and returns structured JSON. Compile requests rebuild optimized text and include a change report. NIM requests go through `/api/nim/summarize` only when the user explicitly triggers them.

## Error Handling

Invalid input returns a JSON error with status `400`. Missing NIM credentials returns a JSON error with status `400` and code `NIM_API_KEY_MISSING`. Unexpected server failures return status `500` without exposing secrets.

## Testing

Use Python `unittest`. Tests are written before production code for parser, analyzer, compiler, entity extraction, and NIM request behavior. Full verification is `python3 -m unittest discover -s tests`, followed by launching the local server and checking the browser UI.

## Scope Boundaries

The MVP excludes accounts, billing, quotas, RBAC, production proxy mode, external judge evaluation, semantic cache, ClickHouse telemetry, and framework integrations.
