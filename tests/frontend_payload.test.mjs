import assert from "node:assert/strict";
import test from "node:test";

import {
  WORKFLOW_PRESETS,
  buildCompilePayload,
  createDefaultControls,
  controlsFromPreset,
} from "../src/services/payload.js";
import {
  deriveUsabilityVerdict,
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
  assert.equal(payload.output_policy.max_words, null);
  assert.equal(payload.tool_policy.max_tools, null);
  assert.deepEqual(payload.semantic_policy, { scorer: "lexical", provider: "deterministic" });
});

test("workflow presets provide concrete optimization jobs", () => {
  assert.deepEqual(
    WORKFLOW_PRESETS.map((preset) => preset.id),
    [
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
