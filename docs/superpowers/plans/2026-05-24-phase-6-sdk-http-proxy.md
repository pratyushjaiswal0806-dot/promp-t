# Phase 6 SDK And HTTP Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PromptCompiler usable from coding agents through a small Python SDK and an OpenAI-compatible HTTP proxy route.

**Architecture:** Add a dependency-free SDK module that calls the local `/v1` APIs and a proxy helper that compiles OpenAI chat-completion messages before returning a provider-shaped mocked response. Keep real provider forwarding out of scope for this phase; the proxy exposes trace metadata headers and body metadata for later live forwarding.

**Tech Stack:** Python standard library `urllib`, current `/v1` API layer, standard-library HTTP server, unittest.

---

### Task 1: SDK Contract Tests

**Files:**
- Create: `tests/test_sdk.py`
- Modify: `promptcompiler/__init__.py`

- [x] Add tests for `PromptCompilerClient.analyze`.
- [x] Add tests for `PromptCompilerClient.compile`.
- [x] Add tests for `promptcompiler.wrap(fake_openai_client)`.

### Task 2: Proxy Contract Tests

**Files:**
- Modify: `tests/test_v1_api.py`
- Modify: `tests/test_server.py`

- [x] Add tests for `POST /v1/proxy/openai/chat/completions`.
- [x] Verify OpenAI-compatible response shape.
- [x] Verify `X-PromptCompiler-Trace`, original-token, and optimized-token headers.
- [x] Verify streaming requests fail clearly for now.

### Task 3: SDK Module

**Files:**
- Create: `promptcompiler/sdk.py`
- Modify: `promptcompiler/__init__.py`

- [x] Implement `PromptCompilerClient`.
- [x] Implement `wrap(client, ...)`.
- [x] Preserve an OpenAI-like `client.chat.completions.create(...)` call path.

### Task 4: Proxy Module And Routing

**Files:**
- Create: `promptcompiler/proxy.py`
- Modify: `promptcompiler/server.py`

- [x] Implement `proxy_openai_chat_completions`.
- [x] Add `handle_api_request_with_headers` while preserving existing `handle_api_request`.
- [x] Add route for `/v1/proxy/openai/chat/completions`.
- [x] Add trace headers in real HTTP responses.

### Task 5: Docs And Verification

**Files:**
- Modify: `README.md`

- [x] Document SDK examples.
- [x] Document proxy curl example and mocked-provider behavior.
- [x] Run focused SDK/proxy tests.
- [x] Run full suite.
- [x] Restart local server and live-smoke proxy route.
