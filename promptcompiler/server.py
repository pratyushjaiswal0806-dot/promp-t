"""Local HTTP server for the PromptCompiler workbench."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

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


def handle_api_request(method: str, path: str, body: bytes) -> tuple[int, str]:
    """Return a status code and JSON body for an API request."""

    parsed_path = urlparse(path)
    route = parsed_path.path
    query = _query_params(parsed_path.query)

    try:
        if method == "GET" and route == "/api/health":
            return _json_response(
                200,
                {
                    "ok": True,
                    "nim_configured": nim_is_configured(),
                    "default_model": DEFAULT_NIM_MODEL,
                },
            )

        if method == "GET" and route == "/api/models":
            return _json_response(200, _models_response())

        if method == "GET" and route == "/api/samples":
            return _json_response(200, {"samples": list_samples()})

        if method == "GET" and route == "/v1/metrics":
            return _json_response(200, metrics_v1(query))

        if method == "GET" and route.startswith("/v1/requests/"):
            trace_id = route.removeprefix("/v1/requests/").strip("/")
            trace = request_trace_v1(trace_id)
            if trace is None:
                return _json_response(404, {"error": "Request trace not found"})
            return _json_response(200, trace)

        if method == "GET" and route.startswith("/v1/sessions/") and route.endswith("/context"):
            session_id = route.removeprefix("/v1/sessions/").removesuffix("/context").strip("/")
            if not session_id:
                return _json_response(400, {"error": "session_id is required"})
            return _json_response(200, session_context_v1(session_id, query))

        if method != "POST":
            return _json_response(405, {"error": "Method not allowed"})

        if route == "/v1/proxy/openai/chat/completions":
            status, response, _headers = _handle_openai_proxy_request(body)
            return status, response

        payload = _parse_json_body(body)
        model = str(payload.get("model") or DEFAULT_NIM_MODEL)
        compile_options = _compile_options(payload)

        if route == "/api/analyze":
            return _json_response(200, analyze_prompt(str(payload.get("input", "")), model=model))

        if route == "/api/compile":
            return _json_response(
                200,
                compile_prompt(str(payload.get("input", "")), model=model, **compile_options),
            )

        if route == "/api/export":
            result = compile_prompt(str(payload.get("input", "")), model=model, **compile_options)
            return _json_response(
                200,
                {
                    "model": model,
                    "optimized_text": result["optimized_text"],
                    "compile": result,
                },
            )

        if route == "/api/nim/summarize":
            text = str(payload.get("text", ""))
            client = NimClient.from_env()
            return _json_response(200, client.summarize(text, model=model))

        if route == "/api/generate-prompt":
            idea = str(payload.get("idea") or "").strip()
            if not idea:
                return _json_response(400, {"error": "idea is required"})
            kind = str(payload.get("kind") or "website").strip().lower() or "website"
            client = NimClient.from_env()
            return _json_response(
                200,
                client.generate_extensive_prompt(idea, kind=kind, model=model),
            )

        if route == "/v1/analyze":
            return _json_response(200, analyze_v1(payload))

        if route == "/v1/compile":
            return _json_response(200, compile_v1(payload))

        if route == "/v1/retrieve":
            return _json_response(200, retrieve_v1(payload))

        if route == "/v1/lint":
            return _json_response(200, lint_v1(payload))

        if route.startswith("/v1/sessions/") and route.endswith("/append"):
            session_id = route.removeprefix("/v1/sessions/").removesuffix("/append").strip("/")
            if not session_id:
                return _json_response(400, {"error": "session_id is required"})
            return _json_response(200, append_session_v1(session_id, payload))

        return _json_response(404, {"error": "API route not found"})
    except CompilePolicyError as exc:
        payload = {"code": exc.error_code, "error": str(exc)}
        if exc.details:
            payload["details"] = exc.details
        return _json_response(exc.status_code, payload)
    except ValueError as exc:
        return _json_response(400, {"error": str(exc)})
    except NimConfigError:
        return _json_response(
            400,
            {
                "code": "NIM_API_KEY_MISSING",
                "error": "Set NVIDIA_API_KEY to enable NVIDIA NIM actions.",
            },
        )
    except NimRequestError as exc:
        status = exc.status_code if 400 <= exc.status_code <= 599 else 502
        payload: dict[str, Any] = {"code": exc.error_code, "error": str(exc)}
        if exc.detail:
            payload["detail"] = exc.detail
        return _json_response(status, payload)
    except Exception as exc:  # pragma: no cover - defensive boundary
        return _json_response(500, {"error": f"Unexpected server error: {exc}"})


class PromptCompilerHandler(BaseHTTPRequestHandler):
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


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), PromptCompilerHandler)
    print(f"PromptCompiler running at http://{host}:{port}")
    server.serve_forever()


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


def _json_response(status: int, payload: dict[str, Any]) -> tuple[int, str]:
    return status, json.dumps(payload, ensure_ascii=True, sort_keys=True)


def _json_response_with_headers(
    status: int,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> tuple[int, str, dict[str, str]]:
    return status, json.dumps(payload, ensure_ascii=True, sort_keys=True), headers


def _handle_openai_proxy_request(body: bytes) -> tuple[int, str, dict[str, str]]:
    try:
        payload = _parse_json_body(body)
        response, headers = proxy_openai_chat_completions(payload)
        return _json_response_with_headers(200, response, headers)
    except ProxyError as exc:
        return _json_response_with_headers(
            exc.status_code,
            {"code": exc.code, "error": str(exc)},
            {},
        )
    except CompilePolicyError as exc:
        payload = {"code": exc.error_code, "error": str(exc)}
        if exc.details:
            payload["details"] = exc.details
        return _json_response_with_headers(exc.status_code, payload, {})
    except ValueError as exc:
        return _json_response_with_headers(400, {"error": str(exc)}, {})
    except Exception as exc:  # pragma: no cover - defensive boundary
        return _json_response_with_headers(
            500,
            {"error": f"Unexpected server error: {exc}"},
            {},
        )


def _query_params(query: str) -> dict[str, str]:
    parsed = parse_qs(query, keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items() if values}


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


if __name__ == "__main__":
    run()
