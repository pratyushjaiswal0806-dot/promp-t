import assert from "node:assert/strict";
import test from "node:test";

import {
  WORKFLOW_PRESETS,
  buildCompilePayload,
  createDefaultControls,
  controlsFromPreset,
} from "../src/services/payload.js";
import {
  buildTrustProfile,
  deriveUsabilityVerdict,
  optimizationInsight,
  proposedPromptForDryRun,
} from "../src/services/report.js";

test("buildCompilePayload threads every optimization policy field", () => {
  const controls = {
    ...createDefaultControls(),
    targetTokenBudget: "256",
    dryRun: true,
    zeroRetention: true,
    cacheStaticPrefix: true,
    cacheEnabled: true,
    outputFormat: "json",
    maxWords: "80",
    explain: false,
    systemPromptRef: "json_only",
    reuseExpectedCalls: "25",
    includeDecodePrompt: false,
    validationMode: "loose",
    retrievalTopK: "3",
    toolCompact: true,
    maxTools: "2",
    deterministicSemantic: true,
  };

  assert.deepEqual(
    buildCompilePayload({
      inputValue: "Keep CASE-123.\n\nrepeat\n\nrepeat",
      selectedModel: "gpt-4o-mini",
      mode: "balanced",
      controls,
    }),
    {
      input: "Keep CASE-123.\n\nrepeat\n\nrepeat",
      model: "gpt-4o-mini",
      mode: "balanced",
      target_token_budget: 256,
      dry_run: true,
      zero_retention: true,
      context_policy: {
        cache_static_prefix: true,
        retrieval_top_k: 3,
        system_prompt_ref: "json_only",
        reuse_expected_calls: 25,
        include_decode_prompt: false,
        validation: "loose",
      },
      output_policy: {
        explain: false,
        format: "json",
        max_words: 80,
      },
      tool_policy: {
        compact: true,
        max_tools: 2,
      },
      cache_policy: {
        enabled: true,
      },
      semantic_policy: {
        provider: "deterministic",
        scorer: "embedding",
        reason: "explicit_user_enabled",
      },
    },
  );
});

test("buildCompilePayload omits optional numeric fields when controls are blank", () => {
  const payload = buildCompilePayload({
    inputValue: "hello",
    selectedModel: "local",
    mode: "lossless",
    controls: createDefaultControls(),
  });

  assert.equal(payload.target_token_budget, null);
  assert.equal(payload.context_policy.retrieval_top_k, null);
  assert.equal(payload.context_policy.reuse_expected_calls, 10);
  assert.equal(payload.context_policy.include_decode_prompt, true);
  assert.equal(payload.context_policy.validation, "strict");
  assert.equal(payload.output_policy.max_words, null);
  assert.equal(payload.tool_policy.max_tools, null);
  assert.deepEqual(payload.semantic_policy, { scorer: "lexical", provider: "deterministic" });
});

test("buildCompilePayload auto-enables deterministic semantic scoring for RAG/source prompts", () => {
  const controls = {
    ...createDefaultControls(),
    autoSemantic: true,
    deterministicSemantic: false,
  };

  const payload = buildCompilePayload({
    inputValue: [
      "Question: Do refunds over 500 need manager approval?",
      "",
      "Source: doc-a",
      "Refunds over 500 require manager approval.",
      "",
      "Source: doc-b",
      "Reimbursements greater than 500 dollars need supervisor review.",
    ].join("\n"),
    selectedModel: "gpt-4o-mini",
    mode: "balanced",
    controls,
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "embedding",
    reason: "auto_rag_source_detected",
  });
});

test("buildCompilePayload keeps lexical semantic scoring for ordinary prompts in auto mode", () => {
  const payload = buildCompilePayload({
    inputValue: "Write a concise product brief for a local-first prompt compiler.",
    selectedModel: "gpt-4o-mini",
    mode: "balanced",
    controls: createDefaultControls(),
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "lexical",
  });
});

test("explicit deterministic semantic scoring overrides auto detection", () => {
  const controls = {
    ...createDefaultControls(),
    autoSemantic: false,
    deterministicSemantic: true,
  };

  const payload = buildCompilePayload({
    inputValue: "Write a concise product brief.",
    selectedModel: "gpt-4o-mini",
    mode: "lossless",
    controls,
  });

  assert.deepEqual(payload.semantic_policy, {
    provider: "deterministic",
    scorer: "embedding",
    reason: "explicit_user_enabled",
  });
});

test("workflow presets provide concrete optimization jobs", () => {
  assert.deepEqual(
    WORKFLOW_PRESETS.map((preset) => preset.id),
    [
      "reusable-context",
      "long-chat-history",
      "rag-overlap",
      "tool-logs",
      "json-schema-bloat",
      "support-ticket-context",
      "prompt-generation-cleanup",
    ],
  );

  const ragControls = controlsFromPreset("rag-overlap", createDefaultControls());
  assert.equal(ragControls.mode, "balanced");
  assert.equal(ragControls.retrievalTopK, "3");
  assert.equal(ragControls.deterministicSemantic, true);

  const reusableControls = controlsFromPreset("reusable-context", createDefaultControls());
  assert.equal(reusableControls.mode, "context_file");
  assert.equal(reusableControls.reuseExpectedCalls, "100");
  assert.equal(reusableControls.includeDecodePrompt, true);
  assert.equal(reusableControls.validationMode, "strict");
});

test("deriveUsabilityVerdict marks preserved low-risk output as ready to use", () => {
  const verdict = deriveUsabilityVerdict({
    dry_run: false,
    preservation: { ok: true, missing_entities: [] },
    compile: {
      warnings: [],
      risk_score: 0.28,
      plan: { risk_level: "medium" },
    },
  });

  assert.equal(verdict.label, "Ready to use");
  assert.equal(verdict.status, "ready");
});

test("deriveUsabilityVerdict blocks outputs with missing protected entities", () => {
  const verdict = deriveUsabilityVerdict({
    dry_run: false,
    preservation: { ok: false, missing_entities: ["CASE-123"] },
    compile: {
      warnings: [],
      risk_score: 0.9,
      plan: { risk_level: "high" },
    },
  });

  assert.equal(verdict.label, "Do not use");
  assert.equal(verdict.status, "blocked");
  assert.match(verdict.reason, /missing protected/i);
});

test("deriveUsabilityVerdict marks aggressive warning-heavy output for review", () => {
  const verdict = deriveUsabilityVerdict({
    dry_run: false,
    preservation: { ok: true, missing_entities: [] },
    compile: {
      warnings: ["Target budget 100 tokens was enforced by removing 1 segments."],
      risk_score: 0.73,
      plan: { risk_level: "high" },
    },
  });

  assert.equal(verdict.label, "Review first");
  assert.equal(verdict.status, "review");
  assert.match(verdict.reason, /high risk/i);
});

test("dry runs expose proposed optimized prompt separately from active output", () => {
  const result = {
    dry_run: true,
    optimized_prompt: "original prompt",
    preservation: { ok: true, missing_entities: [] },
    compile: {
      optimized_text: "original prompt",
      proposed_optimized_text: "optimized proposal",
      warnings: [],
      risk_score: 0.28,
      plan: { risk_level: "medium" },
    },
  };

  const verdict = deriveUsabilityVerdict(result);

  assert.equal(verdict.label, "Preview only");
  assert.equal(verdict.status, "preview");
  assert.equal(proposedPromptForDryRun(result), "optimized proposal");
});

test("optimizationInsight explains unchanged safe prompts", () => {
  const insight = optimizationInsight({
    original_token_count: 20,
    optimized_token_count: 20,
    compile: {
      original_tokens: 20,
      optimized_tokens: 20,
      tokens_saved: 0,
      semantic: { scorer: "lexical", summary: { rag_chunks: 0, removed_chunks: 0 } },
      plan: { actions: [] },
      warnings: [],
    },
  });

  assert.equal(insight.status, "unchanged");
  assert.match(insight.title, /no safe compression/i);
});

test("optimizationInsight explains semantic pruning when chunks are removed", () => {
  const insight = optimizationInsight({
    compile: {
      original_tokens: 48,
      optimized_tokens: 22,
      tokens_saved: 26,
      semantic: {
        scorer: "embedding",
        summary: { rag_chunks: 2, removed_chunks: 1 },
        removed_chunk_ids: ["seg_a_chunk_1"],
      },
      plan: { actions: [{ action: "rag_prune" }] },
      warnings: [],
    },
  });

  assert.equal(insight.status, "semantic");
  assert.match(insight.title, /semantic compression/i);
  assert.match(insight.body, /removed 1/i);
});

test("buildTrustProfile recommends distillation for creative website prompts with low safe savings", () => {
  const profile = buildTrustProfile({
    inputValue: "Create a modern responsive portfolio website with hero, about, skills, projects, experience, testimonials, blog, and contact sections.",
    mode: "balanced",
    result: {
      original_token_count: 120,
      optimized_token_count: 118,
      token_accounting: {
        method: "segmented_prompt_estimate",
        original_tokens: 120,
        optimized_tokens: 118,
        optimized_reuse_tokens: 122,
        segment_overhead_tokens: 12,
      },
      compile: {
        tokens_saved: 2,
        semantic: { scorer: "lexical", summary: { rag_chunks: 0, removed_chunks: 0 } },
        warnings: [],
      },
    },
  });

  assert.equal(profile.promptType, "Creative build prompt");
  assert.equal(profile.bestOptimization, "Distill");
  assert.equal(profile.safeCompressionPotential, "low");
  assert.equal(profile.confidence.label, "No safe savings");
  assert.match(profile.accounting.note, /segmented/i);
  assert.match(profile.explanationRows.map((row) => row.body).join(" "), /distillation/i);
});

test("buildTrustProfile marks RAG semantic pruning as verified semantic savings", () => {
  const profile = buildTrustProfile({
    inputValue: "Question: refund?\n\nSource: doc-a\nRefunds need approval.\n\nSource: doc-b\nReimbursements need supervisor review.",
    mode: "balanced",
    result: {
      original_token_count: 80,
      optimized_token_count: 48,
      token_accounting: {
        method: "segmented_prompt_estimate",
        original_tokens: 80,
        optimized_tokens: 48,
        optimized_reuse_tokens: 48,
      },
      compile: {
        tokens_saved: 32,
        semantic: {
          scorer: "embedding",
          summary: { rag_chunks: 2, removed_chunks: 1 },
          removed_chunk_ids: ["chunk_b"],
        },
        warnings: [],
      },
    },
  });

  assert.equal(profile.promptType, "RAG/source prompt");
  assert.equal(profile.bestOptimization, "Compress");
  assert.equal(profile.safeCompressionPotential, "high");
  assert.equal(profile.confidence.label, "Verified semantic savings");
});

test("buildTrustProfile marks duplicate removal as verified deterministic savings", () => {
  const profile = buildTrustProfile({
    inputValue: "repeat this block\n\nrepeat this block",
    mode: "balanced",
    result: {
      original_token_count: 20,
      optimized_token_count: 12,
      token_accounting: {
        method: "segmented_prompt_estimate",
        original_tokens: 20,
        optimized_tokens: 12,
        optimized_reuse_tokens: 12,
      },
      compile: {
        tokens_saved: 8,
        changes: [{ type: "duplicate_removed" }],
        semantic: { scorer: "lexical", summary: { rag_chunks: 0, removed_chunks: 0 } },
        warnings: [],
      },
    },
  });

  assert.equal(profile.promptType, "General prompt");
  assert.equal(profile.bestOptimization, "Compress");
  assert.equal(profile.confidence.label, "Verified deterministic savings");
});
