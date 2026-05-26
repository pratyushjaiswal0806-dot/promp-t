"""Optional NVIDIA NIM client using the OpenAI-compatible chat API."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

from .entities import extract_entities
from .env import load_local_env
from .models import DEFAULT_NIM_MODEL


DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NimConfigError(RuntimeError):
    """Raised when NIM configuration is missing or invalid."""


class NimRequestError(RuntimeError):
    """Raised when a NIM API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int = 502,
        error_code: str = "NIM_REQUEST_FAILED",
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail


@dataclass(frozen=True)
class NimClient:
    api_key: str
    base_url: str = DEFAULT_NIM_BASE_URL

    @classmethod
    def from_env(cls) -> "NimClient":
        load_local_env()
        api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
        if not api_key:
            raise NimConfigError("NVIDIA_API_KEY is not configured")
        base_url = os.environ.get("NVIDIA_NIM_BASE_URL", DEFAULT_NIM_BASE_URL).rstrip("/")
        return cls(api_key=api_key, base_url=base_url)

    def build_summarize_payload(
        self,
        text: str,
        model: str = DEFAULT_NIM_MODEL,
    ) -> dict[str, Any]:
        return {
            "model": model or DEFAULT_NIM_MODEL,
            "temperature": 0.1,
            "max_tokens": 500,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You compress unpinned LLM prompt context. Preserve IDs, dates, URLs, "
                        "currency values, percentages, names, code requirements, schemas, and "
                        "explicit user constraints. Do not summarize text marked @pin. Return "
                        "only the compressed text."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Compress this unpinned context safely:\n\n{text}",
                },
            ],
        }

    def build_generate_prompt_payload(
        self,
        idea: str,
        kind: str = "website",
        model: str = DEFAULT_NIM_MODEL,
    ) -> dict[str, Any]:
        normalized_kind = (kind or "website").strip().lower() or "website"
        return {
            "model": model or DEFAULT_NIM_MODEL,
            "temperature": 0.35,
            "max_tokens": 2200,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a senior product prompt architect. Generate a very extensive, "
                        "production-ready prompt for an AI coding assistant. The prompt must be "
                        "specific, structured, implementation-oriented, and immediately usable. "
                        "Return only the generated prompt, not commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a very extensive prompt for building a {normalized_kind}.\n\n"
                        f"User idea:\n{idea.strip()}\n\n"
                        "The generated prompt must include these sections: product goal, target "
                        "users, core user workflows, information architecture, visual style, "
                        "layout requirements, responsive behavior, interactions, data/state "
                        "handling, empty/loading/error states, accessibility, performance, "
                        "acceptance criteria, and verification steps. Make it detailed enough "
                        "that a coding agent can build the website without asking follow-up "
                        "questions."
                    ),
                },
            ],
        }

    def list_available_models(self) -> list[dict[str, Any]]:
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/models",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise _nim_http_error(
                exc,
                "NIM model listing",
                "NVIDIA NIM is not authorized to list models with the configured API key.",
            ) from exc
        except urllib.error.URLError as exc:
            raise NimRequestError(f"NIM model listing failed: {exc.reason}") from exc

        parsed = json.loads(body)
        raw_models = parsed.get("data", [])
        if not isinstance(raw_models, list):
            raise NimRequestError("NIM model listing response did not include a data array")

        models: list[dict[str, Any]] = []
        for item in raw_models:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            model_id = str(item["id"])
            models.append(
                {
                    "id": model_id,
                    "provider": "nvidia-nim",
                    "label": _label_from_model_id(model_id),
                    "context_window": int(item.get("context_window") or 0),
                    "tokenizer": "fallback-estimate",
                    "notes": "Loaded from NVIDIA NIM /v1/models for this API key.",
                }
            )

        return sorted(models, key=lambda model: (model["id"].startswith("openai/gpt-oss"), model["id"]))

    def generate_extensive_prompt(
        self,
        idea: str,
        kind: str = "website",
        model: str = DEFAULT_NIM_MODEL,
    ) -> dict[str, Any]:
        payload = self.build_generate_prompt_payload(idea, kind=kind, model=model)
        parsed = self._chat_completion(
            payload,
            context="NIM prompt generation",
            authorization_message=(
                "NVIDIA NIM is not authorized for prompt generation with the configured "
                "API key. Create or paste a NVIDIA API key with inference access, then "
                "restart PromptCompiler."
            ),
        )
        generated = _message_content(parsed, "NIM prompt generation response")
        return {
            "generated_prompt": generated,
            "model": payload["model"],
            "kind": (kind or "website").strip().lower() or "website",
            "raw": parsed,
        }

    def summarize(self, text: str, model: str = DEFAULT_NIM_MODEL) -> dict[str, Any]:
        payload = self.build_summarize_payload(text, model)
        parsed = self._chat_completion(
            payload,
            context="NIM request",
            authorization_message=(
                "NVIDIA NIM is not authorized for chat completions with the configured "
                "API key. Create or paste a NVIDIA API key with inference access, then "
                "restart PromptCompiler."
            ),
            timeout=60,
        )
        summary = _message_content(parsed, "NIM response")

        preservation = _check_preservation(text, summary)

        return {
            "summary": summary,
            "model": payload["model"],
            "preservation": preservation,
            "raw": parsed,
        }

    def _chat_completion(
        self,
        payload: dict[str, Any],
        context: str,
        authorization_message: str,
        timeout: int = 90,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise _nim_http_error(
                exc,
                context,
                authorization_message,
            ) from exc
        except urllib.error.URLError as exc:
            raise NimRequestError(f"{context} failed: {exc.reason}") from exc

        return json.loads(body)


def nim_is_configured() -> bool:
    load_local_env()
    return bool(os.environ.get("NVIDIA_API_KEY", "").strip())


def _ssl_context() -> ssl.SSLContext:
    cafile = _certifi_cafile()
    if cafile:
        return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


def _certifi_cafile() -> str | None:
    try:
        import certifi  # type: ignore
    except Exception:
        return None
    return str(certifi.where())


def _check_preservation(original: str, summary: str) -> dict[str, Any]:
    original_entities = extract_entities(original)
    missing = [entity for entity in original_entities if entity not in summary]
    return {
        "ok": not missing,
        "checked_entities": original_entities,
        "missing_entities": missing,
    }


def _message_content(parsed: dict[str, Any], response_name: str) -> str:
    try:
        content = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise NimRequestError(
            f"{response_name} did not include choices[0].message.content"
        ) from exc
    return str(content)


def _nim_http_error(
    exc: urllib.error.HTTPError,
    context: str,
    authorization_message: str,
) -> NimRequestError:
    try:
        detail = exc.read().decode("utf-8", errors="replace")
    finally:
        exc.close()
    if exc.code in {401, 403}:
        return NimRequestError(
            authorization_message,
            status_code=exc.code,
            error_code="NIM_AUTHORIZATION_FAILED",
            detail=detail,
        )
    return NimRequestError(
        f"{context} failed with HTTP {exc.code}: {detail}",
        status_code=502,
        error_code="NIM_REQUEST_FAILED",
        detail=detail,
    )


def _label_from_model_id(model_id: str) -> str:
    return model_id.split("/", 1)[-1].replace("-", " ").replace("_", " ").title()
