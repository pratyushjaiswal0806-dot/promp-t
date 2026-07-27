export const home = {
  hero: {
    eyebrow: "Local-first LLM context optimizer",
    title: "Compile long prompts before they reach the model.",
    intro: "Paste a prompt. See where tokens go. Remove the waste. Get a smaller prompt with a traceable change report — all local, no paid APIs required.",
  },
  actions: [
    { label: "Open Workbench", target: "workbench" },
    { label: "See How It Works", target: "how-it-works", variant: "secondary" },
  ],
  metrics: [
    { value: "~30%", label: "Median token reduction", detail: "on RAG, chat history, and tool output benchmarks" },
    { value: "<1s", label: "Compile latency", detail: "for typical debugging payloads on local CPU" },
    { value: "100%", label: "Deterministic mode", detail: "same input always produces identical output" },
    { value: "0", label: "Paid APIs required", detail: "core compile runs entirely offline" },
  ],
  features: [
    {
      label: "Parse",
      title: "Map every token before touching it.",
      body: "Segments roles, RAG chunks, tool output, duplicated instruction blocks, and pinned @pin markers into a structured graph — so the compiler knows what it is working with.",
      code: "$ curl -X POST http://127.0.0.1:8765/v1/analyze \\\n  -d '{\"model\":\"gpt-4o-mini\",\"messages\":[...]}",
    },
    {
      label: "Protect",
      title: "Lock what matters so it never disappears.",
      body: "Case IDs, URLs, dates, currency values, and any @pin-marked instruction survive every transformation. The compiler warns when a change policy would lose something important.",
      code: "@pin CASE-123 - do not summarize this\n@pin $50,000 budget limit",
    },
    {
      label: "Compile",
      title: "Reduce context with explainable rules.",
      body: "Four modes — lossless, balanced, aggressive, and context_file. Each produces a diff showing exactly what changed, why, and how many tokens were saved.",
      code: "$ promptcompiler compile prompt.json --mode balanced\nRemoved 3 duplicate instruction blocks\nCompacting 4 tool/log repetition lines",
    },
    {
      label: "Measure",
      title: "Audit every run before it ships.",
      body: "Token deltas, changed blocks, semantic scores, lint findings, and a trace ID — so every optimized prompt is reviewable before it reaches the model.",
      code: "original_tokens: 1847\noptimized_tokens: 1243\ntokens_saved: 604 (32.7%)\nchanges: [dedupe, compact_log, prune_rag]",
    },
  ],
  stages: [
    { number: "01", title: "Paste or import", body: "Drop in raw text, OpenAI messages JSON, or RAG chunk arrays. Workbench accepts multiple formats." },
    { number: "02", title: "Analyze", body: "Inspect token allocation, roles, duplicate groups, and protected entities before committing to any changes." },
    { number: "03", title: "Compile", body: "Choose a mode and compile. Review the diff, savings, and any preservation warnings." },
    { number: "04", title: "Export or copy", body: "Copy the optimized text, export JSON, or re-run with a different mode. Trace IDs enable replay." },
  ],
  useCaseLinks: [
    { title: "RAG pipelines", body: "Prune overlapping retrieved segments by semantic similarity. Protect citation IDs and source URLs while reducing redundancy in context windows.", target: "use-cases", image: "/rag_answer_assembly.png" },
    { title: "Long chat history", body: "Remove repeated instruction blocks and collapsed log lines while preserving case IDs, names, and monetary values exactly.", target: "use-cases", image: "/prompt_generation.png" },
    { title: "Tool and agent logs", body: "Compact repeated failure patterns, truncate oversized tool output, and keep the final decision or result intact.", target: "use-cases", image: "/support_rma_context.png" },
  ],
  beforeAfter: {
    eyebrow: "Before / After",
    title: "What compile looks like",
    before: {
      label: "Original — 1,847 tokens",
      code: "[SYSTEM] You are an AI assistant.\n[SYSTEM] You are an AI assistant.\n[SYSTEM] You are an AI assistant.\n[USER] @pin CASE-2024-99: Acme Corp refund request\n[USER] Customer: John Smith, Acme Corp\n[USER] Issue: Billing error on invoice INV-4421\n[USER] Request: Refund of $3,200 for overcharge\n[TOOL] Failed: connection refused\n[TOOL] Failed: connection refused\n[TOOL] Failed: connection refused\n[ASSISTANT] I can help with that refund...",
    },
    after: {
      label: "Optimized — 1,243 tokens (32.7% saved)",
      code: "[SYSTEM] You are an AI assistant.\n[USER] @pin CASE-2024-99: Acme Corp refund request\n[USER] Customer: John Smith, Acme Corp\n[USER] Issue: Billing error on invoice INV-4421\n[USER] Request: Refund of $3,200 for overcharge\n[TOOL] Failed: connection refused [x3]\n[ASSISTANT] I can help with that refund...",
    },
  },
  benchmarks: [
    { corpus: "30 prompt pairs", coverage: "RAG, chat history, tool logs, JSON schemas, compliance" },
    { corpus: "Median savings", coverage: "~30% token reduction across balanced/aggressive modes" },
    { corpus: "Pinned preservation", coverage: "100% - no @pin content removed in any mode" },
    { corpus: "Zero-retention mode", coverage: "No raw prompt text in traces, cache, or browser history" },
  ],
};