export const security = {
  hero: {
    eyebrow: "Local-First Controls",
    title: "Security",
    intro: "Your data never leaves your machine unless you choose to send it. Everything runs locally.",
  },
  principles: [
    { label: "Local-First", title: "Everything runs locally", body: "The app runs on your local Python server with relative API calls and repo-local configuration. No prompts are sent to third parties by default." },
    { label: "Zero Retention", title: "Zero-retention trace posture", body: "Trace views emphasize metadata, savings, warnings, and policy outcomes instead of storing raw prompt payloads as analytics records." },
    { label: "Protected Values", title: "Protected-value checks", body: "Critical values are detected and surfaced so compile results can be reviewed for missing IDs, URLs, names, and pinned instructions." },
    { label: "Provider Boundary", title: "Explicit provider boundary", body: "NVIDIA NIM or other provider calls remain visible as an opt-in boundary. Local analysis and compile workflows stay usable without remote calls." },
  ],
  comparisonData: {
    headers: ["Capability", "PromptCompiler", "Cloud alternatives"],
    rows: [
      ["Data residency", true, false],
      ["Audit trail", true, "check:partial"],
      ["Deterministic transforms", true, false],
      ["Offline capable", true, false],
      ["Cost per request", "check:free", "cross:usage-based"],
    ],
  },
};
