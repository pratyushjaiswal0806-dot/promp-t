"""Provider-compatible proxy helpers for PromptCompiler."""

from __future__ import annotations

import time
from typing import Any

from .v1 import compile_v1


class ProxyError(ValueError):
    """Raised when a provider-compatible proxy request cannot be served."""

    def __init__(self, message: str, status_code: int = 400, code: str = "PROXY_ERROR") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def proxy_openai_chat_completions(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Compile an OpenAI-compatible chat completion request and return a mock response."""

    if payload.get("stream") is True:
        raise ProxyError(
            "Streaming proxy responses are not supported in this local mock provider yet.",
            status_code=400,
            code="STREAMING_NOT_SUPPORTED",
        )

    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ProxyError("messages must be a list", status_code=400, code="INVALID_MESSAGES")

    options = payload.get("promptcompiler")
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ProxyError("promptcompiler must be an object", status_code=400, code="INVALID_OPTIONS")
    if options.get("mock_provider") is False:
        raise ProxyError(
            "Live provider forwarding is not configured in Phase 6; omit mock_provider=false.",
            status_code=501,
            code="LIVE_PROVIDER_NOT_CONFIGURED",
        )

    model = str(payload.get("model") or "gpt-4o-mini")
    compile_payload = {
        "provider": str(options.get("provider") or "openai"),
        "model": model,
        "messages": messages,
        "mode": str(options.get("mode") or "balanced"),
        "session_id": options.get("session_id"),
        "target_token_budget": options.get("target_token_budget"),
        "dry_run": bool(options.get("dry_run", False)),
        "zero_retention": bool(options.get("zero_retention", True)),
        "rag_chunks": options.get("rag_chunks", payload.get("rag_chunks", [])),
        "tools": options.get("tools", payload.get("tools", [])),
        "context_policy": options.get("context_policy", {}),
        "output_policy": options.get("output_policy", {}),
        "semantic_policy": options.get("semantic_policy", {}),
        "tool_policy": options.get("tool_policy", {}),
        "cache_policy": options.get("cache_policy", {}),
        "task_type": options.get("task_type"),
    }
    compiled = compile_v1(compile_payload)
    trace_id = str(compiled["trace_id"])
    prompt_tokens = int(compiled["optimized_token_count"])
    response = {
        "id": f"chatcmpl_pc_{trace_id.removeprefix('tr_')[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        "[mock provider] PromptCompiler optimized the request locally. "
                        f"Trace: {trace_id}"
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": 0,
            "total_tokens": prompt_tokens,
        },
        "promptcompiler": {
            "trace_id": trace_id,
            "mode": compiled["mode"],
            "session_id": compiled["session_id"],
            "original_token_count": compiled["original_token_count"],
            "optimized_token_count": compiled["optimized_token_count"],
            "token_reduction_percent": compiled["token_reduction_percent"],
            "cache": compiled["cache"],
            "route": compiled.get("route", {}),
            "provider_cache_hints": compiled.get("provider_cache_hints", {}),
            "context_policy": compiled.get("context_policy", {}),
            "output_policy": compiled.get("output_policy", {}),
            "semantic_policy": compiled.get("semantic_policy", {}),
            "tool_policy": compiled.get("tool_policy", {}),
            "cache_policy": compiled.get("cache_policy", {}),
            "retention": compiled["retention"],
            "transformations": compiled["transformations"],
        },
    }
    headers = {
        "X-PromptCompiler-Trace": trace_id,
        "X-PromptCompiler-Original-Tokens": str(compiled["original_token_count"]),
        "X-PromptCompiler-Optimized-Tokens": str(compiled["optimized_token_count"]),
        "X-PromptCompiler-Cache-Status": str(compiled["cache"]["status"]),
    }
    return response, headers
