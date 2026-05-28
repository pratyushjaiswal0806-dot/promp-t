export const home = {
  hero: {
    eyebrow: "Local-first prompt compiler",
    title: "Compile long LLM context before it reaches the model.",
    intro: "Stop wasting tokens. Parse, protect, compile, measure — all local, all deterministic.",
  },
  actions: [
    { label: "Open Workbench", target: "workbench" },
    { label: "See Pipeline", target: "how-it-works", variant: "secondary" },
  ],
  metrics: [
    { value: "4", label: "Pipeline stages", detail: "parse, protect, compile, measure" },
    { value: "3", label: "Compile modes", detail: "lossless, balanced, aggressive" },
    { value: "0", label: "Default retention", detail: "raw payloads stay out of stored traces" },
    { value: "1", label: "Local workbench", detail: "controls, diffs, analytics, history" },
  ],
  features: [
    { label: "Parse", title: "Turn raw context into a structured prompt graph.", body: "Segments roles, RAG chunks, tool output, repeated blocks, pinned instructions, and high-risk identifiers before any reduction starts.", code: "parser.segment(input) → ContextGraph" },
    { label: "Protect", title: "Keep critical values visible and verifiable.", body: "Pinned text, case IDs, URLs, names, and other protected entities are tracked so the compiler can warn when a policy may remove something important.", code: "protector.scan(graph) → Entity[]" },
    { label: "Compile", title: "Apply a policy, not a blind shorten pass.", body: "Modes control duplicate removal, semantic pruning, prompt cleanup, budget targets, cache hints, and route-aware compression decisions.", code: "compiler.compile(graph, mode) → Optimized" },
    { label: "Measure", title: "Inspect every result before it ships.", body: "The workbench shows token deltas, changed blocks, semantic chunk scores, lint findings, trace IDs, and history for repeatable review.", code: "measure.report(result) → Trace" },
  ],
  stages: [
    { number: "01", title: "Parse", body: "Splits raw input into structured segments, roles, RAG chunks, tool output, and repeated blocks." },
    { number: "02", title: "Protect", body: "Detects pinned instructions and values like case IDs so compression does not lose critical context." },
    { number: "03", title: "Compile", body: "Applies lossless, balanced, or aggressive transformations with budget-aware routing and cache hints." },
    { number: "04", title: "Measure", body: "Shows savings, diffs, lint findings, semantic signals, and trace metadata for review." },
  ],
  useCaseLinks: [
    { title: "RAG ANSWER ASSEMBLY", body: "Preview code online or bypass... RAG answer assembly to simulate.", target: "use-cases", image: "/rag_answer_assembly.png" },
    { title: "PROMPT GENERATION", body: "Prompt generation, core data or prompts in generation thresholds.", target: "use-cases", image: "/prompt_generation.png" },
    { title: "SUPPORT AND RMA CONTEXT", body: "Support and context prep/resolutions when managing support and RMA context.", target: "use-cases", image: "/support_rma_context.png" },
  ],
};
