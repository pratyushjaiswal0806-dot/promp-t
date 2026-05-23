"""Local HTTP server for the PromptCompiler workbench."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any

from .analyzer import analyze_prompt
from .compiler import compile_prompt
from .nim import DEFAULT_NIM_MODEL, NimClient, NimConfigError, NimRequestError, nim_is_configured


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"


def handle_api_request(method: str, path: str, body: bytes) -> tuple[int, str]:
    """Return a status code and JSON body for an API request."""

    try:
        if method == "GET" and path == "/api/health":
            return _json_response(
                200,
                {
                    "ok": True,
                    "nim_configured": nim_is_configured(),
                    "default_model": DEFAULT_NIM_MODEL,
                },
            )

        if method != "POST":
            return _json_response(405, {"error": "Method not allowed"})

        payload = _parse_json_body(body)
        model = str(payload.get("model") or DEFAULT_NIM_MODEL)

        if path == "/api/analyze":
            return _json_response(200, analyze_prompt(str(payload.get("input", "")), model=model))

        if path == "/api/compile":
            return _json_response(200, compile_prompt(str(payload.get("input", "")), model=model))

        if path == "/api/nim/summarize":
            text = str(payload.get("text", ""))
            client = NimClient.from_env()
            return _json_response(200, client.summarize(text, model=model))

        return _json_response(404, {"error": "API route not found"})
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
        return _json_response(502, {"code": "NIM_REQUEST_FAILED", "error": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive boundary
        return _json_response(500, {"error": f"Unexpected server error: {exc}"})


class PromptCompilerHandler(BaseHTTPRequestHandler):
    server_version = "PromptCompiler/0.2"

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._write_api_response(*handle_api_request("GET", self.path, b""))
            return
        self._serve_static()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self._write_api_response(*handle_api_request("POST", self.path, body))

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _write_api_response(self, status: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_static(self) -> None:
        requested = self.path.split("?", 1)[0].lstrip("/")
        if not requested:
            requested = "index.html"

        candidate = (WEB_ROOT / requested).resolve()
        if not str(candidate).startswith(str(WEB_ROOT.resolve())) or not candidate.exists():
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


def _content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "text/javascript; charset=utf-8"
    return "application/octet-stream"


if __name__ == "__main__":
    run()
