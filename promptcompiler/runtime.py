"""CompilerRuntime — top-level orchestrator for the v2 pass pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from promptcompiler.ir import ContextGraph
from promptcompiler.passes import CompilerPipeline, CompilationResult, PassContext, PassRegistry
from promptcompiler.passes.parse import ParsePass
from promptcompiler.settings import CompilerSettings


_DEFAULT_PASS_ORDER = [
    "parse.v1",
    "normalize.v1",
    "dedup.v1",
    "entity_resolve.v1",
    "summarize.v1",
    "budget.v1",
    "emit.v1",
]


@lru_cache(maxsize=1)
def _default_pipeline() -> CompilerPipeline:
    """Build the default v2 compiler pipeline."""
    return PassRegistry.build_pipeline("default.v1", _DEFAULT_PASS_ORDER)


class CompilerRuntime:
    """Runtime orchestrator for the v2 compiler pipeline.

    Usage::

        runtime = CompilerRuntime()
        result = runtime.compile("Hello world")
        print(result.output_graph.fingerprint())
    """

    def __init__(
        self,
        pipeline: CompilerPipeline | None = None,
        settings: CompilerSettings | None = None,
    ) -> None:
        self._pipeline = pipeline or _default_pipeline()
        self._settings = settings or CompilerSettings()

    def compile(
        self,
        raw_input: str,
        mode: str | None = None,
        target_token_budget: int | None = None,
        dry_run: bool = False,
    ) -> CompilationResult:
        """Compile *raw_input* through the v2 pipeline.

        Returns a ``CompilationResult`` with the output graph, diagnostics,
        and statistics.
        """
        graph = ContextGraph(
            compiler_version="2.0.0",
            pipeline_config={
                "mode": mode or self._settings.default_mode,
                "target_token_budget": target_token_budget,
                "dry_run": dry_run,
            },
        )
        graph.data["raw_input"] = raw_input

        ctx = PassContext(
            compiler_version=graph.compiler_version,
            settings=self._settings,
        )

        return self._pipeline.execute(graph, ctx)

    def compile_to_text(self, raw_input: str, **kw: object) -> str:
        """Compile and return only the optimized text."""
        result = self.compile(raw_input, **kw)  # type: ignore[arg-type]
        return result.output_graph.data.get("output_text", "")

    @property
    def pipeline(self) -> CompilerPipeline:
        return self._pipeline
