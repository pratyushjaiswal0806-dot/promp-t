"""PromptCompiler v2 pass pipeline."""

from __future__ import annotations

from .base import (
    Pass,
    PassContext,
    CompilerPipeline,
    CompilationResult,
    CompilationStats,
    PassRegistry,
    Diagnostic,
)

# Import pass implementations so their @PassRegistry.register runs
from .parse import ParsePass  # noqa: F401
from .normalize import NormalizePass  # noqa: F401
from .dedup import DedupPass  # noqa: F401
from .entity_resolve import EntityResolutionPass  # noqa: F401
from .summarize import SummarizePass  # noqa: F401
from .budget import BudgetPass  # noqa: F401
from .emit import EmitPass  # noqa: F401

__all__ = [
    "Pass",
    "PassContext",
    "CompilerPipeline",
    "CompilationResult",
    "CompilationStats",
    "PassRegistry",
    "Diagnostic",
]
