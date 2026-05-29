"""FastAPI server for the PromptCompiler workbench.

Provides the full API surface with automatic OpenAPI docs and static file serving.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .analyzer import analyze_prompt
from .compiler import CompilePolicyError, compile_prompt
from .models import DEFAULT_NIM_MODEL, list_models
from .nim import NimClient, NimConfigError, NimRequestError, nim_is_configured
from .proxy import ProxyError, proxy_openai_chat_completions
from .samples import list_samples
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


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"


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


class PromptCompilerHandler(BaseHTTPRequestHandler):
    """Stdlib HTTP handler for testing.

    Mirrors the FastAPI route logic using :func:`handle_api_request_with_headers`.
    """
    server_version = "PromptCompiler/0.2"

    def do_GET(self) -> None:
        if self.path.startswith("/api/") or self.path.startswith("/v1/"):
            self._write_api_response(*handle_api_request_with_headers("GET", self.path, b""))
            return
        self._serve_static()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self._write_api_response(*handle_api_request_with_headers("POST", self.path, body))

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _write_api_response(
        self,
        status: int,
        body: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_static(self) -> None:
        candidate = _static_file_for_request(self.path)
        if candidate is None:
            self.send_error(404)
            return
        content = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _content_type(candidate))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


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


def _content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "text/javascript; charset=utf-8"
    if suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def _static_file_for_request(path: str) -> Path | None:
    requested = path.split("?", 1)[0].lstrip("/")
    if not requested:
        requested = "index.html"
    if requested == "favicon.ico":
        requested = "favicon.svg"

    candidate = (WEB_ROOT / requested).resolve()
    web_root = WEB_ROOT.resolve()
    try:
        candidate.relative_to(web_root)
    except ValueError:
        return None
    if not candidate.exists():
        if not Path(requested).suffix:
            index_file = WEB_ROOT / "index.html"
            return index_file if index_file.exists() else None
        return None
    if candidate.is_dir():
        index_file = candidate / "index.html"
        return index_file if index_file.exists() else None
    return candidate


def _choose_default_model(models: list[dict[str, Any]]) -> str:
    configured = DEFAULT_NIM_MODEL
    if any(model.get("id") == configured for model in models):
        return configured
    for model in models:
        model_id = str(model.get("id", ""))
        if not model_id.startswith("openai/gpt-oss"):
            return model_id
    if models:
        return str(models[0].get("id"))
    return configured


def _dedupe_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for model in models:
        model_id = str(model.get("id", ""))
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        unique.append(model)
    return unique


def _models_response() -> dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Test helpers (stdlib HTTP handler equivalents)
# ---------------------------------------------------------------------------


class _QueryParams:
    @staticmethod
    def parse(query: str) -> dict[str, str]:
        parsed = parse_qs(query, keep_blank_values=False)
        return {key: values[-1] for key, values in parsed.items() if values}


def handle_api_request(method: str, path: str, body: bytes) -> tuple[int, str]:
    """Return a status code and JSON body for an API request.

    Used by tests to exercise the API logic without starting a server.
    """
    parsed_path = urlparse(path)
    route = parsed_path.path
    query = _QueryParams.parse(parsed_path.query)

    try:
        if method == "GET" and route == "/api/health":
            return 200, json.dumps(
                {"ok": True, "nim_configured": nim_is_configured(), "default_model": DEFAULT_NIM_MODEL},
                ensure_ascii=True, sort_keys=True,
            )

        if method == "GET" and route == "/api/models":
            return 200, json.dumps(_models_response(), ensure_ascii=True, sort_keys=True)

        if method == "GET" and route == "/api/samples":
            return 200, json.dumps({"samples": list_samples()}, ensure_ascii=True, sort_keys=True)

        if method == "GET" and route == "/v1/metrics":
            return 200, json.dumps(metrics_v1(query), ensure_ascii=True, sort_keys=True)

        if method == "GET" and route.startswith("/v1/requests/"):
            trace_id = route.removeprefix("/v1/requests/").strip("/")
            trace = request_trace_v1(trace_id)
            if trace is None:
                return 404, json.dumps({"error": "Request trace not found"}, ensure_ascii=True, sort_keys=True)
            return 200, json.dumps(trace, ensure_ascii=True, sort_keys=True)

        if method == "GET" and route.startswith("/v1/sessions/") and route.endswith("/context"):
            session_id = route.removeprefix("/v1/sessions/").removesuffix("/context").strip("/")
            if not session_id:
                return 400, json.dumps({"error": "session_id is required"}, ensure_ascii=True, sort_keys=True)
            return 200, json.dumps(session_context_v1(session_id, query), ensure_ascii=True, sort_keys=True)

        if method != "POST":
            return 405, json.dumps({"error": "Method not allowed"}, ensure_ascii=True, sort_keys=True)

        payload = _parse_json_body(body)
        model = str(payload.get("model") or DEFAULT_NIM_MODEL)
        compile_options = _compile_options(payload)

        if route == "/api/analyze":
            return 200, json.dumps(analyze_prompt(str(payload.get("input", "")), model=model), ensure_ascii=True, sort_keys=True)

        if route == "/api/compile":
            return 200, json.dumps(
                compile_prompt(str(payload.get("input", "")), model=model, **compile_options),
                ensure_ascii=True, sort_keys=True,
            )

        if route == "/api/export":
            result = compile_prompt(str(payload.get("input", "")), model=model, **compile_options)
            return 200, json.dumps(
                {"model": model, "optimized_text": result["optimized_text"], "compile": result},
                ensure_ascii=True, sort_keys=True,
            )

        if route == "/api/nim/summarize":
            text = str(payload.get("text", ""))
            client = NimClient.from_env()
            return 200, json.dumps(client.summarize(text, model=model), ensure_ascii=True, sort_keys=True)

        if route == "/api/generate-prompt":
            idea = str(payload.get("idea") or "").strip()
            if not idea:
                return 400, json.dumps({"error": "idea is required"}, ensure_ascii=True, sort_keys=True)
            kind = str(payload.get("kind") or "website").strip().lower() or "website"
            client = NimClient.from_env()
            return 200, json.dumps(
                client.generate_extensive_prompt(idea, kind=kind, model=model),
                ensure_ascii=True, sort_keys=True,
            )

        if route == "/v1/analyze":
            return 200, json.dumps(analyze_v1(payload), ensure_ascii=True, sort_keys=True)

        if route == "/v1/compile":
            return 200, json.dumps(compile_v1(payload), ensure_ascii=True, sort_keys=True)

        if route == "/v1/retrieve":
            return 200, json.dumps(retrieve_v1(payload), ensure_ascii=True, sort_keys=True)

        if route == "/v1/lint":
            return 200, json.dumps(lint_v1(payload), ensure_ascii=True, sort_keys=True)

        if route.startswith("/v1/sessions/") and route.endswith("/append"):
            session_id = route.removeprefix("/v1/sessions/").removesuffix("/append").strip("/")
            if not session_id:
                return 400, json.dumps({"error": "session_id is required"}, ensure_ascii=True, sort_keys=True)
            return 200, json.dumps(append_session_v1(session_id, payload), ensure_ascii=True, sort_keys=True)

        return 404, json.dumps({"error": "API route not found"}, ensure_ascii=True, sort_keys=True)
    except CompilePolicyError as exc:
        response: dict[str, Any] = {"code": exc.error_code, "error": str(exc)}
        if exc.details:
            response["details"] = exc.details
        return exc.status_code, json.dumps(response, ensure_ascii=True, sort_keys=True)
    except ValueError as exc:
        return 400, json.dumps({"error": str(exc)}, ensure_ascii=True, sort_keys=True)
    except NimConfigError:
        return 400, json.dumps(
            {"code": "NIM_API_KEY_MISSING", "error": "Set NVIDIA_API_KEY to enable NVIDIA NIM actions."},
            ensure_ascii=True, sort_keys=True,
        )
    except NimRequestError as exc:
        status = exc.status_code if 400 <= exc.status_code <= 599 else 502
        response: dict[str, Any] = {"code": exc.error_code, "error": str(exc)}
        if exc.detail:
            response["detail"] = exc.detail
        return status, json.dumps(response, ensure_ascii=True, sort_keys=True)
    except Exception as exc:
        return 500, json.dumps({"error": f"Unexpected server error: {exc}"}, ensure_ascii=True, sort_keys=True)


def handle_api_request_with_headers(
    method: str,
    path: str,
    body: bytes,
) -> tuple[int, str, dict[str, str]]:
    """Return a status code, JSON body, and extra response headers."""
    parsed_path = urlparse(path)
    route = parsed_path.path

    if method == "POST" and route == "/v1/proxy/openai/chat/completions":
        return _handle_openai_proxy_request(body)

    status, response = handle_api_request(method, path, body)
    return status, response, {}


def _parse_json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON body") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON body must be an object")
    return parsed


def _handle_openai_proxy_request(body: bytes) -> tuple[int, str, dict[str, str]]:
    try:
        payload = _parse_json_body(body)
        response, headers = proxy_openai_chat_completions(payload)
        return 200, json.dumps(response, ensure_ascii=True, sort_keys=True), headers
    except ProxyError as exc:
        response: dict[str, Any] = {"code": exc.code, "error": str(exc)}
        return exc.status_code, json.dumps(response, ensure_ascii=True, sort_keys=True), {}
    except CompilePolicyError as exc:
        response: dict[str, Any] = {"code": exc.error_code, "error": str(exc)}
        if exc.details:
            response["details"] = exc.details
        return exc.status_code, json.dumps(response, ensure_ascii=True, sort_keys=True), {}
    except ValueError as exc:
        return 400, json.dumps({"error": str(exc)}, ensure_ascii=True, sort_keys=True), {}
    except Exception as exc:
        return 500, json.dumps({"error": f"Unexpected server error: {exc}"}, ensure_ascii=True, sort_keys=True), {}
