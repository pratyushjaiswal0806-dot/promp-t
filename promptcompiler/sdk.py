"""Small dependency-free SDK helpers for PromptCompiler."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class PromptCompilerClient:
    """Client for the local PromptCompiler HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765", timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def analyze(
        self,
        *,
        messages: list[dict[str, Any]] | None = None,
        input: str | None = None,
        prompt: str | None = None,
        model: str,
        provider: str = "openai",
        mode: str = "balanced",
        session_id: str | None = None,
        target_token_budget: int | None = None,
        zero_retention: bool = True,
        rag_chunks: list[Any] | None = None,
        tools: list[Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = _platform_payload(
            messages=messages,
            input=input,
            prompt=prompt,
            model=model,
            provider=provider,
            mode=mode,
            session_id=session_id,
            target_token_budget=target_token_budget,
            zero_retention=zero_retention,
            rag_chunks=rag_chunks,
            tools=tools,
            extra=extra,
        )
        return self._post("/v1/analyze", payload)

    def compile(
        self,
        *,
        messages: list[dict[str, Any]] | None = None,
        input: str | None = None,
        prompt: str | None = None,
        model: str,
        provider: str = "openai",
        mode: str = "balanced",
        session_id: str | None = None,
        target_token_budget: int | None = None,
        zero_retention: bool = True,
        dry_run: bool = False,
        rag_chunks: list[Any] | None = None,
        tools: list[Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = _platform_payload(
            messages=messages,
            input=input,
            prompt=prompt,
            model=model,
            provider=provider,
            mode=mode,
            session_id=session_id,
            target_token_budget=target_token_budget,
            zero_retention=zero_retention,
            rag_chunks=rag_chunks,
            tools=tools,
            extra=extra,
        )
        payload["dry_run"] = dry_run
        return self._post("/v1/compile", payload)

    def proxy_openai_chat_completions(self, **payload: Any) -> dict[str, Any]:
        return self._post("/v1/proxy/openai/chat/completions", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8")
            try:
                detail = json.loads(body)
            except json.JSONDecodeError:
                detail = {"error": body}
            raise RuntimeError(detail.get("error", str(exc))) from exc
        return json.loads(body)


def wrap(
    client: Any,
    *,
    base_url: str = "http://127.0.0.1:8765",
    mode: str = "balanced",
    zero_retention: bool = True,
    compiler_client: PromptCompilerClient | None = None,
) -> Any:
    """Wrap an OpenAI-like client and compile chat messages before requests."""

    return _WrappedClient(
        client,
        compiler_client or PromptCompilerClient(base_url),
        defaults={"mode": mode, "zero_retention": zero_retention},
    )


class _WrappedClient:
    def __init__(
        self,
        client: Any,
        compiler: PromptCompilerClient,
        defaults: dict[str, Any],
    ) -> None:
        self._client = client
        self.chat = _WrappedChat(client.chat, compiler, defaults)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _WrappedChat:
    def __init__(
        self,
        chat: Any,
        compiler: PromptCompilerClient,
        defaults: dict[str, Any],
    ) -> None:
        self._chat = chat
        self.completions = _WrappedCompletions(chat.completions, compiler, defaults)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class _WrappedCompletions:
    def __init__(
        self,
        completions: Any,
        compiler: PromptCompilerClient,
        defaults: dict[str, Any],
    ) -> None:
        self._completions = completions
        self._compiler = compiler
        self._defaults = defaults

    def create(self, **kwargs: Any) -> Any:
        options = kwargs.pop("promptcompiler", None)
        if options is False or (isinstance(options, dict) and options.get("enabled") is False):
            return self._completions.create(**kwargs)

        options = options if isinstance(options, dict) else {}
        mode = str(options.get("mode") or self._defaults["mode"])
        zero_retention = bool(options.get("zero_retention", self._defaults["zero_retention"]))
        model = str(kwargs.get("model") or "")
        messages = kwargs.get("messages")
        if not isinstance(messages, list) or not model:
            return self._completions.create(**kwargs)

        compile_kwargs = {
            "provider": str(options.get("provider") or "openai"),
            "model": model,
            "messages": messages,
            "mode": mode,
            "session_id": options.get("session_id"),
            "target_token_budget": options.get("target_token_budget"),
            "zero_retention": zero_retention,
            "rag_chunks": options.get("rag_chunks"),
            "tools": options.get("tools", kwargs.get("tools")),
            "context_policy": options.get("context_policy"),
            "output_policy": options.get("output_policy"),
            "semantic_policy": options.get("semantic_policy"),
            "tool_policy": options.get("tool_policy"),
            "cache_policy": options.get("cache_policy"),
            "task_type": options.get("task_type"),
        }

        if options.get("analyze_only"):
            metadata = self._compiler.analyze(**compile_kwargs)
            response = self._completions.create(**kwargs)
            return _attach_metadata(response, metadata)

        compiled = self._compiler.compile(**compile_kwargs)
        optimized_messages = compiled.get("optimized_messages")
        if isinstance(optimized_messages, list) and optimized_messages:
            kwargs["messages"] = optimized_messages
        response = self._completions.create(**kwargs)
        return _attach_metadata(response, compiled)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _ResponseDict(dict[str, Any]):
    pass


def _attach_metadata(response: Any, metadata: dict[str, Any]) -> Any:
    summary = {
        "trace_id": metadata.get("trace_id"),
        "original_token_count": metadata.get(
            "original_token_count",
            metadata.get("total_tokens"),
        ),
        "optimized_token_count": metadata.get("optimized_token_count"),
        "token_reduction_percent": metadata.get("token_reduction_percent"),
        "retention": metadata.get("retention", {}),
        "context_policy": metadata.get("context_policy", {}),
        "output_policy": metadata.get("output_policy", {}),
        "semantic_policy": metadata.get("semantic_policy", {}),
        "tool_policy": metadata.get("tool_policy", {}),
        "cache_policy": metadata.get("cache_policy", {}),
        "route": metadata.get("route", {}),
        "provider_cache_hints": metadata.get("provider_cache_hints", {}),
    }
    if isinstance(response, dict):
        wrapped = _ResponseDict(response)
        wrapped.promptcompiler = summary
        return wrapped
    try:
        setattr(response, "promptcompiler", summary)
    except Exception:
        pass
    return response


def _platform_payload(
    *,
    messages: list[dict[str, Any]] | None,
    input: str | None,
    prompt: str | None,
    model: str,
    provider: str,
    mode: str,
    session_id: str | None,
    target_token_budget: int | None,
    zero_retention: bool,
    rag_chunks: list[Any] | None,
    tools: list[Any] | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "mode": mode,
        "zero_retention": zero_retention,
    }
    if messages is not None:
        payload["messages"] = messages
    elif input is not None:
        payload["input"] = input
    elif prompt is not None:
        payload["prompt"] = prompt
    if session_id:
        payload["session_id"] = session_id
    if target_token_budget is not None:
        payload["target_token_budget"] = target_token_budget
    if rag_chunks:
        payload["rag_chunks"] = rag_chunks
    if tools:
        payload["tools"] = tools
    for key, value in extra.items():
        if value is not None:
            payload[key] = value
    return payload
