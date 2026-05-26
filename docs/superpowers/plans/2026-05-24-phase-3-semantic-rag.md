# Phase 3 Semantic Compression And RAG Optimization Plan

## Scope

Implement the approved Phase 3 slice from the PRD/TRD roadmap while keeping PromptCompiler local-first:

- Sentence-aware semantic chunking with sliding windows and overlap.
- Query-aware relevance, similarity, novelty, and compression-risk scores.
- RAG redundancy pruning that preserves source/citation metadata, pins, and protected values.
- Compiler response metadata for semantic chunks, removed chunk IDs, retained chunk IDs, warnings, and plan actions.
- Dashboard rendering for semantic signals.

## Out Of Scope

- Redis semantic cache.
- Production embedding models.
- Full nDCG benchmark dashboard.
- Automatic NIM summarization without explicit user confirmation.

## Implementation Steps

1. Add failing tests first.
   - Add semantic module tests for chunking and scoring.
   - Add compiler tests for duplicate RAG pruning and source/protected-value preservation.
   - Add server contract coverage for semantic metadata.
   - Extend browser E2E expectations for visible semantic signals.

2. Add `promptcompiler.semantic`.
   - Split segments into sentence-aware chunks.
   - Use `window_tokens=256` and `overlap_tokens=32` defaults.
   - Preserve source and citation metadata on every chunk.
   - Score chunks with local lexical heuristics for query relevance, inter-chunk similarity, novelty, and risk.

3. Integrate semantic pruning into `compile_prompt`.
   - Derive the current query from the last non-RAG, non-tool segment.
   - For balanced/aggressive modes, remove redundant unpinned RAG segments only when a retained chunk is sufficiently similar and at least as relevant.
   - Do not remove chunks with unique protected entities or pins, and preserve source/citation metadata on retained chunks.
   - Return semantic metadata and plan actions.

4. Update the website.
   - Add a Semantic Signals panel in the inspector.
   - Render retained/removed chunk IDs, relevance, novelty, similarity, and risk.
   - Keep mobile layout stable.

5. Verify.
   - Run focused semantic/compiler/server tests.
   - Run the full unittest suite with dotenv disabled.
   - Restart the local server and run a browser smoke against `http://127.0.0.1:8765/`.

## Manual Steps

- Optional: refresh `NVIDIA_API_KEY` in `.env` only if you want the explicit NIM Summarize action to work.
- Review one real RAG prompt in balanced and aggressive mode to judge semantic quality.
