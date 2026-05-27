"""Centralized configuration for promptcompiler v2.

All environment variables are read once at import and exposed as typed
Pydantic settings. Components should import from here, not from os.environ.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    """Storage backend configuration."""

    model_config = SettingsConfigDict(env_prefix="PROMPTCOMPILER_")

    backend: Literal["sqlite", "postgres", "redis"] = "sqlite"
    path: str = str(Path.cwd() / ".promptcompiler" / "promptcompiler.sqlite3")
    dsn: str = ""
    cache_url: str = ""
    embedding_dimensions: int = 64
    pool_size: int = 4
    enable_cache: bool = True


class CompilerSettings(BaseSettings):
    """Core compiler pipeline configuration."""

    model_config = SettingsConfigDict(env_prefix="PROMPTCOMPILER_")

    pass_pipeline: str = "default.v1"
    default_model: str = "openai/gpt-oss-120b"
    default_mode: Literal["lossless", "balanced", "aggressive"] = "lossless"
    pinned_budget_ratio: float = 0.25
    session_trigger_threshold: float = 0.7
    session_summary_ratio: float = 0.22

    # Priority scoring weights (must sum to 1.0)
    weight_recency: float = 0.15
    weight_instruction: float = 0.20
    weight_relevance: float = 0.25
    weight_entity_density: float = 0.10
    weight_retrieval_confidence: float = 0.10
    weight_centrality: float = 0.10
    weight_role: float = 0.05
    weight_pinned: float = 0.05

    def validate_weights(self) -> None:
        total = (
            self.weight_recency
            + self.weight_instruction
            + self.weight_relevance
            + self.weight_entity_density
            + self.weight_retrieval_confidence
            + self.weight_centrality
            + self.weight_role
            + self.weight_pinned
        )
        if not abs(total - 1.0) < 1e-3:
            from warnings import warn
            warn(f"Priority weights sum to {total}, expected 1.0")


class SecuritySettings(BaseSettings):
    """Security and compliance configuration."""

    model_config = SettingsConfigDict(env_prefix="PROMPTCOMPILER_")

    enable_secret_scanning: bool = True
    enable_entity_masking: bool = False
    mask_reversible: bool = True
    audit_signing_key: str = ""
    retention_days: int = 90


class PluginSettings(BaseSettings):
    """Plugin discovery configuration."""

    model_config = SettingsConfigDict(env_prefix="PROMPTCOMPILER_")

    extra_plugin_paths: list[str] = []
    disable_entry_point_discovery: bool = False


class PromptCompilerSettings(BaseSettings):
    """Root settings aggregating all sub-settings."""

    model_config = SettingsConfigDict(env_prefix="PROMPTCOMPILER_")

    storage: StorageSettings = StorageSettings()
    compiler: CompilerSettings = CompilerSettings()
    security: SecuritySettings = SecuritySettings()
    plugins: PluginSettings = PluginSettings()
    disable_dotenv: bool = False
    debug: bool = False


# Singleton — import this everywhere
settings = PromptCompilerSettings()
