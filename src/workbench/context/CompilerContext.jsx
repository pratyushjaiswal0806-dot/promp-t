import { createContext, useContext, useState, useCallback, useRef, useEffect, useMemo } from "react";
import { getHealth, getModels, getSamples, analyze, compile, lint, generatePrompt, nimSummarize } from "../../services/compiler.js";
import { readHistory, saveToHistory } from "../../services/history.js";
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
  const [metrics, setMetrics] = useState(EMPTY_METRICS);
  const [breakdown, setBreakdown] = useState([]);
  const [entities, setEntities] = useState([]);
  const [changes, setChanges] = useState([]);
  const [lintFindings, setLintFindings] = useState([]);
  const [segments, setSegments] = useState([]);
  const [diffItems, setDiffItems] = useState([]);
  const [semantic, setSemantic] = useState(null);
  const [history, setHistory] = useState([]);
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
    setSemantic(null);
    setHistory(readHistory());
  }, []);

  const runAction = useCallback(async (name, fn) => {
    setWorkingAction(name);
    try { await fn(); } catch (e) { showError(e.message); }
    finally { setWorkingAction((c) => (c === name ? "" : c)); }
  }, [showError]);

  const compilePayload = useCallback(() => ({
    input: inputValue,
    model: selectedModel,
    mode,
    target_token_budget: null,
    dry_run: false,
  }), [inputValue, selectedModel, mode]);

  // Actions
  const handleAnalyze = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt before analyzing."); inputRef.current?.focus(); return; }
    await runAction("analyze", async () => {
      const result = await analyze(inputValue, selectedModel);
      setMetrics([["Original", result.total_tokens], ["Segments", result.segment_count], ["Opportunity", `${Math.round((result.compression_opportunity || 0) * 100)}%`], ["Model", result.model || selectedModel]]);
      setBreakdown(Object.entries(result.by_type || {}));
      setEntities(result.protected_entities || []);
      setSegments(result.segments || []);
      setSemantic(null);
      const l = await lint(inputValue);
      setLintFindings(l.findings || []);
    });
  }, [inputValue, selectedModel, runAction, showError]);

  const handleCompile = useCallback(async () => {
    if (!inputValue.trim()) { showError("Paste a prompt before compiling."); inputRef.current?.focus(); return; }
    await runAction("compile", async () => {
      const result = await compile(compilePayload());
      const c = result.compile || result;
      const text = result.optimized_prompt || c.optimized_text || "";
      const orig = result.original_token_count ?? c.original_tokens ?? 0;
      const opt = result.optimized_token_count ?? c.optimized_tokens ?? 0;
      const saved = c.tokens_saved ?? Math.max(0, orig - opt);
      const savings = result.token_reduction_percent ?? ((c.savings_ratio || 0) * 100);
      setLastCompile(result);
      setOptimizedOutput(text);
      setMetrics([["Original", orig], ["Optimized", opt], ["Saved", saved], ["Savings", `${Number(savings || 0).toFixed(1)}%`], ["Mode", mode], ["Model", selectedModel]]);
      setBreakdown(Object.entries(c.diff ? _diffBreakdown(c.diff) : []));
      setEntities(result.preservation?.checked_entities || c.preservation?.checked_entities || []);
      setChanges(_buildChanges(c, result));
      setDiffItems(c.diff || result.diff || []);
      setSemantic(result.semantic || c.semantic || null);
      const l = await lint(inputValue);
      setLintFindings(l.findings || []);
      const item = { id: String(Date.now()), model: selectedModel, prompt: inputValue, result, savedAt: new Date().toISOString() };
      const next = saveToHistory(item);
      setHistory(next);
    });
  }, [inputValue, selectedModel, mode, compilePayload, runAction, showError]);

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
    if (item.result) {
      setLastCompile(item.result);
      const c = item.result.compile || item.result;
      const text = item.result.optimized_prompt || c.optimized_text || "";
      setOptimizedOutput(text);
      setDiffItems(c.diff || item.result.diff || []);
      setEntities(item.result.preservation?.checked_entities || c.preservation?.checked_entities || []);
      setChanges(_buildChanges(c, item.result));
      setSemantic(item.result.semantic || c.semantic || null);
    }
  }, []);

  const ctx = {
    inputRef, fileInputRef,
    inputValue, setInputValue,
    optimizedOutput,
    models, modelQuery, setModelQuery, selectedModel, setSelectedModel, visibleModels,
    samples, selectedSampleId, setSelectedSampleId,
    promptIdea, setPromptIdea, promptKind, setPromptKind,
    mode, setMode,
    metrics, breakdown, entities, changes, lintFindings,
    segments, diffItems, semantic,
    history, lastCompile,
    error, clearError,
    workingAction, appStatus,
    canExport,
    handleAnalyze, handleCompile, handleLint, handleGenerate, handleNim,
    handleCopy, handleExportTxt,
    importFile, loadSample, replayHistory,
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
  const warnings = compile.warnings || result.warnings || [];
  return [
    ...warnings.map((w) => ({ type: "warning", label: w })),
    ...(compile.changes || result.changes || []).map((item) => ({ type: "change", label: _changeLabel(item) })),
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
