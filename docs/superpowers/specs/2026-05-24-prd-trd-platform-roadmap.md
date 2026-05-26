# PRD/TRD Platform Roadmap

## Goal

Move PromptCompiler from the current local-first prompt workbench toward the production-grade platform described in `/Users/deepakkudi23/Desktop/prd.md` and `/Users/deepakkudi23/Desktop/trd.md`, while keeping each phase shippable, testable, and reviewable on its own.

## Source Of Truth

The Desktop PRD/TRD describe the target product: a developer infrastructure platform for LLM context optimization, observability, safe compression, semantic cache, evaluation, SDK/proxy integration, and enterprise controls.

The current repo is a smaller local app: Python standard-library server, static HTML/CSS/JavaScript, deterministic analyzer/compiler, optional NVIDIA NIM support, and browser regression tests. The roadmap keeps that app useful while gradually adding the PRD/TRD surface.

## Development Rules

- Ask for user approval before starting each phase.
- Do not start the next phase until the current phase has implementation, verification, and a completion report.
- Prefer small, testable modules over a big rewrite.
- Keep the app local-first until the user approves external infrastructure.
- Treat NIM and other model calls as explicit user-triggered actions.
- Preserve `@pin` content exactly in every compression mode.
- Keep zero-retention behavior available whenever storage or telemetry is introduced.
- Use the Desktop PRD/TRD as product intent, but defer enterprise infrastructure until the local product shape is proven.

## Phase 0: Alignment And Roadmap

Status: complete.

Purpose:

- Capture the PRD/TRD target as a repo-local roadmap.
- Define phase boundaries, acceptance criteria, and manual steps.
- Prepare the Phase 1 implementation plan.

Deliverables:

- `docs/superpowers/specs/2026-05-24-prd-trd-platform-roadmap.md`
- `docs/superpowers/plans/2026-05-24-phase-1-dashboard-mvp.md`

Acceptance criteria:

- The roadmap distinguishes local workbench work from full platform work.
- Each phase has a clear scope, verification plan, and manual step list.
- Phase 1 can begin after explicit user approval.

Manual steps:

- None.

## Phase 1: Website And Dashboard MVP

Purpose:

Make the visible website match the practical PRD/TRD workbench experience while staying inside the current static UI and Python server architecture.

Scope:

- Dashboard-style layout with request/workbench orientation.
- Analyze workflow visible in the UI.
- Compile workflow visible in the UI.
- Model picker/search using `/api/models`.
- Built-in samples UI using `/api/samples`.
- Local prompt file import.
- Text export and full JSON export.
- Segment table with type, role, tokens, pinned status, and protected values.
- Diff/change viewer using compile `diff` and `changes`.
- Prompt analytics with token counts, savings, component breakdown, and protected values.
- Local browser history using `localStorage`.
- NIM summarization entry point with confirmation before external calls.
- Mobile-responsive dashboard layout.

Out of scope:

- Next.js migration.
- FastAPI migration.
- Auth, RBAC, quotas, Redis, PostgreSQL/Supabase, ClickHouse.
- SDK/proxy integration.
- True embedding-based semantic scoring.

Acceptance criteria:

- A user can load a sample, analyze it, compile it, inspect segments/diff, export optimized text, export JSON, and reload a recent local history item.
- The UI clearly shows server/NIM status and does not send text to NIM without confirmation.
- Browser E2E covers the main workbench flow and mobile overflow.
- `PROMPTCOMPILER_DISABLE_DOTENV=1 python3 -m unittest discover -s tests` passes.

Manual steps:

- Open the local URL after implementation.
- Try one sample and one pasted prompt.
- Confirm the dashboard feels aligned with the PRD/TRD direction.

## Phase 2: Compression Modes And Planning

Purpose:

Implement the PRD/TRD compression mode foundation without external infrastructure.

Scope:

- Extend compile request handling with `mode`, `target_token_budget`, and `dry_run`.
- Add `lossless`, `balanced`, and `aggressive` modes.
- Return a transformation plan before or alongside optimized output.
- Enforce pinned budget quota with default 25 percent cap.
- Add local cost-benefit metadata.
- Add safer local compaction for tool outputs, JSON payloads, repeated logs, conversation history, and RAG-like blocks.
- Return warnings when a target budget cannot be met safely.

Out of scope:

- External embeddings.
- Redis semantic cache.
- LLM-as-judge evaluation.
- Provider proxy forwarding.

Acceptance criteria:

- Existing deterministic behavior remains the default lossless path.
- Balanced/aggressive modes produce more savings on long tool/history/RAG prompts while preserving protected entities.
- Dry run returns planned transformations without requiring the UI to treat the result as active output.
- Pinned quota violations return structured error metadata.

Manual steps:

- Optional: provide a few real bloated prompts to test against.

## Phase 3: Semantic Compression And RAG Optimization

Purpose:

Add PRD/TRD semantic behavior in a controlled, optional way.

Scope:

- Semantic chunking with sliding windows and sentence-aware splitting.
- Query-aware chunk scoring.
- Redundancy and novelty scores.
- RAG chunk pruning with source/citation preservation.
- Optional NIM-assisted summarization for older history and verbose tool output.
- Preservation validation after semantic compression.
- Risk scores and retention warnings.

Out of scope:

- Production A/B evaluation.
- Full nDCG benchmark dashboard.
- Redis cache.

Acceptance criteria:

- RAG-like prompts can be pruned with tracked removed chunk IDs and preserved citations.
- NIM semantic summarization is opt-in and guarded by confirmation.
- Semantic results are rejected or warned when protected values are missing.

Manual steps:

- Add or confirm `NVIDIA_API_KEY` in `.env` if model-assisted summarization is desired.
- Review semantic compression examples for quality.

## Phase 4: Platform API Foundation

Purpose:

Introduce the TRD-style API shape while preserving the current local UI.

Scope:

- Add `/v1/analyze` and `/v1/compile`.
- Normalize provider, model, messages, RAG chunks, tools, session ID, target budget, mode, and dry-run fields.
- Add trace IDs.
- Add provider-router-first internal payload objects.
- Add tokenizer confidence metadata.
- Add zero-retention flags in responses and policy handling.
- Keep old `/api/*` routes as compatibility wrappers for the website.

Out of scope:

- API-key auth.
- Storage-backed traces.
- Proxy forwarding.

Acceptance criteria:

- `/v1/*` contract tests cover request and response shapes from the Desktop TRD.
- The existing website continues to work.
- API responses expose enough metadata for future storage, metrics, and proxy work.

Manual steps:

- Decide whether the API should stay standard-library Python for another phase or move to FastAPI.

## Phase 5: Sessions, Metrics, And Cache

Purpose:

Add stateful platform behavior from the PRD/TRD.

Scope:

- Session append API.
- Session compaction at 70 percent of target token budget.
- Request trace metadata.
- Metrics endpoint.
- Local storage backend abstraction.
- Optional Redis cache adapter.
- Optional SQLite or PostgreSQL/Supabase trace store.
- Zero-retention behavior for raw text.

Out of scope:

- Enterprise RBAC.
- ClickHouse high-volume telemetry.
- LLM-as-judge worker.

Acceptance criteria:

- A session can accumulate turns and trigger compaction.
- Metrics show original tokens, optimized tokens, savings, mode usage, and cache status.
- Zero-retention mode stores no raw prompt text.

Manual steps:

- Choose local SQLite, local Postgres, or Supabase for trace/session storage.
- Install/run Redis only if cache work is approved.

## Phase 6: SDK And HTTP Proxy

Purpose:

Make PromptCompiler integration-ready.

Scope:

- Python SDK wrapper skeleton.
- Analyze-only and compile modes in SDK calls.
- Provider-compatible HTTP proxy route.
- Trace metadata headers.
- Streaming support decision.
- Integration docs with examples.

Out of scope:

- LangChain and LlamaIndex integrations unless approved as sub-phases.
- Full auth/RBAC unless Phase 7 starts first.

Acceptance criteria:

- A small OpenAI-compatible client example can call through PromptCompiler.
- Proxy preserves provider-compatible request/response shape in a smoke test.
- Trace metadata is visible without leaking secrets.

Manual steps:

- Provide provider API keys for live proxy tests, or approve mocked-only tests.

## Phase 7: Evaluation And Enterprise Controls

Purpose:

Add the higher-risk production platform capabilities from the PRD/TRD.

Scope:

- Layer 1 retention checks.
- Optional Layer 2 sampled output-quality evaluation.
- API-key auth.
- Basic organization/project policies.
- Quotas.
- Audit events.
- Enterprise settings UI.
- ClickHouse or equivalent telemetry decision.

Acceptance criteria:

- Evaluation can run in a controlled sample mode.
- Zero-retention disables unsafe evaluation paths by default.
- API keys are hashed at rest if storage is enabled.
- Admin settings can adjust mode defaults, pinned budget cap, and evaluation sampling.

Manual steps:

- Choose deployment/storage infrastructure.
- Provide judge/model provider credentials if live evaluation is approved.
- Decide whether to deploy locally, cloud-hosted, or both.

## Manual Setup Summary

No manual setup is needed for Phase 0 or Phase 1 beyond opening the local website.

Manual setup likely starts in Phase 3:

- `NVIDIA_API_KEY` in `.env` for optional NIM semantic summarization.

Manual setup likely starts in Phase 5:

- Storage choice: SQLite, local Postgres, or Supabase.
- Optional Redis if semantic cache/session locks are approved.

Manual setup likely starts in Phase 6:

- Provider API keys for live proxy tests.

Manual setup likely starts in Phase 7:

- Auth/storage/telemetry infrastructure choices.

## Current Recommendation

Start with Phase 1 after Phase 0 approval is complete. It provides the biggest visible improvement and keeps the architecture stable while the product experience is shaped around the PRD/TRD.
