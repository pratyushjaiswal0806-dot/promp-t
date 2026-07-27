import { createContext, useContext, useState, useCallback, useRef, useEffect, useMemo } from "react";
import { getHealth, getModels, getSamples, analyze, compile, getTrace, lint, generatePrompt, nimSummarize } from "../../services/compiler.js";
import { readHistory, saveToHistory } from "../../services/history.js";
import { buildCompilePayload, createDefaultControls, controlsFromPreset } from "../../services/payload.js";
import { buildTrustProfile, deriveUsabilityVerdict, optimizationInsight, proposedPromptForDryRun } from "../../services/report.js";
import { toast } from "../../components/Toast.jsx";

const Ctx = createContext(null);

const EMPTY_OUTPUT = "No optimized prompt yet.";
const EMPTY_METRICS = [["Original", "-"], ["Optimized", "-"], ["Saved", "-"], ["Savings", "-"]];
const INITIAL_MODEL = "openai/gpt-oss-120b";

export function WorkbenchProvider({ children }) {
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  const [inputValue, setInputValue] = useState("");
  const [optimizedOutput, setOptimizedOutput] = useState(EMPTY_OUTPUT);
  const [models, setModels] = useState([]);
  const [modelQuery, setModelQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState(INITIAL_MODEL);
  const [samples, setSamples] = useState([]);
  const [selectedSampleId, setSelectedSampleId] = useState("");
  const [promptIdea, setPromptIdea] = useState("");
  const [promptKind, setPromptKind] = useState("website");
  const [mode, setMode] = useState("balanced");
  const [workflowPresetId, setWorkflowPresetId] = useState("");
  const [controls, setControls] = useState(createDefaultControls);
  const [metrics, setMetrics] = useState(EMPTY_METRICS);
  const [breakdown, setBreakdown] = useState([]);
  const [entities, setEntities] = useState([]);
  const [changes, setChanges] = useState([]);
  const [lintFindings, setLintFindings] = useState([]);
  const [segments, setSegments] = useState([]);
  const [diffItems, setDiffItems] = useState([]);
  const [ragRows, setRagRows] = useState([]);
  const [semantic, setSemantic] = useState(null);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [modeComparisons, setModeComparisons] = useState([]);
  const [traceLookupId, setTraceLookupId] = useState("");
  const [traceLookupResult, setTraceLookupResult] = useState(null);
  const [lastCompile, setLastCompile] = useState(null);
  const [error, setError] = useState("");
  const [workingAction, setWorkingAction] = useState("");
  const [appStatus, setAppStatus] = useState({ text: "Preparing compiler", className: "" });

  // Model filtering
  const filteredModels = useMemo(() => {
    const q = modelQuery.trim().toLowerCase();
    if (!q) return models;
    return models.filter((m) => `${m.id || ""} ${m.label || ""} ${m.provider || ""}`.toLowerCase().includes(q));
  }, [modelQuery, models]);

  const visibleModels = useMemo(() => {
    const selected = models.find((m) => String(m.id) === selectedModel) || { id: selectedModel, label: selectedModel };
    if (!filteredModels.length) return [selected];
    return filteredModels.some((m) => String(m.id) === selectedModel) ? filteredModels : [selected, ...filteredModels];
  }, [filteredModels, models, selectedModel]);

  const canExport = optimizedOutput && optimizedOutput !== EMPTY_OUTPUT;

  // Boot
  useEffect(() => {
    (async () => {
      try {
        const [health, modelPayload, samplePayload] = await Promise.all([getHealth(), getModels(), getSamples()]);
        const nextModels = modelPayload.models || [];
        const nextModel = modelPayload.default_model || health.default_model || selectedModel;
        setModels(nextModels);
        setSamples(samplePayload.samples || []);
        setSelectedModel(nextModel);
        setHistory(readHistory());
        setAppStatus({ text: health.nim_configured ? "Ready + NIM" : "Ready", className: "ready" });
      } catch {
        setAppStatus({ text: "Server unavailable", className: "missing" });
      }
    })();
  }, []);

  const clearError = useCallback(() => setError(""), []);

  const showError = useCallback((msg) => {
    setError(msg);
    toast(msg, "error");
  }, []);

  const resetWorkbench = useCallback(() => {
    setLastCompile(null);
    setOptimizedOutput(EMPTY_OUTPUT);
    setMetrics(EMPTY_METRICS);
    setBreakdown([]);
    setEntities([]);
    setChanges([]);
    setLintFindings([]);
    setSegments([]);
    setDiffItems([]);
    setRagRows([]);
    setSemantic(null);
    setReport(null);
    setModeComparisons([]);
    setHistory(readHistory());
  }, []);

  const runAction = useCallback(async (name, fn) => {
    setWorkingAction(name);
    try { await fn(); }
    catch (e) { showError(e && e.message ? String(e.message) : String(e)); }
    finally { setWorkingAction((c) => (c === name ? "" : c)); }
  }, [showError]);

  const updateControl = useCallback((key, value) => {
    setControls((current) => ({ ...current, [key]: value }));
  }, []);

  const applyWorkflowPreset = useCallback((presetId) => {
    setWorkflowPresetId(presetId);
    const next = controlsFromPreset(presetId, controls);
    if (next.mode) setMode(next.mode);
    const { mode: _, ...controlValues } = next;
    setControls(controlValues);
  }, [controls]);

  const applyCompileResult = useCallback((result, prompt, resultMode, resultModel, resultControls) => {
    const c = result.compile || result;
    const text = result.optimized_prompt || c.optimized_text || "";
    const orig = result.original_token_count ?? c.original_tokens ?? 0;
    const opt = result.optimized_token_count ?? c.optimized_tokens ?? 0;
    const saved = c.tokens_saved ?? Math.max(0, orig - opt);
    const savings = result.token_reduction_percent ?? ((c.savings_ratio || 0) * 100);
    const nextDiff = c.diff || result.diff || [];
    const nextSemantic = result.semantic || c.semantic || null;
    const contextFile = result.context_file || c.context_file || null;
    const metricRows = [
      ["Original", orig],
      ["Optimized", opt],
      ["Saved", saved],
      ["Savings", `${Number(savings || 0).toFixed(1)}%`],
      ["Risk", c.plan?.risk_level || _riskLabel(c.risk_score)],
      ["Route", result.route?.tier || "local"],
      ["Cache", result.cache?.status || c.cache_status || "bypass"],
      ["Mode", resultMode],
    ];
    if (contextFile) {
      metricRows.splice(
        4,
        0,
        ["First call", contextFile.net_first_call_savings],
        ["Per reuse", contextFile.net_reuse_savings_per_call],
        ["Break-even", contextFile.break_even_calls || "-"],
      );
    }

    setLastCompile(result);
    setOptimizedOutput(text);
    setMetrics(metricRows);
    setBreakdown(Object.entries(_diffBreakdown(nextDiff)));
    setEntities(result.preservation?.checked_entities || c.preservation?.checked_entities || []);
    setChanges(_buildChanges(c, result).slice(0, 200));
    setDiffItems(nextDiff.slice(0, 200));
    setSegments(_segmentsFromCompile(nextDiff, result.analysis?.segments || []));
    setSemantic(nextSemantic);
    setRagRows(_ragRows(nextSemantic));
    setReport(_buildReport(result, c, resultMode, resultModel, resultControls, prompt));
    setTraceLookupResult(null);
    return { text, orig, opt, saved, savings, trace_id: result.trace_id, mode: resultMode, model: resultModel, prompt };
  }, []);

  const runCompileForPrompt = useCallback(async ({
    prompt = inputValue,
    compileMode = mode,
    model = selectedModel,
    compileControls = controls,
    saveHistory = true,
  } = {}) => {
    const payload = buildCompilePayload({
      inputValue: prompt,
      selectedModel: model,
      mode: compileMode,
      controls: compileControls,
    });
    const result = await compile(payload);
    let summary;
    try {
      summary = applyCompileResult(result, prompt, compileMode, model, compileControls);
    } catch (err) {
      showError(`Failed to process compile result: ${err && err.message ? err.message : String(err)}`);
      return result;
    }
    try {
      const l = await lint(prompt);
      setLintFindings(l.findings || []);
    } catch { /* lint failures are non-critical */ }
    if (saveHistory && !compileControls.zeroRetention) {
      const item = {
        id: String(Date.now()),
        model,
        mode: compileMode,
        prompt,
        controls: compileControls,
        result,
        summary,
        savedAt: new Date().toISOString(),
      };
      setHistory(saveToHistory(item, compileControls.zeroRetention));
    }
    return result;
  }, [applyCompileResult, controls, inputValue, mode, selectedModel, showError]);

  // Actions
  const handleAnalyze = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt before analyzing."); inputRef.current?.focus(); return; }
    await runAction("analyze", async () => {
      const payload = buildCompilePayload({ inputValue, selectedModel, mode, controls });
      const result = await analyze(payload);
      const analysis = result.analysis || result;
      setMetrics([
        ["Original", result.total_tokens],
        ["Segments", result.segment_count],
        ["Opportunity", `${Math.round((result.compression_opportunity || 0) * 100)}%`],
        ["Budget", result.budget_utilization ? `${Math.round(result.budget_utilization * 100)}%` : "-"],
        ["Model", result.model || selectedModel],
      ]);
      setBreakdown(Object.entries(analysis.by_type || {}));
      setEntities(analysis.protected_entities || []);
      setSegments(analysis.segments || result.components || []);
      setReport(_buildAnalyzeReport(result));
      setSemantic(null);
      const l = await lint(inputValue);
      setLintFindings(l.findings || []);
    });
  }, [controls, inputValue, mode, selectedModel, runAction, showError]);

  const handleCompile = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt before compiling."); inputRef.current?.focus(); return; }
    await runAction("compile", async () => runCompileForPrompt());
  }, [inputValue, runAction, runCompileForPrompt, showError]);

  const handleLint = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt before linting."); inputRef.current?.focus(); return; }
    await runAction("lint", async () => {
      const l = await lint(inputValue);
      setLintFindings(l.findings || []);
    });
  }, [inputValue, runAction, showError]);

  const handleGenerate = useCallback(async () => {
    if (!promptIdea.trim()) { showError("Describe the website or app before generating."); return; }
    await runAction("generate", async () => {
      const result = await generatePrompt(promptIdea, promptKind, selectedModel);
      const gen = result.generated_prompt || "";
      setInputValue(gen);
      setLastCompile(null);
      setOptimizedOutput(EMPTY_OUTPUT);
      setMetrics([["Generated", String(gen.length)], ["Type", result.kind || promptKind], ["Model", result.model || selectedModel], ["Next", "Analyze or compile"]]);
      setChanges([{ type: "plan", label: "generated extensive prompt" }]);
      setReport(null);
      setRagRows([]);
      const l = await lint(gen);
      setLintFindings(l.findings || []);
    });
  }, [promptIdea, promptKind, selectedModel, runAction, showError]);

  const handleNim = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt first."); return; }
    if (!window.confirm("This sends text to NVIDIA NIM. Continue?")) return;
    await runAction("nim", async () => {
      const result = await nimSummarize(inputValue, selectedModel);
      const summary = result.summary || "";
      setOptimizedOutput(summary);
      setMetrics([["Original", String(inputValue.length)], ["Optimized", String(summary.length)], ["Mode", "NIM"], ["Model", result.model || selectedModel]]);
      setEntities(result.preservation?.checked_entities || []);
      setChanges([{ type: "change", label: result.preservation?.ok ? "NIM summary preserved protected values." : "NIM summary is missing protected values." }]);
      setReport({
        title: "External NIM Summary",
        traceId: "",
        risk: result.preservation?.ok ? "low" : "review",
        preservation: result.preservation?.ok ? "preserved" : "missing values",
        missingEntities: result.preservation?.missing_entities || [],
        warnings: result.preservation?.ok ? [] : ["NIM summary may be missing protected values."],
        summaryRows: [["Route", "NVIDIA NIM"], ["Model", result.model || selectedModel]],
        transformations: [{ type: "external_summary", reason: "Explicit NIM action confirmed by user." }],
      });
    });
  }, [inputValue, selectedModel, runAction, showError]);

  const handleCopy = useCallback(async () => {
    if (!canExport) return;
    try { await navigator.clipboard.writeText(optimizedOutput); toast("Copied to clipboard", "success"); }
    catch { showError("Clipboard write failed."); }
  }, [canExport, optimizedOutput, showError]);

  const handleExportTxt = useCallback(() => {
    if (!canExport) return;
    const blob = new Blob([optimizedOutput], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "promptcompiler-optimized.txt"; a.click();
    URL.revokeObjectURL(url);
  }, [canExport, optimizedOutput]);

  const handleExportJson = useCallback(() => {
    if (!lastCompile) return;
    const blob = new Blob([JSON.stringify(lastCompile, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "promptcompiler-report.json"; a.click();
    URL.revokeObjectURL(url);
  }, [lastCompile]);

  const importFile = useCallback(async (file) => {
    if (!file) return;
    try { setInputValue(await file.text()); resetWorkbench(); } catch { showError("Could not read file."); }
  }, [resetWorkbench, showError]);

  const loadSample = useCallback(() => {
    const sample = samples.find((s) => s.id === selectedSampleId);
    if (!sample) { showError("Choose a sample first."); return; }
    setInputValue(sample.input || "");
    resetWorkbench();
  }, [samples, selectedSampleId, resetWorkbench, showError]);

  const replayHistory = useCallback((item) => {
    setInputValue(item.prompt || "");
    if (item.mode) setMode(item.mode);
    if (item.controls) setControls({ ...createDefaultControls(), ...item.controls });
    if (item.result) {
      applyCompileResult(
        item.result,
        item.prompt || "",
        item.mode || item.result.mode || mode,
        item.model || selectedModel,
        item.controls || controls,
      );
    }
  }, [applyCompileResult, controls, mode, selectedModel]);

  const rerunHistory = useCallback(async (item, nextMode) => {
    const prompt = item.prompt || "";
    if (!prompt.trim()) return;
    setInputValue(prompt);
    setMode(nextMode || item.mode || mode);
    await runAction("history", async () => runCompileForPrompt({
      prompt,
      compileMode: nextMode || item.mode || mode,
      model: item.model || selectedModel,
      compileControls: item.controls || controls,
      saveHistory: true,
    }));
  }, [controls, mode, runAction, runCompileForPrompt, selectedModel]);

  const compareHistoryModes = useCallback(async (item) => {
    const prompt = item.prompt || inputValue;
    if (!prompt.trim()) { showError("No prompt is available for mode comparison."); return; }
    await runAction("compare", async () => {
      const rows = [];
      for (const compareMode of ["lossless", "balanced", "aggressive", "context_file"]) {
        try {
          const result = await compile(buildCompilePayload({
            inputValue: prompt,
            selectedModel: item.model || selectedModel,
            mode: compareMode,
            controls: item.controls || controls,
          }));
          const c = result.compile || result;
          rows.push({
            mode: compareMode,
            optimizedTokens: result.optimized_token_count ?? c.optimized_tokens ?? 0,
            saved: c.tokens_saved ?? 0,
            risk: c.plan?.risk_level || _riskLabel(c.risk_score),
            warnings: (c.warnings || result.warnings || []).length,
            traceId: result.trace_id,
          });
        } catch (error) {
          rows.push({ mode: compareMode, error: error.message });
        }
      }
      setModeComparisons(rows);
    });
  }, [controls, inputValue, runAction, selectedModel, showError]);

  const handleTraceLookup = useCallback(async (traceId = traceLookupId) => {
    const id = String(traceId || "").trim();
    if (!id) { showError("Enter a trace ID first."); return; }
    setTraceLookupId(id);
    await runAction("trace", async () => {
      setTraceLookupResult(await getTrace(id));
    });
  }, [runAction, showError, traceLookupId]);

  const ctx = {
    inputRef, fileInputRef,
    inputValue, setInputValue,
    optimizedOutput,
    models, modelQuery, setModelQuery, selectedModel, setSelectedModel, visibleModels,
    samples, selectedSampleId, setSelectedSampleId,
    promptIdea, setPromptIdea, promptKind, setPromptKind,
    mode, setMode,
    workflowPresetId, setWorkflowPresetId, applyWorkflowPreset,
    controls, updateControl,
    metrics, breakdown, entities, changes, lintFindings,
    segments, diffItems, ragRows, semantic, report,
    history, lastCompile, modeComparisons, traceLookupId, setTraceLookupId, traceLookupResult,
    error, clearError,
    workingAction, appStatus,
    canExport,
    handleAnalyze, handleCompile, handleLint, handleGenerate, handleNim,
    handleCopy, handleExportTxt, handleExportJson,
    importFile, loadSample, replayHistory, rerunHistory, compareHistoryModes, handleTraceLookup,
    resetWorkbench,
  };

  return <Ctx.Provider value={ctx}>{children}</Ctx.Provider>;
}

export function useWorkbench() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useWorkbench must be inside WorkbenchProvider");
  return ctx;
}

function _buildChanges(compile, result) {
  const plan = (compile.plan || result.plan)?.actions || [];
  const transformations = result.transformations || [];
  const warnings = compile.warnings || result.warnings || [];
  return [
    ...warnings.map((w) => ({ type: "warning", label: w })),
    ...(compile.changes || result.changes || []).map((item) => ({ type: "change", label: _changeLabel(item) })),
    ...transformations.map((item) => ({
      type: item.type || "transform",
      label: `${item.type || "transform"}: ${item.reason || "Applied by compiler."}`,
      tokens: item.estimated_tokens_saved,
    })),
    ...plan.map((a) => ({ type: "plan", label: `${a.action || "plan"}: ${a.reason || ""}` })),
  ];
}

function _changeLabel(item) {
  if (item.type === "duplicate_removed") return `Removed duplicate ${item.segment_id}; kept ${item.kept_segment_id}.`;
  if (item.type === "segment_compacted") return `Compacted ${item.segment_id}; removed ${item.lines_removed} lines.`;
  if (item.type === "rag_chunk_pruned") return `Pruned redundant RAG chunk ${(item.chunk_ids || []).join(", ")}.`;
  return item.type || "Compiler change";
}

function _diffBreakdown(diff) {
  return diff.reduce((acc, item) => { const k = `type:${item.type || "unknown"}`; acc[k] = (acc[k] || 0) + 1; return acc; }, {});
}

function _riskLabel(score) {
  if (score === undefined || score === null) return "unknown";
  if (Number(score) >= 0.66) return "high";
  if (Number(score) >= 0.34) return "medium";
  return "low";
}

function _buildReport(result, compile, mode, model, controls, prompt = "") {
  const warnings = compile.warnings || result.warnings || [];
  const preservation = result.preservation || compile.preservation || {};
  const transformations = result.transformations?.length
    ? result.transformations
    : (compile.plan?.actions || []).map((action) => ({
      type: action.action || "plan",
      reason: action.reason || "",
      estimated_tokens_saved: action.estimated_tokens_saved,
    }));
  const sessionId = result.session_id || controls?.sessionId || "";
  const contextFile = result.context_file || compile.context_file || null;
  const verdict = deriveUsabilityVerdict(result);
  const insight = optimizationInsight(result);
  const proposedPrompt = proposedPromptForDryRun(result);
  const trustProfile = buildTrustProfile({ inputValue: prompt, mode, result });
  const semantic = result.semantic || compile.semantic || {};
  const semanticSummary = semantic.summary || {};
  const contextRows = contextFile
    ? [
      ["Compact tokens", contextFile.compact_tokens],
      ["Decode tokens", contextFile.decode_tokens],
      ["First call", contextFile.net_first_call_savings],
      ["Per reuse", contextFile.net_reuse_savings_per_call],
      ["Break-even", contextFile.break_even_calls || "-"],
      ["Expected calls", contextFile.reuse_expected_calls],
      ["Total reuse", contextFile.total_reuse_savings],
    ]
    : [];
  return {
    title: contextFile
      ? "Reusable Context Report"
      : result.dry_run ? "Dry Run Optimization Report" : "Optimization Report",
    traceId: result.trace_id || "",
    verdict,
    insight,
    trustProfile,
    proposedPrompt,
    risk: compile.plan?.risk_level || _riskLabel(compile.risk_score),
    riskScore: compile.risk_score,
    preservation: preservation.ok ? "preserved" : "review required",
    missingEntities: preservation.missing_entities || [],
    warnings,
    summaryRows: [
      ...contextRows,
      ["Prompt type", trustProfile.promptType],
      ["Trust", trustProfile.confidence.label],
      ["Best mode", trustProfile.bestOptimization],
      ["Semantic", semantic.scorer || "lexical"],
      ["RAG removed", semanticSummary.removed_chunks ?? 0],
      ["Before cost", `$${Number(result.estimated_cost_before_usd || 0).toFixed(6)}`],
      ["After cost", `$${Number(result.estimated_cost_after_usd || 0).toFixed(6)}`],
      ["Cost reduction", `${Number(result.estimated_cost_reduction_percent || 0).toFixed(1)}%`],
      ["Route", result.route?.tier || "local"],
      ["Cache", result.cache?.status || compile.cache_status || "bypass"],
      ["Mode", mode],
      ["Model", model],
      ["Zero retention", result.retention?.zero_retention ? "on" : "off"],
      ["Session", sessionId || "one-off"],
      ["Compaction", sessionId ? "available through session context" : "not active for one-off compile"],
    ],
    transformations,
  };
}

function _buildAnalyzeReport(result) {
  return {
    title: "Verify Report",
    traceId: result.trace_id || "",
    risk: "preflight",
    preservation: `${result.pinned_tokens || 0} pinned tokens`,
    missingEntities: [],
    warnings: [],
    summaryRows: [
      ["Recommendation", result.recommendation?.should_compile ? "compile" : "keep"],
      ["Reason", result.recommendation?.reason || "analysis complete"],
      ["Budget use", result.budget_utilization ? `${Math.round(result.budget_utilization * 100)}%` : "-"],
      ["Zero retention", result.retention?.zero_retention ? "on" : "off"],
      ["Trace", result.trace_id || "-"],
    ],
    transformations: result.components?.map((component) => ({
      type: component.component_type,
      reason: `${component.token_count} tokens, ${component.is_pinned ? "pinned" : "editable"}`,
      estimated_tokens_saved: null,
    })) || [],
  };
}

function _segmentsFromCompile(diff, fallbackSegments) {
  if (fallbackSegments?.length) return fallbackSegments;
  return (diff || []).map((item) => {
    const text = String(item.original_text || item.optimized_text || "");
    return {
      id: item.segment_id,
      type: item.type,
      role: item.role,
      tokens: Math.max(1, Math.round(text.length / 4)),
      pinned: Boolean(item.pinned),
      status: item.status,
      text,
      risk: item.pinned ? 1 : item.status === "removed" ? 0.35 : 0.2,
    };
  });
}

function _ragRows(semantic) {
  if (!semantic?.chunks) return [];
  const removed = new Set(semantic.removed_chunk_ids || []);
  return semantic.chunks
    .filter((chunk) => chunk.segment_type === "rag" || chunk.source)
    .map((chunk) => ({
      id: chunk.id,
      source: chunk.source || chunk.segment_id,
      tokens: chunk.tokens,
      relevance: chunk.query_relevance_score,
      similarity: chunk.inter_chunk_similarity_score,
      risk: chunk.compression_risk_score,
      decision: removed.has(chunk.id) || chunk.decision === "removed" ? "removed" : "kept",
      why: removed.has(chunk.id)
        ? `Removed as redundant with ${chunk.redundant_with || "a stronger retained chunk"}`
        : "Kept for relevance, novelty, protected values, or pinning",
    }));
}
