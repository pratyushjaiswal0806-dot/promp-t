export const navItems = [
  { id: "home", label: "Home", href: "/" },
  { id: "workbench", label: "Workbench", href: "/workbench" },
  { id: "how-it-works", label: "How It Works", href: "/how-it-works" },
  { id: "platform", label: "Platform", href: "/platform" },
  { id: "security", label: "Security", href: "/security" },
  { id: "use-cases", label: "Use Cases", href: "/use-cases" },
  { id: "api-reference", label: "API", href: "/api-reference" },
  { id: "observability", label: "Observability", href: "/observability" },
  { id: "docs", label: "Docs", href: "/docs" },
];

export const homeHero = {
  eyebrow: "Local-first prompt compiler",
  title: "Compile long LLM context before it reaches the model.",
  body: "PromptCompiler parses messy context, protects critical facts, applies a compression policy, and returns inspectable savings with diffs, lint signals, semantic scores, and trace metadata.",
  primaryAction: { label: "Open Workbench", target: "workbench" },
  secondaryAction: { label: "See Pipeline", target: "how-it-works" },
  proof: [
    "Lossless, balanced, and aggressive compile modes",
    "Local-first defaults with zero-retention trace posture",
    "API, SDK, and OpenAI-compatible proxy paths",
  ],
};

export const valuePillars = [
  {
    label: "Parse",
    title: "Turn raw context into a structured prompt graph.",
    body: "Segments roles, RAG chunks, tool output, repeated blocks, pinned instructions, and high-risk identifiers before any reduction starts.",
  },
  {
    label: "Protect",
    title: "Keep critical values visible and verifiable.",
    body: "Pinned text, case IDs, URLs, names, and other protected entities are tracked so the compiler can warn when a policy may remove something important.",
  },
  {
    label: "Compile",
    title: "Apply a policy, not a blind shorten pass.",
    body: "Modes control duplicate removal, semantic pruning, prompt cleanup, budget targets, cache hints, and route-aware compression decisions.",
  },
  {
    label: "Measure",
    title: "Inspect every result before it ships.",
    body: "The workbench shows token deltas, changed blocks, semantic chunk scores, lint findings, trace IDs, and history for repeatable review.",
  },
];

export const pipelineJourney = [
  {
    step: "01",
    title: "Paste or generate context",
    body: "Start from agent logs, support transcripts, RAG output, or a generated build prompt. Samples and import controls keep the workbench fast for repeat testing.",
    signal: "Input",
  },
  {
    step: "02",
    title: "Analyze structure",
    body: "The parser separates instructions, context, tool results, repeated passages, and likely protected values before compile policy is applied.",
    signal: "Segments",
  },
  {
    step: "03",
    title: "Protect and prune",
    body: "Pinned instructions and important identifiers are preserved while semantic scoring can remove low-value RAG chunks that lexical matching would miss.",
    signal: "Policy",
  },
  {
    step: "04",
    title: "Compile for a target",
    body: "Lossless, balanced, or aggressive modes produce an optimized prompt with budget, cache, and routing metadata attached to the trace.",
    signal: "Output",
  },
  {
    step: "05",
    title: "Measure and inspect",
    body: "Diffs, warnings, lint, token savings, semantic scores, and run history make the result auditable before it is sent to an LLM.",
    signal: "Trace",
  },
];

export const platformSections = [
  {
    id: "workbench-controls",
    title: "Workbench controls",
    body: "A focused UI for model selection, sample loading, prompt import, compile mode, lint, analyze, compile, copy, export, and history review.",
    items: ["Model search", "Mode selector", "Sample loader", "Inspector panels"],
  },
  {
    id: "rag-semantic-pruning",
    title: "RAG and semantic pruning",
    body: "Semantic policy can score chunks and remove paraphrased or low-relevance context while preserving protected facts and warning on risk.",
    items: ["Chunk scoring", "Budget targets", "Protected entities", "Risk warnings"],
  },
  {
    id: "cache-routing",
    title: "Cache and routing signals",
    body: "Compile responses can expose cache policy, static-prefix hints, route tiers, and savings data for agent routing and cost review.",
    items: ["Cache hints", "Static prefixes", "Route tiers", "Trace metadata"],
  },
  {
    id: "api-sdk-proxy",
    title: "API, SDK, and proxy",
    body: "Use the local HTTP API directly, call it through the Python SDK, or route chat-completion style payloads through the OpenAI-compatible proxy.",
    items: ["/v1/analyze", "/v1/compile", "PromptCompilerClient", "/v1/proxy/openai/chat/completions"],
  },
];

export const securitySections = [
  {
    title: "Local-first by default",
    body: "The app is designed to run on the local Python server, with relative API calls and repo-local configuration for development.",
  },
  {
    title: "Zero-retention trace posture",
    body: "Trace views emphasize metadata, savings, warnings, and policy outcomes instead of storing raw prompt payloads as analytics records.",
  },
  {
    title: "Protected-value checks",
    body: "Critical values are detected and surfaced so compile results can be reviewed for missing IDs, URLs, names, and pinned instructions.",
  },
  {
    title: "Explicit provider boundary",
    body: "NVIDIA NIM or other provider calls remain visible as an opt-in boundary; local analysis and compile workflows stay usable without remote calls.",
  },
];

export const useCases = [
  {
    title: "Coding-agent logs",
    body: "Reduce long terminal output, file snippets, and tool traces before handing context to a planning or debugging model.",
    outcome: "Lower token load with inspectable diffs.",
  },
  {
    title: "RAG answer assembly",
    body: "Score retrieved chunks, prune weak matches, and keep protected facts before composing a final model request.",
    outcome: "Cleaner context windows for retrieval flows.",
  },
  {
    title: "Support and RMA context",
    body: "Preserve case numbers, order IDs, product names, and customer constraints while removing repeated conversation text.",
    outcome: "Safer compression for operational prompts.",
  },
  {
    title: "Prompt generation",
    body: "Generate a detailed website or app prompt, then compile and inspect it before sending the final version downstream.",
    outcome: "Faster prompt drafting with measurable savings.",
  },
  {
    title: "Model routing prep",
    body: "Attach token counts, savings, cache hints, and route metadata so agents can choose the right model tier.",
    outcome: "More predictable cost and latency decisions.",
  },
];

export const docsSections = [
  {
    title: "Run locally",
    body: "Start the Python server and Vite dev server during frontend work, or build static assets into the backend-served web directory.",
    commands: ["python3 -m promptcompiler.server", "npm run dev", "npm run build"],
  },
  {
    title: "Compile API",
    body: "Post raw input, model, mode, and optional semantic policy to `/v1/compile`; read optimized text, metrics, warnings, and trace metadata.",
    commands: [
      "curl -X POST http://127.0.0.1:8765/v1/compile -H 'Content-Type: application/json' -d '{\"input\":\"...\",\"mode\":\"balanced\"}'",
    ],
  },
  {
    title: "Python SDK",
    body: "Use `PromptCompilerClient` when an agent or script needs analyze and compile calls without hand-writing HTTP requests.",
    commands: ["from promptcompiler import PromptCompilerClient", "client.compile(input_text, mode='balanced')"],
  },
  {
    title: "Proxy route",
    body: "Send chat-completion shaped requests through the local proxy when an OpenAI-compatible integration needs prompt compilation first.",
    commands: ["/v1/proxy/openai/chat/completions", "X-PromptCompiler-Trace"],
  },
];

export const apiReferenceSections = [
  {
    label: "Analyze",
    title: "/v1/analyze",
    body: "Returns token estimates, segment boundaries, protected entities, duplicate groups, and compression opportunity before a compile run changes anything.",
  },
  {
    label: "Compile",
    title: "/v1/compile",
    body: "Accepts model, mode, target budget, context policy, output policy, cache policy, semantic policy, and dry-run flags, then returns optimized text plus evidence.",
  },
  {
    label: "Retrieve",
    title: "/v1/retrieve",
    body: "Scores retrieval chunks so teams can understand which context should remain visible before an expensive model call.",
  },
  {
    label: "Lint",
    title: "/v1/lint",
    body: "Flags prompt waste, vague instructions, oversized blocks, and other quality issues that make model behavior less predictable.",
  },
  {
    label: "Proxy",
    title: "/v1/proxy/openai/chat/completions",
    body: "Provides an OpenAI-compatible integration point for applications that want PromptCompiler to prepare context before chat-completion calls.",
  },
  {
    label: "Sessions",
    title: "/v1/sessions/{id}/context",
    body: "Builds compact session context from pinned, recent, and summarized turns while keeping request traces focused on metadata.",
  },
];

export const observabilitySections = [
  {
    label: "Trace",
    title: "Every compile produces inspectable metadata.",
    body: "Trace data can include route tier, cache status, token savings, compile mode, warnings, and request timing without depending on raw prompt retention.",
  },
  {
    label: "Metrics",
    title: "Savings and request counts become product signals.",
    body: "The metrics surface helps teams see token reduction, mode usage, cache behavior, and local platform activity over time.",
  },
  {
    label: "Diffs",
    title: "Prompt changes stay reviewable.",
    body: "Segment-level diffs explain removed duplicates, compacted blocks, preserved pins, and semantic pruning decisions.",
  },
  {
    label: "Risk",
    title: "Warnings stay next to the output.",
    body: "Policy warnings, lint findings, and protected-value checks make risk visible before optimized text is copied, exported, or proxied.",
  },
];

export const motionStats = [
  { value: "4", label: "Pipeline stages", detail: "parse, protect, compile, measure" },
  { value: "3", label: "Compile modes", detail: "lossless, balanced, aggressive" },
  { value: "0", label: "Default retention", detail: "raw payloads stay out of stored traces" },
  { value: "1", label: "Local workbench", detail: "controls, diffs, analytics, history" },
];

export const pageMeta = {
  home: {
    title: "PromptCompiler",
    eyebrow: "Premium local workbench",
    description: "A dark, immersive product overview for local-first prompt compilation.",
  },
  workbench: {
    title: "Workbench",
    eyebrow: "Compile and inspect",
    description: "Paste, analyze, compile, lint, compare, and export optimized prompts.",
  },
  "how-it-works": {
    title: "How It Works",
    eyebrow: "Pipeline",
    description: "Parse raw context, protect critical values, compile by policy, and measure the result.",
  },
  platform: {
    title: "Platform",
    eyebrow: "Integration surface",
    description: "API, SDK, proxy, semantic pruning, cache hints, routing metadata, and analytics.",
  },
  security: {
    title: "Security",
    eyebrow: "Local-first controls",
    description: "Local execution, protected-value checks, visible provider boundaries, and zero-retention trace posture.",
  },
  "use-cases": {
    title: "Use Cases",
    eyebrow: "Where it fits",
    description: "Practical workflows for agents, RAG, support operations, prompt drafting, and routing.",
  },
  docs: {
    title: "Docs",
    eyebrow: "Operator notes",
    description: "Commands, API shapes, SDK usage, proxy route notes, and verification entry points.",
  },
  "api-reference": {
    title: "API Reference",
    eyebrow: "HTTP surface",
    description: "A practical guide to the local analyze, compile, retrieve, lint, session, metrics, and proxy endpoints.",
  },
  observability: {
    title: "Observability",
    eyebrow: "Evidence layer",
    description: "How traces, metrics, diffs, warnings, and history explain what happened during each compile run.",
  },
};

export default {
  navItems,
  homeHero,
  valuePillars,
  pipelineJourney,
  platformSections,
  securitySections,
  useCases,
  docsSections,
  apiReferenceSections,
  observabilitySections,
  motionStats,
  pageMeta,
};
