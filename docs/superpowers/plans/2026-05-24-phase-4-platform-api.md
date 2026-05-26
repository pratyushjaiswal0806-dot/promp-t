# Phase 4 Platform API Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TRD-style `/v1/analyze` and `/v1/compile` APIs without breaking the current website or `/api/*` routes.

**Architecture:** Keep the current standard-library Python server. Add a focused v1 contract module that normalizes provider/model/messages/RAG/tools/session/policy fields into the existing local analyzer/compiler, then maps results into platform-shaped responses with trace IDs, tokenizer metadata, and zero-retention metadata.

**Tech Stack:** Python standard library HTTP server, existing analyzer/compiler/parser/tokenizer modules, unittest contract tests.

---

### Task 1: Contract Tests

**Files:**
- Create: `tests/test_v1_api.py`
- Modify: `tests/test_server.py`

- [ ] Add failing tests for `POST /v1/analyze`.
- [ ] Add failing tests for `POST /v1/compile`.
- [ ] Assert legacy `/api/compile` remains compatible.

### Task 2: V1 Normalization Module

**Files:**
- Create: `promptcompiler/v1.py`

- [ ] Add `NormalizedV1Request` and `normalize_v1_request`.
- [ ] Normalize `provider`, `model`, `messages`, `rag_chunks`, `tools`, `session_id`, `target_token_budget`, `mode`, `dry_run`, and zero-retention policy.
- [ ] Generate in-memory `trace_id` values with `tr_` prefix.
- [ ] Return tokenizer metadata with `tokenizer_accuracy: estimated`.

### Task 3: V1 Response Mapping

**Files:**
- Modify: `promptcompiler/v1.py`

- [ ] Add `analyze_v1`.
- [ ] Add `compile_v1`.
- [ ] Map existing analyzer/compiler output into TRD-shaped response fields.
- [ ] Include retention metadata showing raw payloads are not stored.

### Task 4: Server Routing

**Files:**
- Modify: `promptcompiler/server.py`

- [ ] Route `POST /v1/analyze` to `analyze_v1`.
- [ ] Route `POST /v1/compile` to `compile_v1`.
- [ ] Ensure `GET /v1/*` returns JSON method errors instead of static file behavior.
- [ ] Preserve existing `/api/*` behavior.

### Task 5: Docs And Verification

**Files:**
- Modify: `README.md`

- [ ] Document `/v1/analyze` and `/v1/compile` examples.
- [ ] Run focused tests.
- [ ] Run full suite.
- [ ] Run local curl smoke against the live server.
