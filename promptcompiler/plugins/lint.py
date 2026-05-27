"""Lint rule protocol for token-waste detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class LintFinding:
    """A single lint finding."""
    code: str
    severity: str          # "error" | "warning" | "info"
    message: str
    line: int | None = None
    column: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LintContext:
    """Context available to a lint rule."""
    text: str
    filename: str | None = None
    total_tokens: int = 0
    segment_count: int = 0
    mode: str = "lossless"


class LintRule(Protocol):
    """A single lint rule.  Implementations must be deterministic."""

    rule_id: str
    severity: str

    def check(self, context: LintContext) -> LintFinding | None:
        """Check *context* and return a finding, or None."""
        ...
