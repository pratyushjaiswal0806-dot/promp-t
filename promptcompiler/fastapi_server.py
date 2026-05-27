"""FastAPI server for the PromptCompiler workbench.

Provides the same API surface as the stdlib server with automatic OpenAPI docs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .analyzer import analyze_prompt
from .compiler import CompilePolicyError, compile_prompt
from .models import DEFAULT_NIM_MODEL, list_models
from .nim import NimClient, NimConfigError, NimRequestError, nim_is_configured
from .proxy import ProxyError, proxy_openai_chat_completions
from .samples import list_samples
from .server import WEB_ROOT, _content_type, _static_file_for_request
from .v1 import (
    append_session_v1,
    analyze_v1,
    compile_v1,
    lint_v1,
    metrics_v1,
    request_trace_v1,
    retrieve_v1,
    session_context_v1,
)


app = FastAPI(
    title="PromptCompiler API",
    description="Local-first prompt analysis and deterministic prompt compilation workbench.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "PromptCompiler", "url": "https://github.com/anomalyco/promptcompiler"},
)


# ---------------------------------------------------------------------------
# Health / Models / Samples
# ---------------------------------------------------------------------------


@app.get(
    "/api/health",
    summary="Health check",
    description="Returns server health, NIM configuration status, and the default model.",
    tags=["System"],
)
async def health():
    return {"ok": True, "nim_configured": nim_is_configured(), "default_model": DEFAULT_NIM_MODEL}


@app.get(
    "/api/models",
    summary="List models",
    description="Returns the list of configured models (local registry + NIM live models if configured).",
    tags=["System"],
)
async def models():
    return _models_response()


@app.get(
    "/api/samples",
    summary="List samples",
    description="Returns the list of built-in sample prompts.",
    tags=["System"],
)
async def samples():
    return {"samples": list_samples()}


# ---------------------------------------------------------------------------
# v1 API routes
# ---------------------------------------------------------------------------


@app.get(
    "/v1/metrics",
    summary="Usage metrics",
    description="Returns aggregate usage metrics (request count, tokens, etc.).",
    tags=["v1"],
)
async def v1_metrics(request: Request):
    return metrics_v1(dict(request.query_params))


@app.get(
    "/v1/requests/{trace_id}",
    summary="Get request trace",
    description="Returns a previously recorded request trace by trace ID.",
    tags=["v1"],
)
async def v1_request_trace(trace_id: str):
    trace = request_trace_v1(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Request trace not found")
    return trace


@app.get(
    "/v1/sessions/{session_id}/context",
    summary="Session context",
    description="Returns the accumulated context for a session, including turn history and token usage.",
    tags=["v1"],
)
async def v1_session_context(session_id: str, request: Request):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return session_context_v1(session_id, dict(request.query_params))


@app.post(
    "/v1/analyze",
    summary="Analyze prompt",
    description="Analyze a prompt and return token counts, structural breakdown, and waste findings.",
    tags=["v1"],
)
async def v1_analyze(payload: dict[str, Any]):
    try:
        return analyze_v1(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(
    "/v1/compile",
    summary="Compile prompt",
    description="Compile (compress/summarize/deduplicate) a prompt with the specified mode and budget.",
    tags=["v1"],
)
async def v1_compile(payload: dict[str, Any]):
    try:
        return compile_v1(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except CompilePolicyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post(
    "/v1/retrieve",
    summary="Retrieve RAG chunks",
    description="Retrieve the most relevant RAG chunks for a query using semantic search.",
    tags=["v1"],
)
async def v1_retrieve(payload: dict[str, Any]):
    return retrieve_v1(payload)


@app.post(
    "/v1/lint",
    summary="Lint prompt",
    description="Lint a prompt for token waste and return actionable findings.",
    tags=["v1"],
)
async def v1_lint(payload: dict[str, Any]):
    return lint_v1(payload)


@app.post(
    "/v1/sessions/{session_id}/append",
    summary="Append session turn",
    description="Append a conversation turn to a session with automatic compaction.",
    tags=["v1"],
)
async def v1_session_append(session_id: str, payload: dict[str, Any]):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return append_session_v1(session_id, payload)


@app.post(
    "/v1/proxy/openai/chat/completions",
    summary="OpenAI-compatible proxy",
    description="Proxy a chat completion request through the configured NIM provider.",
    tags=["v1"],
)
async def v1_openai_proxy(payload: dict[str, Any]):
    try:
        response, headers = proxy_openai_chat_completions(payload)
        return JSONResponse(content=response, headers=headers)
    except ProxyError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "error": str(exc)})
    except CompilePolicyError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.error_code, "error": str(exc), "details": exc.details},
        )


# ---------------------------------------------------------------------------
# Legacy /api/ routes
# ---------------------------------------------------------------------------


@app.post(
    "/api/analyze",
    summary="Analyze (legacy)",
    description="Legacy endpoint — analyze a prompt and return structural breakdown.",
    tags=["Legacy"],
)
async def legacy_analyze(payload: dict[str, Any]):
    return analyze_prompt(str(payload.get("input", "")), model=_resolve_model(payload))


@app.post(
    "/api/compile",
    summary="Compile (legacy)",
    description="Legacy endpoint — compile a prompt with compression options.",
    tags=["Legacy"],
)
async def legacy_compile(payload: dict[str, Any]):
    opts = _compile_options(payload)
    return compile_prompt(str(payload.get("input", "")), model=_resolve_model(payload), **opts)


@app.post(
    "/api/export",
    summary="Export (legacy)",
    description="Legacy endpoint — compile and return optimized text alongside full compile result.",
    tags=["Legacy"],
)
async def legacy_export(payload: dict[str, Any]):
    opts = _compile_options(payload)
    result = compile_prompt(str(payload.get("input", "")), model=_resolve_model(payload), **opts)
    return {"model": _resolve_model(payload), "optimized_text": result["optimized_text"], "compile": result}


@app.post(
    "/api/nim/summarize",
    summary="NIM summarize (legacy)",
    description="Legacy endpoint — summarize text using the configured NIM model.",
    tags=["Legacy"],
)
async def legacy_nim_summarize(payload: dict[str, Any]):
    try:
        client = NimClient.from_env()
        return client.summarize(str(payload.get("text", "")), model=_resolve_model(payload))
    except NimConfigError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "NIM_API_KEY_MISSING",
                "error": "Set NVIDIA_API_KEY to enable NVIDIA NIM actions.",
            },
        )


@app.post(
    "/api/generate-prompt",
    summary="Generate prompt (legacy)",
    description="Legacy endpoint — generate an extensive prompt from an idea using the configured NIM model.",
    tags=["Legacy"],
)
async def legacy_generate_prompt(payload: dict[str, Any]):
    idea = str(payload.get("idea") or "").strip()
    if not idea:
        raise HTTPException(status_code=400, detail="idea is required")
    kind = str(payload.get("kind") or "website").strip().lower() or "website"
    try:
        client = NimClient.from_env()
        return client.generate_extensive_prompt(idea, kind=kind, model=_resolve_model(payload))
    except NimConfigError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "NIM_API_KEY_MISSING",
                "error": "Set NVIDIA_API_KEY to enable NVIDIA NIM actions.",
            },
        )


# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------


@app.exception_handler(404)
async def _static_fallback(request: Request, exc: HTTPException):
    if not request.url.path.startswith(("/api/", "/v1/", "/docs", "/redoc", "/openapi.json")):
        candidate = _static_file_for_request(request.url.path)
        if candidate is not None:
            content = candidate.read_bytes()
            return Response(content=content, media_type=_content_type(candidate))
    return HTMLResponse(status_code=404)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(host: str = "127.0.0.1", port: int = 8766) -> None:
    """Start the FastAPI server with uvicorn.

    Parameters
    ----------
    host : str
        Bind address (default 127.0.0.1).
    port : int
        Port number (default 8766).
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


def _resolve_model(payload: dict[str, Any]) -> str:
    return str(payload.get("model") or DEFAULT_NIM_MODEL)


def _compile_options(payload: dict[str, Any]) -> dict[str, Any]:
    budget = payload.get("target_token_budget")
    if budget in {"", None}:
        target_token_budget = None
    else:
        target_token_budget = int(budget)
    return {
        "mode": str(payload.get("mode") or "lossless"),
        "target_token_budget": target_token_budget,
        "dry_run": bool(payload.get("dry_run", False)),
    }


def _models_response() -> dict[str, Any]:
    from .server import _choose_default_model, _dedupe_models

    fallback_models = list_models()
    if not nim_is_configured():
        return {
            "default_model": _choose_default_model(fallback_models),
            "models": fallback_models,
            "source": "local-registry",
        }
    try:
        live_models = NimClient.from_env().list_available_models()
    except (NimConfigError, NimRequestError):
        return {
            "default_model": _choose_default_model(fallback_models),
            "models": fallback_models,
            "source": "local-registry",
        }
    models = _dedupe_models(live_models) or fallback_models
    return {
        "default_model": _choose_default_model(models),
        "models": models,
        "source": "nvidia-live" if live_models else "local-registry",
    }
