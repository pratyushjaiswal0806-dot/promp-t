# Phase 5 Sessions Metrics And SQLite Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local SQLite-backed sessions, trace metrics, and aggregate metrics APIs while preserving zero-retention behavior.

**Architecture:** Introduce a small SQLite storage boundary used only by the versioned `/v1` APIs. Request traces store metrics and transformation metadata, not raw prompt text. Sessions store turn token counts and optionally content only when zero-retention is disabled; adaptive compaction replaces older unpinned turns with a summary metric row after 70 percent budget utilization.

**Tech Stack:** Python standard library `sqlite3`, current HTTP server, current analyzer/compiler/tokenizer, unittest.

---

### Task 1: SQLite Storage

**Files:**
- Create: `promptcompiler/storage.py`
- Test: `tests/test_storage.py`

- [ ] Add schema creation for `sessions`, `session_turns`, and `request_traces`.
- [ ] Add trace recording and metrics aggregation.
- [ ] Add session append and adaptive compaction at 70 percent of target token budget.
- [ ] Verify zero-retention session turns do not store raw content.

### Task 2: V1 Session And Metrics APIs

**Files:**
- Modify: `promptcompiler/v1.py`
- Modify: `promptcompiler/server.py`
- Test: `tests/test_v1_api.py`

- [ ] Add `append_session_v1`.
- [ ] Add `metrics_v1`.
- [ ] Add `request_trace_v1`.
- [ ] Route `POST /v1/sessions/{session_id}/append`.
- [ ] Route `GET /v1/metrics`.
- [ ] Route `GET /v1/requests/{trace_id}`.

### Task 3: Trace Writes

**Files:**
- Modify: `promptcompiler/v1.py`
- Test: `tests/test_v1_api.py`

- [ ] Record `/v1/analyze` request metrics.
- [ ] Record `/v1/compile` request metrics.
- [ ] Preserve zero-retention metadata in trace rows.

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] Document SQLite DB path and override env var.
- [ ] Document session append and metrics examples.
- [ ] Ignore local `.promptcompiler/` SQLite files.
- [ ] Run focused storage/API tests.
- [ ] Run full test suite and live smoke.
