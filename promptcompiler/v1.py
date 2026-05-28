"""Versioned platform API contract helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any
from uuid import uuid4

from .analyzer import analyze_prompt
from .cache import cache_key_for_compile
from .compiler import compile_prompt
from .embeddings import normalize_semantic_policy
from .lint import lint_token_waste
from .minify import structured_input_to_text
from .models import DEFAULT_NIM_MODEL
from .policies import normalize_context_policy, normalize_output_policy
from .prompt_registry import expand_system_prompt_ref
from .retrieval import select_retrieval_context
from .routing import choose_model_route
from .storage import get_store
from .tokenizer import estimate_text_tokens
from .tools import select_tools_for_query


_ESTIMATED_COST_PER_1K_TOKENS = 0.0015


@dataclass(frozen=True)
class NormalizedV1Request:
    trace_id: str
    provider: str
    model: str
    session_id: str | None
    raw_input: str
    mode: str
    target_token_budget: int | None
    dry_run: bool
    zero_retention: bool
    payload_kind: str
    messages: list[dict[str, str]]
    context_policy: dict[str, Any]
    output_policy: dict[str, Any]
    semantic_policy: dict[str, Any]
    tool_policy: dict[str, Any]
    cache_policy: dict[str, Any]


def analyze_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Analyze a prompt via the v1 API.

    Returns token breakdown, component analysis, budget utilization,
    and a recommendation on whether to compile.
    """
    started = time.perf_counter()
    request = normalize_v1_request(payload)
    analysis = analyze_prompt(request.raw_input, model=request.model)
    components = _analysis_components(analysis)
    pinned_tokens = sum(item["token_count"] for item in components if item["is_pinned"])
    budget_utilization = _budget_utilization(
        analysis["total_tokens"],
        request.target_token_budget,
    )
    should_compile = analysis["compression_opportunity"] > 0 or (
        budget_utilization is not None and budget_utilization >= 0.7
    ) or analysis["total_tokens"] > 800

    response = {
        "trace_id": request.trace_id,
        "provider": request.provider,
        "model": request.model,
        "session_id": request.session_id,
        "mode": request.mode,
        "dry_run": request.dry_run,
        "total_tokens": analysis["total_tokens"],
        "segment_count": analysis["segment_count"],
        "compression_opportunity": analysis["compression_opportunity"],
        "estimated_input_cost_usd": _estimated_cost(analysis["total_tokens"]),
        "budget_utilization": budget_utilization,
        "pinned_tokens": pinned_tokens,
        "pinned_budget_ratio": (
            round(pinned_tokens / analysis["total_tokens"], 6) if analysis["total_tokens"] else 0
        ),
        "components": components,
        "recommendation": {
            "should_compile": should_compile,
            "reason": _recommendation_reason(should_compile, budget_utilization, analysis),
        },
        "tokenizer_accuracy": "estimated",
        "tokenizer": _tokenizer_metadata(request),
        "retention": _retention_metadata(request),
        "context_policy": request.context_policy,
        "output_policy": request.output_policy,
        "semantic_policy": request.semantic_policy,
        "tool_policy": request.tool_policy,
        "analysis": analysis,
    }
    _record_trace(
        endpoint="analyze",
        request=request,
        response=response,
        latency_ms=_elapsed_ms(started),
    )
    return response


def compile_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Compile a prompt via the v1 API.

    Applies deterministic compression (dedup, summarization, semantic pruning)
    based on the normalized request parameters. Caches results by cache key.
    Records a trace for observability.
    """
    started = time.perf_counter()
    request = normalize_v1_request(payload)
    cache_key = _compile_cache_key(payload, request)
    if cache_key:
        cached = get_store().get_compile_cache(cache_key)
        if cached:
            response = dict(cached)
            response["trace_id"] = request.trace_id
            response["cache"] = {"status": "hit", "key": cache_key}
            response["provider_cache_hints"] = {
                "static_prefix_cacheable": request.context_policy.get("cache_static_prefix", False),
                "cache_key": cache_key,
            }
            _record_trace(
                endpoint="compile",
                request=request,
                response=response,
                latency_ms=_elapsed_ms(started),
            )
            return response

    result = compile_prompt(
        request.raw_input,
        model=request.model,
        mode=request.mode,
        target_token_budget=request.target_token_budget,
        dry_run=request.dry_run,
        semantic_policy=request.semantic_policy,
    )
    before_cost = _estimated_cost(result["original_tokens"])
    after_cost = _estimated_cost(result["optimized_tokens"])
    route = choose_model_route(
        {"task_type": payload.get("task_type"), "total_tokens": result["original_tokens"]}
    )
    cache = {"status": "miss", "key": cache_key} if cache_key else {"status": result["cache_status"]}

    response = {
        "trace_id": request.trace_id,
        "provider": request.provider,
        "model": request.model,
        "session_id": request.session_id,
        "mode": result["mode"],
        "dry_run": result["dry_run"],
        "original_token_count": result["original_tokens"],
        "optimized_token_count": result["optimized_tokens"],
        "token_reduction_percent": _percent_reduction(
            result["original_tokens"],
            result["optimized_tokens"],
        ),
        "estimated_cost_before_usd": before_cost,
        "estimated_cost_after_usd": after_cost,
        "estimated_cost_reduction_percent": _cost_reduction_percent(before_cost, after_cost),
        "optimized_prompt": result["optimized_text"],
        "optimized_messages": _optimized_messages(result, request),
        "transformations": _transformations(result),
        "evaluation": {
            "layer1_retention_score": 1.0 if result["preservation"]["ok"] else 0.0,
            "layer2_status": (
                "disabled_zero_retention" if request.zero_retention else "not_configured"
            ),
        },
        "cache": cache,
        "route": route,
        "provider_cache_hints": {
            "static_prefix_cacheable": request.context_policy.get("cache_static_prefix", False),
            "cache_key": cache_key,
        },
        "tokenizer_accuracy": "estimated",
        "tokenizer": _tokenizer_metadata(request),
        "retention": _retention_metadata(request),
        "context_policy": request.context_policy,
        "output_policy": request.output_policy,
        "semantic_policy": request.semantic_policy,
        "tool_policy": request.tool_policy,
        "cache_policy": request.cache_policy,
        "semantic": result["semantic"],
        "preservation": result["preservation"],
        "compile": result,
    }
    if cache_key:
        get_store().set_compile_cache(cache_key, response)
    _record_trace(
        endpoint="compile",
        request=request,
        response=response,
        latency_ms=_elapsed_ms(started),
    )
    return response


def retrieve_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Retrieve the most relevant RAG chunks for a query using semantic search.

    Parameters
    ----------
    payload : dict
        Must contain "query" (str) and "rag_chunks" (list of dicts with id/source/text).

    Returns
    -------
    dict
        Retrieved chunks ordered by relevance score.
    """
    query = str(payload.get("query") or "")
    chunks = []
    for index, item in enumerate(payload.get("rag_chunks") or []):
        if isinstance(item, dict):
            text = _content_to_text(item.get("text", item.get("content", "")))
            chunks.append(
                {
                    "id": str(item.get("id") or item.get("source") or f"chunk_{index + 1}"),
                    "source": str(item.get("source") or item.get("id") or f"chunk_{index + 1}"),
                    "text": text,
                    "tokens": max(12, estimate_text_tokens(text)),
                }
            )
    return select_retrieval_context(
        query=query,
        chunks=chunks,
        top_k=int(payload.get("top_k") or 5),
        max_tokens=int(payload.get("max_tokens") or 1200),
    )


def lint_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Lint a prompt for token waste and return actionable findings.

    Parameters
    ----------
    payload : dict
        Must contain "input" (str) — the prompt text to lint.

    Returns
    -------
    dict
        Payload kind and a list of findings (redundant whitespace, repeated lines, etc.).
    """
    raw_input, payload_kind, _ = _raw_input_from_payload(payload)
    return {
        "payload_kind": payload_kind,
        "findings": lint_token_waste(raw_input),
    }


def append_session_v1(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append a conversation turn to a session with automatic compaction.

    Parameters
    ----------
    session_id : str
        Session identifier.
    payload : dict
        Turn data (role, content) plus optional policy fields (zero_retention, mode, etc.).

    Returns
    -------
    dict
        Result of appending the turn, including compaction metadata if triggered.
    """
    provider = str(payload.get("provider") or _provider_from_model(str(payload.get("model", ""))))
    model = str(payload.get("model") or DEFAULT_NIM_MODEL)
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    zero_retention = bool(payload.get("zero_retention", policy.get("zero_retention", False)))
    turn = payload.get("turn")
    if not isinstance(turn, dict):
        raise ValueError("turn must be an object")
    content = _content_to_text(turn.get("content", ""))
    role = str(turn.get("role") or "user")
    return get_store().append_session_turn(
        session_id=session_id,
        provider=provider,
        model=model,
        role=role,
        content=content,
        target_token_budget=_target_budget(payload.get("target_token_budget")),
        mode=str(payload.get("mode") or "lossless"),
        zero_retention=zero_retention,
    )


def metrics_v1(filters: dict[str, str]) -> dict[str, Any]:
    """Return aggregate usage metrics (request count, tokens, etc.)."""
    return get_store().metrics(filters)


def request_trace_v1(trace_id: str) -> dict[str, Any] | None:
    """Return a request trace by ID, or None if not found."""
    return get_store().get_trace(trace_id)


def session_context_v1(session_id: str, filters: dict[str, str]) -> dict[str, Any]:
    """Return session context with sliding window and budget."""
    target = _target_budget(filters.get("target_token_budget"))
    window = int(filters.get("sliding_window_turns") or 4)
    return {
        "session_id": session_id,
        "target_token_budget": target,
        "sliding_window_turns": window,
        "context": get_store().session_context(session_id, target, window),
    }


_ALLOWED_MODES = {"lossless", "balanced", "aggressive"}


def normalize_v1_request(payload: dict[str, Any]) -> NormalizedV1Request:
    provider = str(payload.get("provider") or _provider_from_model(str(payload.get("model", ""))))
    model = str(payload.get("model") or DEFAULT_NIM_MODEL)
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    zero_retention = bool(payload.get("zero_retention", policy.get("zero_retention", False)))
    context_policy = normalize_context_policy(payload.get("context_policy"))
    output_policy = normalize_output_policy(payload.get("output_policy"))
    semantic_policy = normalize_semantic_policy(payload.get("semantic_policy"))
    tool_policy = payload.get("tool_policy") if isinstance(payload.get("tool_policy"), dict) else {}
    cache_policy = payload.get("cache_policy") if isinstance(payload.get("cache_policy"), dict) else {}
    raw_input, payload_kind, messages = _raw_input_from_payload(payload, tool_policy=tool_policy)
    raw_input = _apply_prompt_policies(raw_input, context_policy, output_policy)

    mode = str(payload.get("mode") or "lossless").strip().lower()
    if mode not in _ALLOWED_MODES:
        raise ValueError(
            f"Unsupported compression mode '{mode}'. Choose lossless, balanced, or aggressive."
        )

    target_token_budget = _target_budget(payload.get("target_token_budget"))

    return NormalizedV1Request(
        trace_id=str(payload.get("trace_id") or f"tr_{uuid4().hex}"),
        provider=provider,
        model=model,
        session_id=str(payload["session_id"]) if payload.get("session_id") else None,
        raw_input=raw_input,
        mode=mode,
        target_token_budget=target_token_budget,
        dry_run=bool(payload.get("dry_run", False)),
        zero_retention=zero_retention,
        payload_kind=payload_kind,
        messages=messages,
        context_policy=context_policy,
        output_policy=output_policy,
        semantic_policy=semantic_policy,
        tool_policy=tool_policy,
        cache_policy=cache_policy,
    )


def _raw_input_from_payload(
    payload: dict[str, Any],
    tool_policy: dict[str, Any] | None = None,
) -> tuple[str, str, list[dict[str, str]]]:
    if "structured_input" in payload:
        return structured_input_to_text(payload.get("structured_input")), "structured_input", []

    if "messages" in payload:
        if not isinstance(payload["messages"], list):
            raise ValueError("messages must be a list")
        messages = _normalize_messages(payload["messages"])
        messages_text = json.dumps({"messages": messages}, ensure_ascii=True, sort_keys=True)
        parts = [messages_text]
        parts.extend(_rag_chunks_to_text(payload.get("rag_chunks", [])))
        parts.extend(
            _tools_to_text(
                payload.get("tools", []),
                query=_query_from_messages(messages),
                tool_policy=tool_policy or {},
            )
        )
        return "\n\n".join(part for part in parts if part.strip()), "messages", messages

    if "input" in payload:
        return str(payload.get("input") or ""), "input", []
    if "prompt" in payload:
        return str(payload.get("prompt") or ""), "prompt", []
    return "", "empty", []


def _normalize_messages(messages: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"messages[{index}] must be an object")
        normalized.append(
            {
                "role": str(message.get("role") or "user"),
                "content": _content_to_text(message.get("content", "")),
            }
        )
    return normalized


def _rag_chunks_to_text(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if not isinstance(value, list):
        raise ValueError("rag_chunks must be a list")

    chunks: list[str] = []
    for index, chunk in enumerate(value):
        if isinstance(chunk, str):
            chunks.append(chunk)
            continue
        if not isinstance(chunk, dict):
            raise ValueError(f"rag_chunks[{index}] must be an object or string")
        source = str(chunk.get("source") or chunk.get("id") or f"rag_{index + 1}")
        citation = str(chunk.get("citation") or "").strip()
        text = _content_to_text(chunk.get("text", chunk.get("content", "")))
        lines = [f"Source: {source}"]
        if citation:
            lines.append(f"Citation: {citation}")
        lines.append(text)
        chunks.append("\n".join(line for line in lines if line.strip()))
    return chunks


def _tools_to_text(
    value: Any,
    query: str = "",
    tool_policy: dict[str, Any] | None = None,
) -> list[str]:
    if value is None or value == "":
        return []
    if not isinstance(value, list):
        raise ValueError("tools must be a list")

    selected_value = value
    policy = tool_policy or {}
    if policy.get("compact"):
        dict_tools = [tool for tool in value if isinstance(tool, dict)]
        selected_value = select_tools_for_query(
            query,
            dict_tools,
            max_tools=int(policy.get("max_tools") or 8),
        )

    tools: list[str] = []
    for index, tool in enumerate(selected_value):
        if isinstance(tool, str):
            tools.append(f"Tool: tool_{index + 1}\n{tool}")
            continue
        if not isinstance(tool, dict):
            raise ValueError(f"tools[{index}] must be an object or string")
        function = tool.get("function") if isinstance(tool.get("function"), dict) else {}
        name = str(tool.get("name") or function.get("name") or tool.get("type") or f"tool_{index + 1}")
        tools.append(
            "Tool: "
            + name
            + "\n"
            + json.dumps(tool, ensure_ascii=True, sort_keys=True)
        )
    return tools


def _apply_prompt_policies(
    raw_input: str,
    context_policy: dict[str, Any],
    output_policy: dict[str, Any],
) -> str:
    prefix_parts: list[str] = []
    expanded = expand_system_prompt_ref(context_policy.get("system_prompt_ref"))
    if expanded:
        prefix_parts.append(str(expanded["content"]))
    instruction = str(output_policy.get("instruction") or "").strip()
    if instruction:
        prefix_parts.append(instruction)
    if not prefix_parts:
        return raw_input
    prefix = "\n".join(prefix_parts)
    return f"{prefix}\n\n{raw_input}" if raw_input.strip() else prefix


def _query_from_messages(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") != "system" and message.get("content"):
            return message["content"]
    return messages[-1]["content"] if messages else ""


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
                else:
                    parts.append(json.dumps(item, ensure_ascii=True, sort_keys=True))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=True, sort_keys=True)


def _target_budget(value: Any) -> int | None:
    if value is None or value == "":
        return None
    budget = int(value)
    if budget < 0:
        raise ValueError("target_token_budget must be a non-negative integer.")
    return budget


def _provider_from_model(model: str) -> str:
    if model.startswith("nvidia/"):
        return "nvidia"
    if model.startswith("anthropic/"):
        return "anthropic"
    if model.startswith("google/") or model.startswith("gemini"):
        return "google"
    return "openai-compatible"


def _analysis_components(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    total_tokens = analysis["total_tokens"]
    for segment in analysis["segments"]:
        token_count = int(segment["tokens"])
        components.append(
            {
                "segment_id": segment["id"],
                "component_type": segment["type"],
                "role": segment["role"],
                "token_count": token_count,
                "relative_share": round(token_count / total_tokens, 6) if total_tokens else 0,
                "cost_estimate_usd": _estimated_cost(token_count),
                "is_pinned": bool(segment["pinned"]),
                "compression_risk_score": 1.0 if segment["pinned"] else 0.25,
                "protected_entities": segment["entities"],
            }
        )
    return components


def _optimized_messages(
    result: dict[str, Any],
    request: NormalizedV1Request,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for item in result["diff"]:
        if item.get("status") == "removed":
            continue
        role = str(item.get("role") or "user")
        if role == "unknown":
            continue
        messages.append({"role": role, "content": str(item.get("optimized_text") or "")})

    if messages:
        return messages
    if request.messages:
        return _messages_with_policy_prefix(request.messages, request)
    if request.payload_kind in {"input", "prompt", "empty"}:
        return [{"role": "user", "content": result["optimized_text"]}]
    return []


def _messages_with_policy_prefix(
    messages: list[dict[str, str]],
    request: NormalizedV1Request,
) -> list[dict[str, str]]:
    prefix_parts: list[str] = []
    expanded = expand_system_prompt_ref(request.context_policy.get("system_prompt_ref"))
    if expanded:
        prefix_parts.append(str(expanded["content"]))
    instruction = str(request.output_policy.get("instruction") or "").strip()
    if instruction:
        prefix_parts.append(instruction)
    if not prefix_parts:
        return messages

    prefix = "\n".join(prefix_parts)
    output = [dict(message) for message in messages]
    if output and output[0].get("role") == "system":
        output[0]["content"] = f"{prefix}\n\n{output[0].get('content', '')}".strip()
        return output
    return [{"role": "system", "content": prefix}, *output]


def _transformations(result: dict[str, Any]) -> list[dict[str, Any]]:
    transformations: list[dict[str, Any]] = []
    for action in result["plan"]["actions"]:
        transformations.append(
            {
                "type": action.get("action", "transform"),
                "affected_segment_ids": action.get("segment_ids", []),
                "affected_chunk_ids": action.get("chunk_ids", []),
                "reason": action.get("reason", ""),
                "estimated_tokens_saved": action.get("estimated_tokens_saved"),
            }
        )
    return transformations


def _tokenizer_metadata(request: NormalizedV1Request) -> dict[str, str]:
    return {
        "provider": request.provider,
        "model": request.model,
        "tokenizer": "promptcompiler-estimator",
        "accuracy": "estimated",
    }


def _retention_metadata(request: NormalizedV1Request) -> dict[str, Any]:
    return {
        "zero_retention": request.zero_retention,
        "raw_payload_stored": False,
        "optimized_payload_stored": False,
        "storage": "sqlite-metrics",
        "external_evaluation_allowed": not request.zero_retention,
    }


def _compile_cache_key(payload: dict[str, Any], request: NormalizedV1Request) -> str | None:
    if not request.cache_policy.get("enabled"):
        return None
    return cache_key_for_compile(
        request.raw_input,
        {
            "model": request.model,
            "mode": request.mode,
            "target_token_budget": request.target_token_budget,
            "dry_run": request.dry_run,
            "context_policy": request.context_policy,
            "output_policy": request.output_policy,
            "semantic_policy": request.semantic_policy,
            "tool_policy": request.tool_policy,
            "task_type": payload.get("task_type"),
        },
    )


def _record_trace(
    endpoint: str,
    request: NormalizedV1Request,
    response: dict[str, Any],
    latency_ms: int,
) -> None:
    if endpoint == "analyze":
        original_tokens = int(response["total_tokens"])
        optimized_tokens = original_tokens
        reduction = 0.0
        cost_before = float(response["estimated_input_cost_usd"])
        cost_after = cost_before
        transformations: list[dict[str, Any]] = []
        evaluation_status = "not_configured"
        cache_status = "bypass"
    else:
        original_tokens = int(response["original_token_count"])
        optimized_tokens = int(response["optimized_token_count"])
        reduction = float(response["token_reduction_percent"])
        cost_before = float(response["estimated_cost_before_usd"])
        cost_after = float(response["estimated_cost_after_usd"])
        transformations = response.get("transformations", [])
        evaluation_status = str(response.get("evaluation", {}).get("layer2_status", "not_configured"))
        cache_status = str(response.get("cache", {}).get("status", "bypass"))

    get_store().record_trace(
        {
            "trace_id": response["trace_id"],
            "endpoint": endpoint,
            "provider": request.provider,
            "model": request.model,
            "session_id": request.session_id,
            "mode": request.mode,
            "original_token_count": original_tokens,
            "optimized_token_count": optimized_tokens,
            "token_reduction_percent": reduction,
            "estimated_cost_before_usd": cost_before,
            "estimated_cost_after_usd": cost_after,
            "cache_status": cache_status,
            "evaluation_status": evaluation_status,
            "zero_retention": request.zero_retention,
            "latency_ms": latency_ms,
            "transformations": transformations,
            "retention": response["retention"],
        }
    )


def _budget_utilization(total_tokens: int, target_token_budget: int | None) -> float | None:
    if not target_token_budget:
        return None
    return round(total_tokens / target_token_budget, 6)


def _estimated_cost(tokens: int) -> float:
    return round((tokens / 1000) * _ESTIMATED_COST_PER_1K_TOKENS, 8)


def _percent_reduction(original: int, optimized: int) -> float:
    if not original:
        return 0.0
    return round(((original - optimized) / original) * 100, 2)


def _cost_reduction_percent(before: float, after: float) -> float:
    if not before:
        return 0.0
    return round(((before - after) / before) * 100, 2)


def _recommendation_reason(
    should_compile: bool,
    budget_utilization: float | None,
    analysis: dict[str, Any],
) -> str:
    if not should_compile:
        return "below budget threshold"
    if budget_utilization is not None and budget_utilization >= 0.7:
        return "near target budget"
    if analysis["compression_opportunity"] > 0:
        return "redundant context detected"
    return "compile recommended"


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))
