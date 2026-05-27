"""Provenance tracking for the PromptCompiler IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .segment import TransformRecord


@dataclass
class ProvenanceChain:
    """Complete provenance for a single output segment.

    Traces the segment's lineage back to original sources, enumerates all
    transformations applied, and reports preservation status.
    """

    output_segment_id: str
    original_segment_ids: list[str] = field(default_factory=list)
    transforms: list[TransformRecord] = field(default_factory=list)
    risk_score: float = 0.0
    preservation_status: str = "full"
    missing_entities: list[str] = field(default_factory=list)


@dataclass
class CompilationProvenance:
    """Full provenance for one compilation run."""

    input_hash: str = ""
    compiler_version: str = ""
    pipeline_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    segments: dict[str, ProvenanceChain] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    def verify_replay(self, other: CompilationProvenance) -> bool:
        return (
            self.input_hash == other.input_hash
            and self.compiler_version == other.compiler_version
            and self.pipeline_id == other.pipeline_id
        )
