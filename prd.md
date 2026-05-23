# PromptCompiler PRD

Version: 0.2  
Date: 2026-05-23  
Status: NIM-first local MVP

## 1. Summary

PromptCompiler is a local-first developer tool for analyzing, budgeting, and safely reducing LLM prompt context. It helps developers see where tokens are going, preserve critical facts, remove deterministic waste, and optionally use NVIDIA NIM APIs for assisted summarization when a free/prototyping key is available.

The MVP is intentionally not an enterprise observability platform. It is a usable prompt budget workbench: paste OpenAI-compatible chat payloads, RAG chunks, tool outputs, or plain text; inspect token allocation; run a safe deterministic compile; and optionally ask a NIM model to summarize compressible segments.

## 2. Problem

LLM applications often send repeated history, verbose tool results, overlapping RAG chunks, stale logs, and old failed attempts. Developers usually cannot see which sections consume the prompt budget or which sections are safe to remove.

This causes:

- Higher input-token cost.
- More latency.
- Context-window pressure.
- Important instructions and facts being crowded out.
- Unsafe ad hoc summarization that silently loses meaning.

## 3. Product Goal

Build a tool that feels like a bundle analyzer for LLM context:

- Show prompt token usage by segment and role.
- Identify duplicate and high-waste sections.
- Preserve pinned and entity-heavy content.
- Produce an optimized prompt with a readable change report.
- Work without paid model APIs.
- Add NVIDIA NIM as an optional accelerator, not a hard dependency.

## 4. Target User

The first user is an AI application developer building agents, copilots, support bots, or RAG workflows. They need a local tool they can run while debugging prompts and before adding production infrastructure.

## 5. MVP Scope

### 5.1 Analyze

Users can paste:

- OpenAI-compatible JSON with `messages`.
- A raw text prompt.
- Tool output, logs, or RAG chunks as plain text.

The app returns:

- Estimated tokens.
- Tokens by segment type.
- Tokens by role.
- Largest segments.
- Duplicate groups.
- Protected entities.
- Compression opportunity score.

### 5.2 Deterministic Compile

The deterministic compiler must:

- Preserve `@pin` segments exactly.
- Preserve URLs, dates, IDs, currency values, and numeric thresholds.
- Remove exact duplicate unpinned segments.
- Collapse repeated adjacent log lines.
- Compact oversized tool/log segments with an explicit omitted-line marker.
- Return the optimized prompt and a change report.

### 5.3 NVIDIA NIM Assisted Mode

If `NVIDIA_API_KEY` is configured, the app can call NVIDIA NIM through an OpenAI-compatible API shape.

NIM assisted mode may:

- Summarize old unpinned conversation turns.
- Summarize verbose tool output.
- Run a lightweight preservation check.

NIM assisted mode must not:

- Modify pinned segments.
- Replace deterministic compile as the default path.
- Be required for the app to run.
- Send data unless the user explicitly clicks a NIM action.

### 5.4 UI

The first screen is the workbench, not a marketing page.

It includes:

- Input editor.
- Analyze and Compile controls.
- Summary metrics.
- Segment table.
- Original vs optimized output.
- Change report.
- NIM status and optional NIM action.

## 6. Non-Goals

The MVP will not include:

- User accounts.
- RBAC.
- Billing.
- ClickHouse telemetry.
- Redis semantic cache.
- Organization quotas.
- Production proxy mode.
- LangChain or LlamaIndex integrations.
- LLM-as-judge evaluation loops.
- Guaranteed semantic equivalence.

## 7. Success Criteria

The MVP is successful when:

- It runs locally with no paid API key.
- It analyzes a pasted prompt in under one second for typical debugging payloads.
- It preserves all pinned content exactly.
- It removes exact duplicates safely.
- It shows a useful token-savings report.
- It can optionally call NVIDIA NIM when `NVIDIA_API_KEY` is present.
- It has tests covering parsing, pin preservation, duplicate removal, entity extraction, token estimation, and NIM request construction.

## 8. Rollout

### Phase 1: Local Analyzer

- Prompt parser.
- Segment classifier.
- Token estimator.
- Entity extractor.
- Analyzer API.
- Workbench UI.

### Phase 2: Deterministic Compiler

- Pin enforcement.
- Duplicate removal.
- Log compaction.
- Compile API.
- Diff output and report.

### Phase 3: NIM Assisted Mode

- NIM client.
- NIM status endpoint.
- Optional summarization action.
- Preservation warning for risky input.

### Phase 4: Project Hardening

- More sample payloads.
- Better token model registry.
- Import/export JSON.
- CLI wrapper.

## 9. Current Implementation Status

Implemented:

- Local analyzer.
- Deterministic compiler.
- Segment-level diff.
- Built-in model registry.
- Built-in samples.
- Browser import/export.
- CLI analyze/compile/models commands.
- Optional NVIDIA NIM summarization.
- Live NVIDIA model picker through the account API key.
- NIM TLS certificate handling for local Python installs.
- Protected-entity preservation warnings for NIM summaries.

Still future work:

- Exact provider tokenizer integration.
- Hosted multi-user deployment.
- Production proxy mode.
- Framework integrations.
- Semantic cache.
- LLM-as-judge evaluation dashboard.
