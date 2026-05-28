export const platform = {
  hero: {
    eyebrow: "Integration Surface",
    title: "Platform",
    intro: "API, SDK, proxy, semantic pruning, cache hints, and routing metadata — all surfaced through a deterministic compiler pipeline.",
  },
  capabilities: [
    { icon: "⌨", title: "Workbench Controls", body: "Model search, mode selector (lossless/balanced/aggressive), sample loader, file import, inspector panels, and export controls.", tryIt: 'curl -X POST /v1/compile -d \'{"input":"...","mode":"balanced"}\'' },
    { icon: "▤", title: "RAG & Semantic Pruning", body: "Score retrieved chunks with semantic or lexical policies. Prune weak matches while keeping protected facts and warning on risk.", tryIt: 'curl -X POST /v1/retrieve -d \'{"input":"...","top_k":5}\'' },
    { icon: "◷", title: "Cache & Routing", body: "Compile responses expose cache policy hints, static-prefix signals, route tiers, and savings metadata for agent routing and cost review.", tryIt: 'curl -X POST /v1/compile -d \'{"cache_policy":{"ttl":300}}\'' },
    { icon: "⚡", title: "API, SDK & Proxy", body: "Use the local HTTP API directly, call it through the Python SDK, or route chat-completion payloads through the OpenAI-compatible proxy.", tryIt: 'from promptcompiler import PromptCompilerClient; client.compile("...")' },
  ],
  techStack: [
    { name: "Python 3.11+", role: "Core compiler engine" },
    { name: "FastAPI", role: "HTTP server layer" },
    { name: "SQLite", role: "Session and trace storage" },
    { name: "React + Vite", role: "Frontend workbench" },
    { name: "OpenAI Proxy", role: "Compatible integration" },
  ],
  architecture: [
    { component: "Client", description: "Workbench, CLI, or external application" },
    { component: "CLI", description: "Command-line interface for scripting" },
    { component: "API", description: "FastAPI HTTP server (local)" },
    { component: "SDK", description: "Python client library" },
    { component: "Proxy", description: "OpenAI-compatible chat endpoint" },
    { component: "Pipeline", description: "7-pass deterministic compiler" },
    { component: "Storage", description: "SQLite store for sessions & traces" },
  ],
};
