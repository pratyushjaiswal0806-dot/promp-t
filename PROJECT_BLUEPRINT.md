# PromptCompiler Project Blueprint

Last updated: 2026-05-25

This document is the combined product requirements document and technical
requirements document for PromptCompiler. It is intended to be the single
high-context reference for anyone trying to understand what the product is, why
it exists, how it works, what has already been built, how to run it, how to test
it, and where the architecture is meant to go next.

It consolidates the current repository state, the original `prd.md`, the
original `trd.md`, the platform roadmap specs, the token reduction roadmap, and
the implementation now present in `promptcompiler/`, `web/`, and `tests/`.

## Table Of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Product Definition](#2-product-definition)
- [3. Target Users And Use Cases](#3-target-users-and-use-cases)
- [4. Product Scope](#4-product-scope)
- [5. User Workflows](#5-user-workflows)
- [6. Functional Requirements](#6-functional-requirements)
- [7. Non-Functional Requirements](#7-non-functional-requirements)
- [8. Current Feature Inventory](#8-current-feature-inventory)
- [9. Token Reduction System](#9-token-reduction-system)
- [10. Architecture Overview](#10-architecture-overview)
- [11. Runtime Stack](#11-runtime-stack)
- [12. Repository Layout](#12-repository-layout)
- [13. Core Domain Model](#13-core-domain-model)
- [14. Compiler Pipeline](#14-compiler-pipeline)
- [15. Semantic And RAG Pipeline](#15-semantic-and-rag-pipeline)
- [16. Platform API](#16-platform-api)
- [17. Legacy Workbench API](#17-legacy-workbench-api)
- [18. OpenAI-Compatible Proxy](#18-openai-compatible-proxy)
- [19. Python SDK](#19-python-sdk)
- [20. CLI](#20-cli)
- [21. Local Storage, Sessions, Metrics, And Cache](#21-local-storage-sessions-metrics-and-cache)
- [22. Web Workbench](#22-web-workbench)
- [23. NVIDIA NIM Integration](#23-nvidia-nim-integration)
- [24. Policies And Registries](#24-policies-and-registries)
- [25. Privacy, Security, And Retention](#25-privacy-security-and-retention)
- [26. Configuration](#26-configuration)
- [27. Testing And Verification](#27-testing-and-verification)
- [28. Known Limitations](#28-known-limitations)
- [29. Roadmap](#29-roadmap)
- [30. Glossary](#30-glossary)

## 1. Executive Summary

PromptCompiler is a local-first workbench and developer utility for inspecting,
budgeting, and reducing LLM prompt context before it is sent to a model
provider. It is designed for developers, agent builders, and power users who
have large prompts, long chat histories, RAG payloads, tool schemas, logs, and
other context-heavy inputs that need to be made smaller without silently losing
important instructions or protected values.

The project started as a local web workbench with deterministic prompt analysis
and compilation. It now includes:

- A dependency-light Python package.
- A standard-library HTTP server.
- A static browser UI.
- Prompt parsing for raw text and OpenAI-compatible messages.
- Local token estimation.
- Protected entity extraction.
- Deterministic compile modes.
- Semantic chunk scoring and RAG pruning.
- Policy-driven prompt/output/tool/cache controls.
- A versioned `/v1` platform API.
- SQLite-backed traces, metrics, sessions, and compile cache.
- A Python SDK and OpenAI-like client wrapper.
- A local OpenAI-compatible mock proxy endpoint.
- Optional NVIDIA NIM model listing and summarization.
- Browser-level and unit regression coverage.

The central product promise is not "magically summarize everything." The real
promise is:

1. Show where tokens are going.
2. Identify what can safely be removed or compacted.
3. Preserve pinned instructions and protected values.
4. Produce an explainable transformation plan.
5. Expose the same capability through UI, API, SDK, CLI, and proxy surfaces.

The system deliberately works without paid provider calls. Optional NIM support
is available only when explicitly configured and invoked.

## 2. Product Definition

### 2.1 Product Name

PromptCompiler

### 2.2 Product Category

Local-first LLM prompt analysis, token budgeting, and context optimization
tooling.

### 2.3 Core Problem

LLM applications often waste large numbers of input tokens on repeated context,
verbose tool output, duplicated RAG chunks, oversized system prompts, broad tool
schemas, long chat history, and unclear multi-task user prompts. These costs are
hard to see before the request is sent. If a developer manually shortens the
context, they risk deleting IDs, constraints, dates, URLs, schema requirements,
or pinned instructions that the model still needs.

PromptCompiler exists to make this process inspectable and safer.

### 2.4 Product Thesis

Prompt reduction should be treated like a compile step:

- Parse the prompt into structured components.
- Estimate the size and risk of each component.
- Apply deterministic transforms where possible.
- Preserve explicit constraints.
- Produce a diff, plan, and trace metadata.
- Avoid external model calls unless the user explicitly opts in.

### 2.5 Product Positioning

PromptCompiler is not a general chat app, provider, hosted observability suite,
or autonomous agent runtime. It is a local prompt compiler and inspection layer
that can sit before those systems.

It can be used as:

- A browser workbench for manual analysis.
- A CLI for local scripts.
- An API server for agents and tools.
- A Python SDK wrapper around OpenAI-like clients.
- A local proxy in front of OpenAI-compatible chat completions.

## 3. Target Users And Use Cases

### 3.1 Primary Users

Developers building AI products:

- Need to control cost and context size.
- Work with chat messages, RAG chunks, and tool calls.
- Need explainable behavior and local testing.
- Care about traceability, retention, and safety.

Agent builders:

- Have long session histories and repeated tool traces.
- Need adaptive session compaction.
- Need pre-send linting for bloated prompts.
- Want a wrapper/proxy that can reduce context without rewriting the agent.

Power users and prompt engineers:

- Want to paste a prompt and see where tokens are going.
- Want to mark protected instructions with `@pin`.
- Want to compare input and optimized output visually.
- Want exportable JSON reports.

### 3.2 Secondary Users

Platform teams:

- Want zero-retention local traces.
- Want metrics around savings and cache behavior.
- Want provider-agnostic request contracts.

Students and portfolio builders:

- Can use the project as a concrete example of local-first AI tooling,
  platform API design, and browser-visible verification.

### 3.3 Jobs To Be Done

- "Before I send this giant prompt, show me what it contains and what it costs."
- "Remove duplicated or redundant context without losing important IDs."
- "Keep a pinned system/developer instruction exactly present."
- "Compact repeated tool logs and noisy RAG payloads."
- "Route simple prompts toward cheaper/smaller models."
- "Store metrics and traces without storing raw prompts."
- "Wrap my existing OpenAI-like client with minimal integration work."
- "Test prompt optimization locally before wiring a paid provider."

## 4. Product Scope

### 4.1 In Scope

Prompt analysis:

- Parse raw text blocks.
- Parse OpenAI-compatible `messages`.
- Estimate tokens locally.
- Break down tokens by role and segment type.
- Detect duplicate segments.
- Extract protected entities.
- Identify compression opportunity.

Deterministic compilation:

- Preserve `@pin` content.
- Remove duplicate unpinned segments.
- Collapse repeated adjacent lines.
- Truncate verbose tool/RAG output.
- Summarize older unpinned history locally in balanced/aggressive modes.
- Minify JSON and Markdown-like content.
- Build a plan, diff, warnings, and risk score.

Token reduction controls:

- Context policy.
- Output policy.
- Reusable system prompt refs.
- Structured input minification.
- Tool schema compaction.
- Retrieval top-k and token budgeting.
- Session sliding window and summary context.
- Compile caching.
- Token-waste linting.
- Simple model routing hints.

Local platform integration:

- `/api/*` workbench routes.
- `/v1/*` platform routes.
- Python SDK.
- OpenAI-compatible proxy route.
- CLI.
- SQLite traces, metrics, sessions, and cache.

NIM integration:

- Optional `.env` loading.
- Optional NVIDIA model listing.
- Optional NIM summarization.
- Explicit browser confirmation before sending prompt text externally.
- Protected-entity preservation check on NIM summaries.

### 4.2 Out Of Scope Today

- Hosted SaaS deployment.
- Authentication and multi-user accounts.
- Billing.
- Team workspaces.
- Live upstream provider forwarding through the proxy.
- Streaming proxy responses.
- Provider-specific exact tokenizers.
- Embedding-backed semantic scoring.
- A database server such as Postgres.
- Redis or distributed cache.
- Browser extension packaging.
- Mobile app packaging.

### 4.3 Future Scope

- Live provider forwarding.
- Streaming proxy support.
- Provider-specific tokenizers.
- Embedding-based RAG scoring.
- Evaluation jobs that compare optimized prompt quality against originals.
- Enterprise controls for policy packs and audit export.
- More advanced system prompt registry.
- Tool schema policy packs.
- Cross-session analytics.

## 5. User Workflows

### 5.1 Browser Workbench Flow

1. Start the local server:

```bash
python3 -m promptcompiler.server
```

2. Open:

```text
http://127.0.0.1:8765
```

3. Paste a prompt, raw text, Markdown, JSON, logs, or OpenAI-compatible message
   JSON.

4. Pick a model from the local/live model picker.

5. Optionally select:

- Compression mode.
- Target token budget.
- System prompt ref.
- Output format.
- Max words.
- Retrieval top-k.
- Cache prefix flag.
- Compile cache flag.
- Explain flag.
- Dry-run mode.

6. Click `Analyze`, `Lint`, or `Compile & Optimize`.

7. Inspect:

- Token metrics.
- Segment table.
- Protected values.
- Changes.
- Lint findings.
- Diff.
- Semantic signals.
- Optimized output.

8. Copy or export optimized text/JSON.

### 5.2 API Integration Flow

1. Start the local server.
2. POST a provider-style payload to `/v1/analyze` or `/v1/compile`.
3. Read `trace_id`, token counts, retention metadata, transformations, and
   optimized messages.
4. Send the optimized messages to the real provider if desired.
5. Query `/v1/metrics` or `/v1/requests/{trace_id}` for local observability.

### 5.3 SDK Wrapper Flow

1. Wrap an OpenAI-like client:

```python
import promptcompiler

wrapped = promptcompiler.wrap(openai_client, base_url="http://127.0.0.1:8765")
```

2. Call `wrapped.chat.completions.create(...)` as usual.
3. Pass PromptCompiler options through the `promptcompiler` request key.
4. Read the attached `response.promptcompiler` metadata.

### 5.4 Proxy Flow

1. Send an OpenAI-compatible chat completion request to:

```text
/v1/proxy/openai/chat/completions
```

2. Include an optional `promptcompiler` object.
3. PromptCompiler compiles the request locally.
4. The current proxy returns a mock OpenAI-compatible response with trace/token
   headers.

### 5.5 Session Management Flow

1. Append turns to `/v1/sessions/{session_id}/append`.
2. Provide `target_token_budget` and mode.
3. PromptCompiler tracks token count.
4. At 70 percent budget utilization, older unpinned turns are compacted into a
   summary row.
5. Fetch compact context from `/v1/sessions/{session_id}/context`.

### 5.6 NIM Summarization Flow

1. Set `NVIDIA_API_KEY` in `.env` or environment.
2. Start the server.
3. Use the UI `NIM Summarize` button or call `/api/nim/summarize`.
4. The UI asks for confirmation before sending prompt text externally.
5. The response includes a summary and preservation metadata.

## 6. Functional Requirements

### 6.1 Prompt Parsing

The system must accept:

- Empty input.
- Plain text.
- Multi-paragraph text.
- Code blocks.
- OpenAI-style `messages` arrays.
- JSON objects containing `messages`.
- Message content as strings, arrays, or structured values.
- Provider-style platform payloads with `messages`, `input`, `prompt`, or
  `structured_input`.

The parser must produce ordered `Segment` records with:

- Stable segment IDs.
- Segment type.
- Role.
- Text.
- Estimated tokens.
- Pinned flag.
- Protected entities.

### 6.2 Analysis

Analysis must return:

- Selected model ID.
- Total token estimate.
- Segment count.
- Token breakdown by type.
- Token breakdown by role.
- Largest segments.
- Duplicate groups.
- Protected entities.
- Compression opportunity.
- Full segment list.

### 6.3 Compilation

Compilation must:

- Validate mode.
- Validate target budget.
- Reject pinned content that exceeds the pinned budget limit.
- Preserve pinned content.
- Remove exact duplicate unpinned segments.
- Compact repeated lines.
- Compact JSON and Markdown only outside lossless mode.
- Truncate verbose tool/RAG output while preserving protected lines.
- Summarize verbose tool/RAG output locally in balanced/aggressive modes.
- Summarize older unpinned context locally in balanced/aggressive modes.
- Build semantic scoring metadata.
- Prune redundant RAG chunks in balanced/aggressive modes.
- Report warnings when target budget cannot be met safely.
- Check protected entity preservation.
- Return active and proposed optimized text.
- Return metrics that do not imply token savings when output text is unchanged.

### 6.4 Compile Modes

`lossless`:

- Default mode.
- Safest behavior.
- Duplicate removal and repeated-line compaction are allowed.
- No JSON/Markdown minify.
- No local history summarization.
- No tool/RAG summarization.
- Large tool/RAG truncation uses wider limits.

`balanced`:

- Intended default for practical savings.
- Allows structured minify.
- Allows larger tool/RAG compaction.
- Allows older-history summarization.
- Allows RAG pruning with stricter similarity threshold.
- Medium risk score baseline.

`aggressive`:

- Maximizes local savings.
- Uses smaller tool/RAG thresholds.
- Summarizes more context.
- Allows more RAG pruning.
- Higher risk score baseline.
- Must still preserve pinned content and protected values where possible.

### 6.5 Dry Run

Dry run must:

- Build the proposed compile result.
- Leave the active optimized text equal to the original raw input.
- Report active saved tokens as zero when the active output is unchanged.
- Still return the proposed optimized text and proposed savings.

### 6.6 Protected Entity Preservation

Protected entity extraction currently detects:

- URLs.
- ISO dates.
- UUIDs.
- Currency values.
- Percentages.
- Uppercase ticket-like IDs such as `CASE-123`.
- Numeric inequality constraints such as `>= 10`.

Compilation and summarization must report missing protected entities.

### 6.7 Policies

The platform API must normalize:

- `context_policy`.
- `output_policy`.
- `tool_policy`.
- `cache_policy`.

Policy values must be explicit in API responses so downstream tools can inspect
what was applied.

### 6.8 Retrieval

The retrieval helper must:

- Score candidate chunks against the query.
- Sort by score and ID.
- Enforce `top_k`.
- Enforce `max_tokens`.
- Deduplicate highly similar selected chunks.
- Return selected chunks, used tokens, and removed chunk IDs.

### 6.9 Tool Schema Compaction

Tool schema handling must:

- Keep important schema fields.
- Shorten verbose descriptions.
- Remove examples and comments.
- Recursively compact parameters.
- Select relevant tools by query overlap when compact policy is enabled.

### 6.10 Linting

Linting must detect avoidable token waste patterns:

- Huge reusable system prompts.
- Multi-task requests.
- Agent reflection overhead.
- Too many retrieved results.

### 6.11 Metrics And Traces

Every `/v1/analyze` and `/v1/compile` call must record a trace containing:

- Trace ID.
- Endpoint.
- Provider.
- Model.
- Session ID.
- Mode.
- Original and optimized token counts.
- Token reduction percent.
- Estimated cost before/after.
- Cache status.
- Evaluation status.
- Zero-retention flag.
- Latency.
- Transformations.
- Retention metadata.

Trace rows must not store raw prompt text.

## 7. Non-Functional Requirements

### 7.1 Local-First

The application must run on a local machine with:

- Python 3.
- Standard library server.
- Static browser assets.
- SQLite for local persistence.

No paid API key should be required for the core workflow.

### 7.2 Dependency Discipline

The current implementation deliberately avoids large framework dependencies.
The core server, SDK, CLI, and tests are standard-library Python.

The browser UI is plain HTML, CSS, and JavaScript.

### 7.3 Privacy

Raw prompt text should be processed locally by default. Traces should store
metadata, not raw payloads. Zero-retention mode must make that explicit in
responses.

### 7.4 Explainability

Every compile response must include transformation metadata, diff information,
risk score, warnings, and preservation checks.

### 7.5 Safety

The compiler must favor preserving important context over meeting a token budget
at all costs. If the target cannot be met safely, the system should return a
warning rather than pretending the budget was satisfied.

### 7.6 Testability

The codebase should remain testable through:

- Unit tests.
- API handler tests.
- Storage tests.
- SDK tests.
- Browser/static asset tests.
- End-to-end UI tests.

### 7.7 Portability

The project should run without Docker, Postgres, Redis, or Node for the main
server. Node is only used for the current browser E2E runner.

## 8. Current Feature Inventory

### 8.1 Product Features

- Local workbench UI.
- Model picker.
- Searchable model list.
- Built-in samples.
- Prompt file import.
- Analyze button.
- Lint button.
- Compile button.
- NIM summarize button.
- Copy optimized output.
- Export optimized text.
- Export JSON compile report.
- Segment table.
- Diff panel.
- Semantic signals panel.
- Protected values panel.
- Local browser history.
- Responsive layout coverage.

### 8.2 Compiler Features

- Parse text/messages into segments.
- Token estimates.
- Duplicate segment detection.
- Duplicate removal.
- Repeated-line collapse.
- Tool/log truncation.
- Tool/RAG local summarization.
- Older context local summarization.
- JSON minification.
- Markdown plaintext compaction.
- Pinned budget enforcement.
- Protected entity preservation check.
- Lossless/balanced/aggressive modes.
- Dry-run planning.
- Cost-benefit metadata.
- Risk score and risk level.
- Semantic chunk report.

### 8.3 Platform Features

- `/v1/analyze`.
- `/v1/compile`.
- `/v1/retrieve`.
- `/v1/lint`.
- `/v1/metrics`.
- `/v1/requests/{trace_id}`.
- `/v1/sessions/{id}/append`.
- `/v1/sessions/{id}/context`.
- `/v1/proxy/openai/chat/completions`.
- Trace IDs.
- Tokenizer metadata.
- Retention metadata.
- Provider/model/session fields.
- Cache metadata.
- Route metadata.

### 8.4 Developer Integration Features

- Python client.
- OpenAI-like wrapper.
- Analyze-only wrapper mode.
- Direct compile wrapper mode.
- Proxy route.
- CLI models/analyze/compile.
- Exportable JSON reports.

## 9. Token Reduction System

PromptCompiler reduces token usage through multiple layers. Some change the
prompt text. Others reduce future prompt construction before the model call.

### 9.1 Reduction Layers

| Layer | Mechanism | Implemented In | Main Benefit |
| --- | --- | --- | --- |
| Parsing | Segment prompt into typed blocks | `parser.py` | Makes reductions inspectable |
| Analysis | Detect token-heavy and duplicate segments | `analyzer.py` | Shows opportunity before compile |
| Lossless compile | Dedupe and repeat collapse | `compiler.py` | Low-risk savings |
| Structured minify | JSON/Markdown compaction | `minify.py` | Smaller machine inputs |
| Semantic pruning | Local chunk scoring and RAG dedupe | `semantic.py` | Removes redundant retrieved context |
| Embedding-style scoring | Deterministic local vector similarity when enabled | `embeddings.py`, `semantic.py` | Catches paraphrased RAG redundancy |
| Retrieval budget | top-k and max-token selection | `retrieval.py` | Prevents over-injection |
| Session compaction | Summary plus recent/pinned turns | `storage.py`, `session_context.py` | Controls long chats |
| Prompt refs | Reusable short system instructions | `prompt_registry.py` | Avoids repeated large prompts |
| Output policy | Max words / JSON / bullets / no explanation | `policies.py` | Reduces expected completion size |
| Tool policy | Schema compaction and tool selection | `tools.py` | Shrinks tool definitions |
| Routing | Small/primary route hints | `routing.py` | Helps avoid overpowered models |
| Compile cache | Stable compile cache keys | `cache.py`, `storage.py` | Avoids repeated work |
| Lint | Pre-send waste warnings | `lint.py` | Flags bloat before send |

### 9.2 Lossless Metric Rule

PromptCompiler must not report token savings when the output text is unchanged.

The compiler enforces this through `_token_metrics_for_output(...)`:

- If `optimized_text == raw_input`, optimized tokens equal original tokens.
- Saved tokens are zero.
- This applies to dry-run active output and any compile result where no actual
  output change occurs.

This rule prevents misleading savings caused by minor differences between
segment-level token overhead and whole-text token estimation.

### 9.3 Pinned Budget Rule

Pinned content is protected, but it cannot consume the whole target budget.

When `target_token_budget` is set:

- Pinned tokens are summed.
- Pinned limit is 25 percent of the target budget.
- If pinned tokens exceed that limit, compile fails with:
  `PINNED_BUDGET_EXCEEDED`.

The reason is practical: if a user pins too much text, the compiler cannot
truthfully reduce the prompt under the target without violating the pin.

### 9.4 Target Budget Rule

The target budget is a goal, not permission to delete important content.

If optimized output remains above the target:

- The compile still returns the safest result.
- A warning explains that the target could not be met safely.
- Risk metadata reflects the concern.

## 10. Architecture Overview

### 10.1 High-Level System

```text
Browser UI
  |
  | /api/* and /v1/*
  v
Standard-library Python HTTP server
  |
  +--> Parser
  +--> Analyzer
  +--> Compiler
  |      |
  |      +--> Entity extraction
  |      +--> Minify helpers
  |      +--> Semantic/RAG scoring
  |      +--> Diff builder
  |
  +--> Platform API normalization
  |      |
  |      +--> Context/output/tool/cache policies
  |      +--> Retrieval helper
  |      +--> Routing helper
  |
  +--> SQLite store
  |      |
  |      +--> Sessions
  |      +--> Session turns
  |      +--> Request traces
  |      +--> Compile cache
  |
  +--> Optional NVIDIA NIM client
```

### 10.2 Request Lifecycle For `/v1/compile`

```text
Incoming JSON payload
  |
  v
normalize_v1_request
  |
  +--> provider/model/session/mode/budget
  +--> context/output/tool/cache policies
  +--> messages/input/prompt/structured_input normalization
  +--> prompt ref and output instruction prefix
  |
  v
cache lookup if cache_policy.enabled
  |
  +--> hit: return cached response with new trace_id
  |
  v
compile_prompt
  |
  +--> parse_prompt
  +--> enforce pinned budget
  +--> semantic report
  +--> dedupe / compact / summarize / prune
  +--> preservation check
  +--> diff and plan
  |
  v
platform response shaping
  |
  +--> optimized_prompt
  +--> optimized_messages
  +--> transformations
  +--> evaluation metadata
  +--> route metadata
  +--> retention metadata
  |
  v
record SQLite trace
  |
  v
return JSON
```

### 10.3 Request Lifecycle For Browser Compile

The browser currently calls `/v1/compile` directly for compile actions. The UI
builds a payload from the controls, then renders the returned platform response
into workbench panels.

## 11. Runtime Stack

### 11.1 Backend

- Python package: `promptcompiler`.
- HTTP server: `http.server.ThreadingHTTPServer`.
- Request handling: `BaseHTTPRequestHandler`.
- Persistence: SQLite through `sqlite3`.
- HTTP outbound NIM calls: `urllib.request`.
- CLI: `argparse`.
- Tests: `unittest`.

### 11.2 Frontend

- Static `web/index.html`.
- Static `web/styles.css`.
- Static `web/app.js`.
- SVG favicon.
- No frontend framework.
- No bundler required for the app itself.

### 11.3 Optional External Service

- NVIDIA NIM OpenAI-compatible API.
- Default base URL: `https://integrate.api.nvidia.com/v1`.
- Requires `NVIDIA_API_KEY`.

### 11.4 Current Repository Scale

At the time this document was generated:

- The repository has 24 Python modules under `promptcompiler/`.
- The test suite has 20 Python test files plus a browser E2E runner.
- The web app has HTML, CSS, JS, and SVG assets.
- The measured repo subset was about 11,626 lines across product docs, code,
  tests, web assets, and roadmap/spec documents.

## 12. Repository Layout

```text
.
├── README.md
├── prd.md
├── trd.md
├── PROJECT_BLUEPRINT.md
├── docs/
│   └── superpowers/
│       ├── plans/
│       └── specs/
├── promptcompiler/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── cache.py
│   ├── cli.py
│   ├── compiler.py
│   ├── diff.py
│   ├── embeddings.py
│   ├── entities.py
│   ├── env.py
│   ├── lint.py
│   ├── minify.py
│   ├── models.py
│   ├── nim.py
│   ├── parser.py
│   ├── policies.py
│   ├── prompt_registry.py
│   ├── proxy.py
│   ├── retrieval.py
│   ├── routing.py
│   ├── samples.py
│   ├── sdk.py
│   ├── semantic.py
│   ├── server.py
│   ├── session_context.py
│   ├── storage.py
│   ├── tokenizer.py
│   ├── tools.py
│   └── v1.py
├── tests/
│   ├── test_*.py
│   └── web_e2e_runner.mjs
└── web/
    ├── app.js
    ├── favicon.svg
    ├── index.html
    └── styles.css
```

### 12.1 Module Inventory

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Public exports: `PromptCompilerClient`, `wrap`, `__version__`. |
| `analyzer.py` | Token allocation, duplicate groups, largest segments, protected entity inventory. |
| `cache.py` | Stable compile cache key generation. |
| `cli.py` | Command-line `models`, `analyze`, and `compile` commands. |
| `compiler.py` | Deterministic compile modes, budget validation, diff, plan, savings metrics. |
| `diff.py` | Kept/removed segment diff helpers. |
| `embeddings.py` | Deterministic local embedding helpers and semantic policy normalization. |
| `entities.py` | Regex-based protected entity extraction. |
| `env.py` | Local `.env` loading with disable switch. |
| `lint.py` | Token waste lint rules. |
| `minify.py` | JSON minification, Markdown plaintext compaction, structured input serialization. |
| `models.py` | Local NIM-first model registry and default model selection. |
| `nim.py` | Optional NVIDIA NIM client, model listing, summarization, error mapping. |
| `parser.py` | Raw text and messages parsing into `Segment` records. |
| `policies.py` | Context and output policy normalization. |
| `prompt_registry.py` | Built-in reusable system prompt refs. |
| `proxy.py` | OpenAI-compatible proxy helper and mock provider response. |
| `retrieval.py` | Budget-aware retrieval selection and dedupe. |
| `routing.py` | Simple model route hints. |
| `samples.py` | Built-in UI samples. |
| `sdk.py` | Dependency-free Python client and OpenAI-like wrapper. |
| `semantic.py` | Local semantic chunking, scoring, and RAG pruning. |
| `server.py` | HTTP server, static serving, `/api/*`, `/v1/*` routing. |
| `session_context.py` | Compact context assembly for sessions. |
| `storage.py` | SQLite sessions, traces, metrics, compile cache. |
| `tokenizer.py` | Approximate local token estimator. |
| `tools.py` | Tool schema compaction and relevant tool selection. |
| `v1.py` | Versioned platform API normalization and response shaping. |

## 13. Core Domain Model

### 13.1 Segment

`Segment` is the core parsed unit.

Fields:

- `id`: stable ID such as `seg_1`.
- `type`: one of text-like, system, developer, user, assistant, tool, rag.
- `role`: original chat role or `unknown`.
- `text`: segment content.
- `tokens`: approximate token count plus segment overhead.
- `pinned`: true when text contains `@pin`.
- `entities`: protected values found in the segment.

### 13.2 Segment Types

From message roles:

- `system`
- `developer`
- `user`
- `assistant`
- `tool`
- `text`

From raw text heuristics:

- `tool` when text looks like errors, tracebacks, warnings, or logs.
- `rag` when text includes `Source:` or citation markers.
- `text` otherwise.

### 13.3 Compile Result

The core compiler returns:

- `model`
- `mode`
- `target_token_budget`
- `dry_run`
- `original_tokens`
- `optimized_tokens`
- `tokens_saved`
- `savings_ratio`
- `optimized_text`
- `proposed_optimized_text`
- `proposed_optimized_tokens`
- `proposed_tokens_saved`
- `changes`
- `diff`
- `retained_segment_ids`
- `preservation`
- `plan`
- `semantic`
- `warnings`
- `risk_score`
- `evaluation_status`
- `cache_status`
- `cost_benefit`

### 13.4 Platform Compile Response

The `/v1/compile` response wraps the core compiler with integration metadata:

- `trace_id`
- `provider`
- `model`
- `session_id`
- `mode`
- `dry_run`
- `original_token_count`
- `optimized_token_count`
- `token_reduction_percent`
- `estimated_cost_before_usd`
- `estimated_cost_after_usd`
- `estimated_cost_reduction_percent`
- `optimized_prompt`
- `optimized_messages`
- `transformations`
- `evaluation`
- `cache`
- `route`
- `provider_cache_hints`
- `tokenizer_accuracy`
- `tokenizer`
- `retention`
- `context_policy`
- `output_policy`
- `tool_policy`
- `cache_policy`
- `semantic`
- `preservation`
- `compile`

### 13.5 Analysis Response

The `/v1/analyze` response includes:

- `trace_id`
- `provider`
- `model`
- `session_id`
- `mode`
- `dry_run`
- `total_tokens`
- `estimated_input_cost_usd`
- `budget_utilization`
- `pinned_tokens`
- `pinned_budget_ratio`
- `components`
- `recommendation`
- `tokenizer_accuracy`
- `tokenizer`
- `retention`
- `context_policy`
- `output_policy`
- `tool_policy`
- `analysis`

## 14. Compiler Pipeline

### 14.1 Stage 1: Validate Request

The compiler accepts:

- `raw_input`
- `model`
- `mode`
- `target_token_budget`
- `dry_run`

It validates:

- Mode is one of `lossless`, `balanced`, `aggressive`.
- Target budget is a positive integer if provided.
- Pinned content does not exceed the target pinned budget.

### 14.2 Stage 2: Parse Segments

`parse_prompt` handles:

- JSON object with `messages`.
- Raw messages array.
- Plain text blocks split by blank lines while respecting fenced code blocks.

### 14.3 Stage 3: Build Semantic Report

`build_semantic_report`:

- Chunks every segment.
- Scores chunks against the current query.
- Computes relevance, similarity, novelty, and risk.
- Marks redundant RAG chunks for removal in balanced/aggressive modes.

### 14.4 Stage 4: Iterate Segments

For every segment:

1. If semantic pruning removed it, add a RAG prune change and removed diff.
2. If it is an unpinned duplicate, remove it.
3. Otherwise compact it if allowed.
4. Add retained text to the optimized prompt.
5. Add diff metadata.

### 14.5 Stage 5: Segment Compaction

Compaction can perform:

- JSON minify.
- Markdown plaintext conversion.
- Adjacent repeated-line collapse.
- Large tool/RAG truncation.
- Tool/RAG local summary.
- Older-history local summary.

Pinned segments skip these compactions.

### 14.6 Stage 6: Metrics

The compiler estimates:

- Original tokens from segment tokens.
- Optimized tokens from optimized text.
- Tokens saved.
- Savings ratio.

If the optimized output is byte-for-byte equal to the raw input, it reports zero
savings and uses the original token count as the optimized token count.

### 14.7 Stage 7: Preservation

The compiler extracts protected entities from the original raw input and checks
whether each one exists in the optimized text.

Response shape:

```json
{
  "ok": true,
  "checked_entities": ["CASE-123"],
  "missing_entities": []
}
```

### 14.8 Stage 8: Plan And Risk

The plan contains:

- Mode.
- Target budget.
- Estimated original tokens.
- Estimated optimized tokens.
- Estimated saved tokens.
- Risk level.
- Actions.

Risk score baseline:

- Lossless: low.
- Balanced: medium.
- Aggressive: higher.

Warnings and missing entities increase risk.

## 15. Semantic And RAG Pipeline

### 15.1 Design Intent

The PRD/TRD describes semantic compression and RAG pruning. The default
implementation uses deterministic lexical heuristics so it can run locally
without external services. Phase 1 also supports an optional deterministic local
embedding-style scorer through `semantic_policy`, which improves paraphrase
matching without sending prompt text outside the machine.

### 15.2 Chunking

`chunk_segment`:

- Reads `Source:` and `Citation:` metadata.
- Keeps pinned or short segments as a single chunk.
- Splits long segments into sentence-aware windows.
- Uses default window size of 256 estimated tokens.
- Uses default overlap of 32 estimated tokens.

### 15.3 Scoring

`score_chunks` computes:

- `query_relevance_score`
- `inter_chunk_similarity_score`
- `novelty_score`
- `compression_risk_score`
- `decision`

The scoring is based on normalized lexical token overlap and Jaccard
similarity by default, with stopwords removed. When
`semantic_policy.scorer == "embedding"`, scoring uses deterministic local
vectors and cosine similarity.

### 15.4 RAG Pruning

In balanced/aggressive modes:

- RAG chunks are sorted by relevance and source order.
- A new chunk can be removed if it is highly similar to a retained chunk.
- It must not have better relevance.
- It must not contain unique protected entities.
- Removal produces a `rag_prune` action.

Thresholds:

- Balanced: 0.78 similarity.
- Aggressive: 0.62 similarity.

### 15.5 Semantic Limitations

Because the default scorer is lexical and the Phase 1 embedding scorer is local
and deterministic:

- Paraphrase detection is limited.
- Domain synonyms may not match.
- Scores are deterministic and inspectable but not as strong as provider or
  embedding-model vectors.
- The current system is intentionally conservative around protected entities.

## 16. Platform API

The versioned API is the preferred integration surface for agents, SDKs, and
future hosted-compatible usage.

### 16.1 Common Payload Fields

| Field | Type | Purpose |
| --- | --- | --- |
| `provider` | string | Provider label. Inferred from model if omitted. |
| `model` | string | Model ID. Defaults to configured default model. |
| `messages` | array | OpenAI-compatible messages. |
| `input` | string | Raw text input. |
| `prompt` | string | Alternate raw text field. |
| `structured_input` | any | Minified structured payload. |
| `rag_chunks` | array | Retrieved context candidates. |
| `tools` | array | Tool schemas or tool text. |
| `session_id` | string | Session grouping. |
| `mode` | string | `lossless`, `balanced`, or `aggressive`. |
| `target_token_budget` | integer | Optional token budget. |
| `dry_run` | boolean | Plan only; keep active output unchanged. |
| `zero_retention` | boolean | Local retention preference. |
| `policy.zero_retention` | boolean | Alternate zero-retention location. |
| `context_policy` | object | Context behavior controls. |
| `output_policy` | object | Output-shape behavior controls. |
| `tool_policy` | object | Tool compaction/selection controls. |
| `cache_policy` | object | Compile cache controls. |
| `task_type` | string | Route hint such as grammar or formatting. |

### 16.2 `POST /v1/analyze`

Purpose:

- Normalize provider-style payload.
- Analyze token allocation.
- Return recommendation and component metadata.
- Record trace.

Example:

```bash
curl -s http://127.0.0.1:8765/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "@pin Return JSON for CASE-123."},
      {"role": "user", "content": "Should we approve a refund over $500?"}
    ],
    "target_token_budget": 8000,
    "mode": "balanced",
    "zero_retention": true
  }'
```

### 16.3 `POST /v1/compile`

Purpose:

- Normalize provider-style payload.
- Apply prompt/output/tool/cache policies.
- Compile prompt.
- Return optimized prompt/messages.
- Record trace.
- Optionally store compile cache.

Example:

```bash
curl -s http://127.0.0.1:8765/v1/compile \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "@pin Keep CASE-123 exactly."},
      {"role": "user", "content": "Can ACME approve the refund?"}
    ],
    "rag_chunks": [
      {"id": "policy-a", "source": "policy-a", "text": "Refunds over $500 require manager approval."},
      {"id": "policy-b", "source": "policy-b", "text": "Refunds over $500 require manager approval."}
    ],
    "mode": "balanced",
    "policy": {"zero_retention": true}
  }'
```

### 16.4 `POST /v1/retrieve`

Purpose:

- Budget RAG/search results before adding them to a prompt.

Payload:

```json
{
  "query": "refund over 500",
  "rag_chunks": [
    {"id": "a", "source": "policy", "text": "refund approval over 500 manager"}
  ],
  "top_k": 2,
  "max_tokens": 120
}
```

Response:

- `chunks`
- `tokens`
- `removed_chunk_ids`

### 16.5 `POST /v1/lint`

Purpose:

- Return token-waste findings for a prompt-like payload.

Example:

```bash
curl -s http://127.0.0.1:8765/v1/lint \
  -H "Content-Type: application/json" \
  -d '{"input": "Analyze this code, explain it, optimize it, write tests, generate docs"}'
```

### 16.6 `POST /v1/sessions/{session_id}/append`

Purpose:

- Append a turn to local session state.
- Track token count.
- Trigger compaction when budget utilization crosses 70 percent.

Payload:

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "turn": {
    "role": "tool",
    "content": "ERROR compile failed\nERROR compile failed\nCASE-123 should stay"
  },
  "target_token_budget": 12000,
  "mode": "balanced",
  "zero_retention": true
}
```

### 16.7 `GET /v1/sessions/{session_id}/context`

Purpose:

- Return compact session context.

Query parameters:

- `target_token_budget`
- `sliding_window_turns`

Behavior:

- Keep summaries.
- Keep pinned turns.
- Keep recent turns.
- Stay under approximate budget where possible.

### 16.8 `GET /v1/metrics`

Purpose:

- Return aggregate trace/session/cache metrics.

Optional filters:

- `provider`
- `model`
- `mode`
- `session_id`

### 16.9 `GET /v1/requests/{trace_id}`

Purpose:

- Fetch a stored request trace by trace ID.

Trace payloads include metrics and transformations but not raw prompt payloads.

## 17. Legacy Workbench API

The browser still uses and/or exposes compatibility routes under `/api`.

### 17.1 `GET /api/health`

Returns:

- `ok`
- `nim_configured`
- `default_model`

### 17.2 `GET /api/models`

Returns:

- `default_model`
- `models`

When NVIDIA API key is present, the server attempts live NIM model listing and
deduplicates model IDs against the local fallback registry.

### 17.3 `GET /api/samples`

Returns built-in prompt samples:

- Support RMA Chat.
- Agent Error Logs.
- RAG Overlap.

### 17.4 `POST /api/analyze`

Legacy analyze route for workbench-style payloads:

```json
{
  "input": "...",
  "model": "..."
}
```

### 17.5 `POST /api/compile`

Legacy compile route for workbench-style payloads:

```json
{
  "input": "...",
  "model": "...",
  "mode": "balanced",
  "target_token_budget": 8000,
  "dry_run": false
}
```

### 17.6 `POST /api/export`

Returns:

- `model`
- `optimized_text`
- `compile`

### 17.7 `POST /api/nim/summarize`

Calls NVIDIA NIM summarization when configured.

If key is missing:

```json
{
  "code": "NIM_API_KEY_MISSING",
  "error": "Set NVIDIA_API_KEY to enable NVIDIA NIM actions."
}
```

## 18. OpenAI-Compatible Proxy

### 18.1 Route

```text
POST /v1/proxy/openai/chat/completions
```

### 18.2 Current Behavior

The proxy:

- Accepts OpenAI-style chat completion payloads.
- Reads optional `promptcompiler` options.
- Compiles messages locally through `/v1` logic.
- Returns an OpenAI-compatible mock chat completion shape.
- Adds PromptCompiler trace/token/cache headers.

### 18.3 Headers

The proxy returns:

- `X-PromptCompiler-Trace`
- `X-PromptCompiler-Original-Tokens`
- `X-PromptCompiler-Optimized-Tokens`
- `X-PromptCompiler-Cache-Status`

### 18.4 Unsupported Today

- `stream: true` returns `STREAMING_NOT_SUPPORTED`.
- `mock_provider: false` returns `LIVE_PROVIDER_NOT_CONFIGURED`.

These are explicit future work items.

## 19. Python SDK

### 19.1 Direct Client

```python
from promptcompiler import PromptCompilerClient

client = PromptCompilerClient("http://127.0.0.1:8765")

analysis = client.analyze(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "repeat\n\nrepeat"}],
)

compiled = client.compile(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "repeat\n\nrepeat"}],
    mode="balanced",
)
```

### 19.2 OpenAI-Like Wrapper

```python
import promptcompiler

wrapped = promptcompiler.wrap(openai_client, base_url="http://127.0.0.1:8765")

response = wrapped.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "@pin Keep CASE-123 exactly."},
        {"role": "user", "content": "repeat\n\nrepeat"},
    ],
    promptcompiler={
        "mode": "balanced",
        "session_id": "support-ticket-123",
        "target_token_budget": 8000,
        "zero_retention": True,
    },
)

print(response.promptcompiler["trace_id"])
```

### 19.3 Wrapper Options

The wrapper accepts:

- `enabled`
- `mode`
- `zero_retention`
- `provider`
- `session_id`
- `target_token_budget`
- `rag_chunks`
- `tools`
- `context_policy`
- `output_policy`
- `tool_policy`
- `cache_policy`
- `task_type`
- `analyze_only`

If `enabled` is false, the wrapper bypasses PromptCompiler.

If `analyze_only` is true, the original provider request is left unchanged but
PromptCompiler metadata is attached to the response.

## 20. CLI

### 20.1 Commands

List models:

```bash
python3 -m promptcompiler.cli models
```

Analyze a prompt file:

```bash
python3 -m promptcompiler.cli analyze prompt.json
```

Compile a prompt file:

```bash
python3 -m promptcompiler.cli compile prompt.json --out optimized.txt
```

### 20.2 CLI Design

The CLI is intentionally small. It is useful for:

- Quick local testing.
- Scripted compile operations.
- Verifying module behavior without the browser.

## 21. Local Storage, Sessions, Metrics, And Cache

### 21.1 Database Path

Default:

```text
.promptcompiler/promptcompiler.sqlite3
```

Override:

```bash
export PROMPTCOMPILER_DB_PATH="/tmp/promptcompiler.sqlite3"
```

### 21.2 Tables

`sessions`:

- `id`
- `provider`
- `model`
- `target_token_budget`
- `current_token_count`
- `compression_mode`
- `zero_retention`
- `created_at`
- `updated_at`
- `compaction_count`

`session_turns`:

- `id`
- `session_id`
- `role`
- `token_count`
- `pinned`
- `content`
- `is_summary`
- `created_at`

`request_traces`:

- `trace_id`
- `endpoint`
- `provider`
- `model`
- `session_id`
- `mode`
- `original_token_count`
- `optimized_token_count`
- `token_reduction_percent`
- `estimated_cost_before_usd`
- `estimated_cost_after_usd`
- `cache_status`
- `evaluation_status`
- `zero_retention`
- `latency_ms`
- `transformations_json`
- `retention_json`
- `created_at`

`compile_cache`:

- `cache_key`
- `response_json`
- `created_at`

### 21.3 Zero Retention

When zero retention is enabled for sessions:

- New turn content is stored as `NULL`.
- Existing turn content for that session is nulled when zero retention is
  activated.
- Token counts and metrics remain.
- Trace rows do not include raw prompt payloads.

### 21.4 Adaptive Compaction

Session compaction triggers when:

- A target token budget exists.
- Total session tokens are at least 70 percent of the target.
- There are older unpinned non-recent turns that can be summarized.

The compactor:

- Keeps the two most recent non-summary turns.
- Keeps pinned turns.
- Deletes older unpinned candidate rows.
- Inserts a summary row.
- Updates session token count and compaction count.

### 21.5 Compile Cache

Compile cache keys include:

- Raw input.
- Model.
- Mode.
- Target budget.
- Dry-run flag.
- Context policy.
- Output policy.
- Tool policy.
- Task type.

This prevents policy changes from reusing an incompatible cached response.

Important retention note:

- Request traces do not store raw prompt payloads.
- Compile cache entries store `response_json` for cache hits.
- A cached compile response can include optimized prompt/message text.
- Users who need strict no-content persistence should leave
  `cache_policy.enabled` false or point `PROMPTCOMPILER_DB_PATH` at disposable
  local storage.

## 22. Web Workbench

### 22.1 Main Panels

The current UI is a workbench, not a marketing landing page.

Panels:

- Topbar and status chip.
- Workbench controls.
- Prompt input.
- Optimized prompt output.
- Analytics.
- Prompt inspector.
- Local history.

### 22.2 Controls

The control panel includes:

- Lint.
- Analyze.
- Compile & Optimize.
- NIM Summarize.
- Model select.
- Model search.
- Sample select.
- Load sample.
- Import prompt file.
- Compression mode.
- Target budget.
- System prompt ref.
- Output format.
- Max words.
- Retrieve top-k.
- Cache prefix checkbox.
- Compile cache checkbox.
- Explain checkbox.
- Dry-run checkbox.

### 22.3 Rendering Responsibilities

The UI renders:

- Empty state.
- Health/model/sample boot status.
- Metrics grid.
- Token breakdown.
- Protected values.
- Compiler changes.
- Lint findings.
- Segment table.
- Diff list.
- Semantic scores.
- Local history.
- Export/download actions.
- Error messages.

### 22.4 Browser Persistence

The UI stores recent compile history in browser local storage under:

```text
promptcompiler.history.v1
```

This is separate from SQLite traces.

### 22.5 External Send Confirmation

The NIM button uses a browser confirmation dialog before sending prompt text to
NVIDIA NIM.

## 23. NVIDIA NIM Integration

### 23.1 Purpose

NIM is optional. The core compiler does not require it.

It is used for:

- Listing live models from NVIDIA.
- Summarizing prompt text through an OpenAI-compatible chat completions API.

### 23.2 Environment Variables

Required for NIM actions:

```bash
NVIDIA_API_KEY="your_key"
```

Optional:

```bash
NVIDIA_NIM_BASE_URL="https://integrate.api.nvidia.com/v1"
PROMPTCOMPILER_DEFAULT_MODEL="nvidia/nemotron-3-nano-30b-a3b"
```

### 23.3 Model Listing

When configured, the app calls:

```text
GET {NVIDIA_NIM_BASE_URL}/models
```

It converts each model into the local model shape:

- `id`
- `provider`
- `label`
- `context_window`
- `tokenizer`
- `notes`

### 23.4 Summarization

The NIM summarize payload uses:

- Low temperature.
- `max_tokens` of 500.
- A system message instructing preservation of IDs, dates, URLs, currency,
  percentages, names, code requirements, schemas, explicit constraints, and
  `@pin` text.

The response is checked against protected entities.

### 23.5 NIM Errors

NIM errors are mapped into actionable server responses:

- Missing key: `NIM_API_KEY_MISSING`.
- Authorization failure: `NIM_AUTHORIZATION_FAILED`.
- Other HTTP/URL issues: `NIM_REQUEST_FAILED`.

## 24. Policies And Registries

### 24.1 Context Policy

Normalized fields:

- `system_prompt_ref`
- `cache_static_prefix`
- `sliding_window_turns`
- `summary_token_budget`
- `retrieval_top_k`

### 24.2 Output Policy

Normalized fields:

- `max_words`
- `format`
- `explain`
- `instruction`

Allowed formats:

- `plain`
- `json`
- `bullets`

Generated instructions can include:

- `Answer in <=N words.`
- `Return JSON only.`
- `Return bullet points only.`
- `No explanation unless asked.`

### 24.3 Built-In System Prompt Refs

| ID | Content |
| --- | --- |
| `concise` | `Be concise.` |
| `json_only` | `Return JSON only.` |
| `bullets_only` | `Return bullet points only.` |
| `no_explanation` | `No explanation unless asked.` |

Unknown refs raise a validation error.

### 24.4 Tool Policy

Current tool policy behavior:

- If `tool_policy.compact` is true, tools are selected and compacted.
- `tool_policy.max_tools` controls maximum selected tools.
- Relevant tools are scored against the latest user query.

### 24.5 Semantic Policy

Normalized fields:

- `scorer`
- `provider`
- `model`
- `dimensions`
- `external`

Default behavior:

- `scorer: lexical`
- Local-only lexical overlap scoring.
- No external network calls.

Phase 1 embedding behavior:

- `scorer: embedding`
- `provider: deterministic`
- Local deterministic vector scoring.
- No external network calls.
- Useful for pruning paraphrased RAG chunks that share meaning but not exact
  wording.

External embedding providers are intentionally not enabled in this phase.

### 24.6 Cache Policy

Current cache policy behavior:

- `cache_policy.enabled` enables compile cache lookup/storage.
- Cache metadata is returned in compile responses.
- Provider cache hints include static prefix cacheability and cache key.

## 25. Privacy, Security, And Retention

### 25.1 Local Default

PromptCompiler runs locally by default. The local deterministic compiler does
not send prompt content to external providers.

### 25.2 External Boundaries

Prompt text can leave the machine only when:

- The user configures `NVIDIA_API_KEY`.
- The user explicitly invokes NIM summarization.
- Future live proxy forwarding is implemented and explicitly configured.

### 25.3 Trace Retention

Request traces store:

- Counts.
- Cost estimates.
- Transformations.
- Cache/evaluation status.
- Retention metadata.

They do not store:

- Raw prompt input.
- Optimized prompt text as a first-class trace field.

Compile cache is separate from request traces. If cache is enabled, the cached
response can include optimized prompt/message text because it is needed to serve
future cache hits.

### 25.4 Session Retention

Session turn content can be stored locally when zero retention is false.

When zero retention is true:

- Raw turn content is not stored.
- Existing content for the session is cleared.
- Counts remain available for metrics.

### 25.5 API Key Hygiene

If an NVIDIA API key is pasted into chat, logs, screenshots, or public files, it
should be revoked and replaced. The project expects keys to live in `.env` or
the shell environment, not in committed source.

## 26. Configuration

### 26.1 `.env` Loading

The app loads a local `.env` file from the repo unless disabled.

Disable local `.env` loading:

```bash
export PROMPTCOMPILER_DISABLE_DOTENV=1
```

### 26.2 Environment Variables

| Variable | Purpose |
| --- | --- |
| `NVIDIA_API_KEY` | Enables NVIDIA NIM model listing and summarization. |
| `NVIDIA_NIM_BASE_URL` | Overrides NIM base URL. |
| `PROMPTCOMPILER_DEFAULT_MODEL` | Overrides default model ID. |
| `PROMPTCOMPILER_DB_PATH` | Overrides SQLite database path. |
| `PROMPTCOMPILER_DISABLE_DOTENV` | Disables local `.env` loading. |

### 26.3 Default Model

Default:

```text
nvidia/llama-3.1-nemotron-nano-8b-v1
```

The default intentionally favors a non-OSS NVIDIA model option when available,
with local registry fallback.

## 27. Testing And Verification

### 27.1 Primary Test Command

```bash
python3 -m unittest discover -s tests
```

For deterministic local test runs that ignore `.env`:

```bash
PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests
```

### 27.2 Test Coverage Map

| Test File | Coverage |
| --- | --- |
| `tests/test_analyzer.py` | Analysis, roles, pins, duplicate plain text. |
| `tests/test_cache.py` | Compile cache key stability. |
| `tests/test_cli.py` | CLI analyze/compile/models behavior. |
| `tests/test_compiler.py` | Compile transforms, modes, dry run, budget, metrics, semantic/minify behavior. |
| `tests/test_entities.py` | Protected entity extraction. |
| `tests/test_lint.py` | Token-waste lint findings. |
| `tests/test_minify.py` | JSON, Markdown, structured input compaction. |
| `tests/test_models_and_api.py` | Model registry, model endpoint, samples, export endpoint. |
| `tests/test_nim.py` | NIM config, payload, SSL handling, auth errors, model listing. |
| `tests/test_policies.py` | Output/context policy normalization and prompt registry. |
| `tests/test_retrieval.py` | Retrieval top-k, token budget, dedupe. |
| `tests/test_routing.py` | Simple/primary model routing decisions. |
| `tests/test_sdk.py` | SDK direct client and wrapper behavior. |
| `tests/test_semantic.py` | Chunking and chunk scoring. |
| `tests/test_server.py` | Health, analyze, compile, NIM error handling. |
| `tests/test_session_context.py` | Compact session context builder. |
| `tests/test_static_assets.py` | Static asset mapping. |
| `tests/test_storage.py` | SQLite traces, metrics, sessions, zero retention. |
| `tests/test_tools.py` | Tool schema compaction and relevant selection. |
| `tests/test_v1_api.py` | Platform API contract, sessions, policies, cache, proxy. |
| `tests/test_web_e2e.py` | Browser UI flow and responsive contract. |

### 27.3 Visual Testing

The browser E2E path is intended to verify:

- The local web server starts.
- The UI loads.
- Main controls are visible.
- Analyze/compile workflow works from the browser.
- Responsive layout does not break at tested sizes.

The Node runner lives at:

```text
tests/web_e2e_runner.mjs
```

### 27.4 Manual Browser Smoke

Manual smoke sequence:

1. Run `python3 -m promptcompiler.server`.
2. Open `http://127.0.0.1:8765`.
3. Load the `Support RMA Chat` sample.
4. Click `Analyze`.
5. Confirm segments and protected values render.
6. Select `Balanced`.
7. Click `Compile & Optimize`.
8. Confirm optimized output differs only when transformations occur.
9. Confirm diff and semantic panels update.
10. Export JSON and verify it contains compile metadata.

### 27.5 Important Regression: Unchanged Output Savings

There is a dedicated compiler regression test to ensure lossless mode does not
claim savings when the output text is unchanged.

Expected behavior:

- Original token count equals optimized token count.
- Tokens saved equals zero.
- Savings ratio equals zero.

## 28. Known Limitations

### 28.1 Tokenizer Accuracy

The tokenizer is approximate. It uses a local regex estimator rather than a
provider-specific tokenizer. Responses label tokenizer accuracy as estimated.

### 28.2 Semantic Depth

Semantic scoring is lexical. It does not currently use embeddings or a
cross-encoder. This is intentional for local-first determinism but limits
paraphrase detection.

### 28.3 Proxy Scope

The proxy currently returns mock provider responses. It does not forward to a
live upstream model provider and does not stream.

### 28.4 NIM Dependency

NIM features depend on a valid NVIDIA API key and account-level model access.
Core local compile features do not depend on NIM.

### 28.5 UI Scope

The UI is a local workbench. It is not yet a multi-project dashboard, hosted
product, or authenticated team app.

### 28.6 Persistence Scope

SQLite is local and simple. It is not built for concurrent multi-user hosted
traffic.

### 28.7 Policy Scope

Prompt refs and policies are currently small built-in sets. There is no external
policy pack system yet.

## 29. Roadmap

### 29.1 Completed Or Mostly Implemented Phases

Phase 1: Dashboard MVP

- Workbench UI.
- Model picker.
- Import/export.
- Analyze/compile flow.
- Segment/diff/semantic displays.
- Local history.

Phase 2: Compression modes and planning

- Lossless, balanced, aggressive modes.
- Target budget.
- Dry run.
- Transformation plan.
- Pinned budget enforcement.
- Risk metadata.

Phase 3: Semantic compression and RAG

- Local chunking.
- Relevance/similarity/novelty/risk scoring.
- RAG redundancy pruning.

Phase 4: Platform API

- `/v1/analyze`.
- `/v1/compile`.
- Provider/model/messages/rag/tools/session/budget/mode/dry-run fields.
- Trace IDs.
- Retention metadata.

Phase 5: Sessions, metrics, cache

- SQLite store.
- Request traces.
- Metrics.
- Session append/context.
- Adaptive compaction.
- Compile cache.

Phase 6: SDK and proxy

- Python SDK.
- OpenAI-like wrapper.
- Analyze-only mode.
- Local OpenAI-compatible mock proxy.
- Trace/token headers.

Token reduction roadmap foundations:

- Prompt refs.
- Output policy.
- Context policy.
- Structured input minify.
- Retrieval budgeting.
- Tool schema compaction.
- Routing hints.
- Cache metadata.
- Lint rules.

### 29.2 Near-Term Product Gaps

- Live provider forwarding in the proxy.
- Streaming proxy responses.
- Provider tokenizer adapters.
- More complete visual regression capture.
- UI for `/v1/metrics`.
- UI for session context management.
- UI for retrieval budgeting.
- More readable trace explorer.

### 29.3 Medium-Term Technical Gaps

- Embedding-backed semantic similarity.
- Better entity extraction for names, schemas, and code symbols.
- Richer policy registry loaded from files.
- Safer tool schema redaction/compaction rules.
- More robust cache invalidation.
- Provider cost table instead of one fixed estimated cost.

### 29.4 Long-Term Product Opportunities

- Enterprise policy packs.
- Prompt budget gates in CI.
- Agent memory compaction service.
- Browser extension.
- Hosted dashboard with local agent bridge.
- Benchmark suite comparing task quality before/after compile.
- Provider spend simulator.

## 30. Glossary

`@pin`:

A marker inside prompt text that tells the compiler to preserve that segment and
avoid compaction/removal.

Balanced mode:

The practical compile mode that applies local compaction and semantic pruning
with moderate risk.

Compile:

The process of transforming a prompt into a smaller, safer, explainable
optimized prompt.

Context policy:

Settings that control reusable system prompt refs, cache prefix hints, and
context/window preferences.

Dry run:

A compile request that returns the proposed plan and proposed output but keeps
the active optimized output unchanged.

Lossless mode:

The safest compile mode. It avoids semantic/history summarization and focuses
on low-risk deterministic changes.

NIM:

NVIDIA Inference Microservices. PromptCompiler can optionally use NVIDIA's
OpenAI-compatible API for model listing and summarization.

Output policy:

Settings that influence response shape, such as JSON-only, bullets-only,
maximum words, and whether explanations are allowed.

Protected entity:

A value such as a URL, date, UUID, currency amount, percentage, ticket ID, or
numeric constraint that should survive compression.

RAG:

Retrieval-augmented generation. In this project it usually means retrieved
context chunks added to the prompt.

Segment:

The internal unit of parsed prompt content. A prompt becomes one or more
segments before analysis and compilation.

Trace:

A local SQLite row storing request-level metrics and transformation metadata
without storing raw prompt payloads.

Zero retention:

A mode where raw prompt/session text is not stored persistently, while metrics
and trace metadata remain available.
