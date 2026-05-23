"""Small model registry for NIM-first local development."""

from __future__ import annotations

from dataclasses import asdict, dataclass


DEFAULT_NIM_MODEL = "openai/gpt-oss-20b"


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    label: str
    context_window: int
    tokenizer: str
    notes: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


_MODELS = [
    ModelSpec(
        id="openai/gpt-oss-20b",
        provider="nvidia-nim",
        label="OpenAI GPT OSS 20B",
        context_window=128000,
        tokenizer="gpt-4o-compatible-estimate",
        notes="Default NIM development model for low-cost summarization and reasoning.",
    ),
    ModelSpec(
        id="openai/gpt-oss-120b",
        provider="nvidia-nim",
        label="OpenAI GPT OSS 120B",
        context_window=128000,
        tokenizer="gpt-4o-compatible-estimate",
        notes="Higher-capacity NIM model when available in the account.",
    ),
    ModelSpec(
        id="qwen/qwen2.5-coder-32b-instruct",
        provider="nvidia-nim",
        label="Qwen2.5 Coder 32B",
        context_window=32768,
        tokenizer="fallback-estimate",
        notes="Useful for code-heavy prompt compaction experiments.",
    ),
    ModelSpec(
        id="meta/llama-3.2-1b-instruct",
        provider="nvidia-nim",
        label="Llama 3.2 1B Instruct",
        context_window=128000,
        tokenizer="fallback-estimate",
        notes="Small NIM model for quick smoke tests when exposed to the account.",
    ),
]


def list_models() -> list[dict[str, str | int]]:
    return [model.to_dict() for model in _MODELS]


def get_model(model_id: str) -> dict[str, str | int]:
    for model in _MODELS:
        if model.id == model_id:
            return model.to_dict()
    return {
        "id": model_id,
        "provider": "nvidia-nim",
        "label": model_id,
        "context_window": 0,
        "tokenizer": "fallback-estimate",
        "notes": "Custom model id supplied by the user.",
    }
