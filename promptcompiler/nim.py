"""Optional NVIDIA NIM client using the OpenAI-compatible chat API."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NIM_MODEL = "openai/gpt-oss-20b"


class NimConfigError(RuntimeError):
    """Raised when NIM configuration is missing or invalid."""


class NimRequestError(RuntimeError):
    """Raised when a NIM API request fails."""


@dataclass(frozen=True)
class NimClient:
    api_key: str
    base_url: str = DEFAULT_NIM_BASE_URL

    @classmethod
    def from_env(cls) -> "NimClient":
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

    def summarize(self, text: str, model: str = DEFAULT_NIM_MODEL) -> dict[str, Any]:
        payload = self.build_summarize_payload(text, model)
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
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise NimRequestError(f"NIM request failed with HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise NimRequestError(f"NIM request failed: {exc.reason}") from exc

        parsed = json.loads(body)
        try:
            summary = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise NimRequestError("NIM response did not include choices[0].message.content") from exc

        return {
            "summary": summary,
            "model": payload["model"],
            "raw": parsed,
        }


def nim_is_configured() -> bool:
    return bool(os.environ.get("NVIDIA_API_KEY", "").strip())
