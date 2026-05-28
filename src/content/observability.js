export const observability = {
  hero: {
    eyebrow: "Evidence Layer",
    title: "Observability",
    intro: "Traces, metrics, diffs, warnings, and history — every compile produces inspectable evidence of what happened and why.",
  },
  signals: [
    { label: "Trace", title: "Every compile produces inspectable metadata.", body: "Route tier, cache status, token savings, compile mode, warnings, and request timing without depending on raw prompt retention." },
    { label: "Metrics", title: "Savings and request counts become product signals.", body: "Token reduction, mode usage, cache behavior, and local platform activity over time. Shown in the workbench analytics drawer." },
    { label: "Diffs", title: "Prompt changes stay reviewable.", body: "Segment-level diffs explain removed duplicates, compacted blocks, preserved pins, and semantic pruning decisions — side by side." },
    { label: "Risk", title: "Warnings stay next to the output.", body: "Policy warnings, lint findings, and protected-value checks make risk visible before optimized text is copied, exported, or proxied." },
  ],
  traceExample: `{
  "trace_id": "tr_abc123",
  "route_tier": "local",
  "cache_status": "miss",
  "compile_mode": "balanced",
  "original_tokens": 1240,
  "optimized_tokens": 680,
  "token_savings_pct": 45.2,
  "warnings": ["pinned_value_detected: case-ID-9876"],
  "duration_ms": 34,
  "timestamp": "2026-05-28T10:30:00Z"
}`,
};
