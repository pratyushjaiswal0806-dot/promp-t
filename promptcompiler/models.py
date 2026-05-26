"""Small model registry for NIM-first local development."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os

from .env import load_local_env


load_local_env()

DEFAULT_NIM_MODEL = os.environ.get(
    "PROMPTCOMPILER_DEFAULT_MODEL",
    "openai/gpt-oss-120b",
)


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
        id="openai/gpt-oss-120b",
        provider="nvidia-nim",
        label="OpenAI GPT OSS 120B",
        context_window=128000,
        tokenizer="gpt-4o-compatible-estimate",
        notes="Default high-capacity NIM model for extensive prompt generation and compilation.",
    ),
    ModelSpec(
        id="nvidia/llama-3.1-nemotron-nano-8b-v1",
        provider="nvidia-nim",
        label="NVIDIA Llama 3.1 Nemotron Nano 8B",
        context_window=128000,
        tokenizer="fallback-estimate",
        notes="Default non-OSS NVIDIA model for prompt compression experiments.",
    ),
    ModelSpec(
        id="nvidia/nemotron-3-nano-30b-a3b",
        provider="nvidia-nim",
        label="NVIDIA Nemotron 3 Nano 30B",
        context_window=128000,
        tokenizer="fallback-estimate",
        notes="NVIDIA model option when exposed by the account-level API key.",
    ),
    ModelSpec(
        id="deepseek-ai/deepseek-v3.2",
        provider="nvidia-nim",
        label="DeepSeek V3.2",
        context_window=128000,
        tokenizer="fallback-estimate",
        notes="Large reasoning model option when exposed by the account-level API key.",
    ),
    ModelSpec(
        id="openai/gpt-oss-20b",
        provider="nvidia-nim",
        label="OpenAI GPT OSS 20B",
        context_window=128000,
        tokenizer="gpt-4o-compatible-estimate",
        notes="Fallback OpenAI OSS NIM model. Not used as the default.",
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
