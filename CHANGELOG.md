# Changelog

## 0.3.0 (unreleased)

### Breaking

- **v1 compiler removed** in favour of v2 pass pipeline (`CompilerRuntime`).
  `compiler.py` now delegates to the v2 pipeline internally.
- **Plugin system removed.** The concrete scorer (lexical/Jaccard), tokenizer
  (tiktoken/regex), and lint rules are inlined directly into their respective
  modules (`semantic.py`, `tokenizer.py`, `lint.py`).
- **SHA-256 embeddings replaced** with SimHash (64-bit) fingerprints.
  `EmbeddingStore` renamed to `FingerprintStore`.
- **IR layer collapsed.** `ir/graph.py`, `ir/entity.py`, `ir/provenance.py`,
  `ir/policy.py` replaced by single `ir/types.py` with flat annotated dataclasses.

### Added

- Benchmark suite: `benchmarks/` with 30 prompt pairs and `evaluate.py`.
- Smoke test flag: `--smoke-test` on `compile` subcommand.
- CHANGELOG.md

### Changed

- NormalizePass now includes JSON/markdown minification.
- SummarizePass handles tool-like text segments (any segment > 20 lines).
- Per-model tokenizer mapping with approximation warnings for non-OpenAI models.
