# PromptCompiler

PromptCompiler is a local-first prompt analysis and optimization workbench. It helps inspect long LLM prompts, preserve important facts, reduce avoidable token waste, and compile prompts into a cleaner shape before they are sent to a model.

It runs locally with deterministic Python logic by default. NVIDIA NIM integration is optional and only used when you provide an API key.

## What It Does

- Analyzes prompt structure, token estimates, roles, duplicate sections, and protected entities.
- Compiles prompts in `lossless`, `balanced`, or `aggressive` modes.
- Preserves pinned instructions and critical values such as case IDs, names, amounts, and dates.
- Shows optimized output, savings metrics, diffs, warnings, lint findings, semantic signals, and request traces.
- Provides a React workbench UI plus JSON APIs for agents, scripts, and SDK-style integrations.
- Supports local SQLite session metrics and request tracing without storing raw prompt payloads in trace rows.
- Optionally connects to NVIDIA NIM for model listing, summarization, and prompt generation.

## Project Layout

```text
promptcompiler/      Python compiler, APIs, SDK helpers, storage, and server
src/                 React source for the workbench UI
web/                 Built static UI served by the Python server
tests/               Python and browser regression tests
docs/reference/      Extended architecture drafts and source material
docs/superpowers/    Product specs and implementation plans
prd.md               Product requirements
trd.md               Technical requirements
PROJECT_BLUEPRINT.md Combined architecture and roadmap reference
```

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer
- npm

The Python code uses the standard library for the local server and core tests. The frontend uses Vite and React.

## Setup

```bash
npm install
cp .env.example .env
```

Edit `.env` only if you want NVIDIA NIM or a custom local database path:

```bash
NVIDIA_API_KEY=your_key_here
PROMPTCOMPILER_DEFAULT_MODEL=openai/gpt-oss-120b
PROMPTCOMPILER_DB_PATH=.promptcompiler/promptcompiler.sqlite3
```

`.env`, `.promptcompiler/`, `node_modules/`, local screenshots, and other generated files are intentionally ignored by git.

## Run Locally

For the full local app with the Python API and built UI:

```bash
npm run build
python3 -m promptcompiler.server
```

Open:

```text
http://127.0.0.1:8765
```

For frontend development with Vite proxying API calls to the Python server:

```bash
python3 -m promptcompiler.server
npm run dev
```

Vite prints the frontend URL, usually `http://127.0.0.1:5173`.

## CLI

```bash
python3 -m promptcompiler.cli models
python3 -m promptcompiler.cli analyze prompt.json
python3 -m promptcompiler.cli compile prompt.json --out optimized.txt
```

## API Examples

Analyze prompt structure:

```bash
curl -s http://127.0.0.1:8765/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "@pin Return JSON for CASE-123."},
      {"role": "user", "content": "Should we approve a refund over $500?"}
    ],
    "zero_retention": true
  }'
```

Compile and reduce a prompt:

```bash
curl -s http://127.0.0.1:8765/v1/compile \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "mode": "balanced",
    "messages": [
      {"role": "system", "content": "@pin Keep CASE-123 exactly."},
      {"role": "user", "content": "Can ACME approve the refund?"}
    ],
    "rag_chunks": [
      {"id": "policy-a", "source": "policy", "text": "Refunds over $500 require manager approval."},
      {"id": "policy-b", "source": "policy-copy", "text": "Refunds over $500 require manager approval."}
    ],
    "semantic_policy": {"scorer": "embedding", "provider": "deterministic"},
    "zero_retention": true
  }'
```

Lint for token waste:

```bash
curl -s http://127.0.0.1:8765/v1/lint \
  -H "Content-Type: application/json" \
  -d '{"input": "Analyze this code, explain it, optimize it, write tests, generate docs"}'
```

## Python SDK

```python
import promptcompiler

client = promptcompiler.PromptCompilerClient("http://127.0.0.1:8765")

analysis = client.analyze(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize this support ticket."}],
)

compiled = client.compile(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "repeat\n\nrepeat"}],
    mode="balanced",
)
```

You can also wrap OpenAI-like clients with `promptcompiler.wrap(...)` for local analysis or mock proxy flows.

## Test And Build

Run the Python and browser regression suite:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests
```

Build the static UI:

```bash
npm run build
```

Check for whitespace issues before committing:

```bash
git diff --check
```

## Notes

- Raw prompt payloads are processed locally by default.
- Request traces store metrics and transformation metadata, not raw prompt text.
- Compile-cache entries can store response JSON when cache policy is enabled, so treat local databases as private development data.
- Live upstream provider forwarding and streaming are future work; the current proxy path returns local mock-provider responses unless a feature explicitly calls NVIDIA NIM.
