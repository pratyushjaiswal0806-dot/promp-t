import { useEffect, useMemo, useRef, useState } from "react";
import {
  docsSections,
  homeHero,
  motionStats,
  navItems,
  apiReferenceSections,
  observabilitySections,
  pageMeta,
  pipelineJourney,
  platformSections,
  securitySections,
  useCases,
  valuePillars,
} from "./data/siteContent.js";
import HomePage from "./pages/HomePage.jsx";
import WorkbenchPage from "./pages/WorkbenchPage.jsx";
import HowItWorksPage from "./pages/HowItWorksPage.jsx";
import PlatformPage from "./pages/PlatformPage.jsx";
import SecurityPage from "./pages/SecurityPage.jsx";
import UseCasesPage from "./pages/UseCasesPage.jsx";
import DocsPage from "./pages/DocsPage.jsx";
import ApiReferencePage from "./pages/ApiReferencePage.jsx";
import ObservabilityPage from "./pages/ObservabilityPage.jsx";

const HISTORY_KEY = "promptcompiler.history.v1";
const INITIAL_MODEL = "openai/gpt-oss-120b";
const EMPTY_OUTPUT = "No optimized prompt yet.";

const pipelineStages = [
  {
    number: "01",
    title: "Parse",
    body: "Splits raw input into structured segments, roles, RAG chunks, tool output, and repeated blocks.",
  },
  {
    number: "02",
    title: "Protect",
    body: "Detects pinned instructions and values like case IDs so compression does not lose critical context.",
  },
  {
    number: "03",
    title: "Compile",
    body: "Applies lossless, balanced, or aggressive transformations with budget-aware routing and cache hints.",
  },
  {
    number: "04",
    title: "Measure",
    body: "Shows savings, diffs, lint findings, semantic signals, and trace metadata for review.",
  },
];

const proofCards = [
  {
    label: "Zero-retention posture",
    title: "Raw payloads stay out of stored traces.",
    body: "Trace rows focus on metadata, savings, transformations, and retention status.",
  },
  {
    label: "Deterministic compression",
    title: "Every visible change has a reason.",
    body: "Duplicate removal, RAG pruning, pin preservation, and warnings all render in the dashboard.",
  },
  {
    label: "Model routing context",
    title: "Route and cache decisions appear in analytics.",
    body: "The result makes it clear whether a compile used cache policy, static prefixes, or route tiers.",
  },
];

const workflowSteps = [
  {
    id: "ready",
    title: "Ready",
    body: "Server, models, and samples initialize.",
  },
  {
    id: "analyze",
    title: "Analyze",
    body: "Segments and protected values are inspected.",
  },
  {
    id: "compile",
    title: "Compile",
    body: "Prompt is compressed and policy checked.",
  },
  {
    id: "measure",
    title: "Measure",
    body: "Diffs, savings, lint, and history update.",
  },
];

const emptyMetrics = [
  ["Original", "-"],
  ["Optimized", "-"],
  ["Saved", "-"],
  ["Savings", "-"],
];

const routePaths = Object.freeze({
  home: "/",
  workbench: "/workbench",
  "how-it-works": "/how-it-works",
  platform: "/platform",
  security: "/security",
  "use-cases": "/use-cases",
  "api-reference": "/api-reference",
  observability: "/observability",
  docs: "/docs",
});

function pageFromHash(hash) {
  const pageId = String(hash || "").replace(/^#/, "");
  return navItems.some((item) => item.id === pageId) ? pageId : null;
}

function pageFromPath(pathname) {
  const normalizedPath = String(pathname || "/").replace(/\/+$/, "") || "/";
  const match = Object.entries(routePaths).find(([, path]) => path === normalizedPath);
  return match?.[0] || null;
}

function pageFromLocation(location) {
  const pathPage = pageFromPath(location?.pathname);
  const hashPage = pageFromHash(location?.hash);
  if (pathPage === "home" && hashPage) return hashPage;
  return pathPage || hashPage || "home";
}

function pathFromPage(pageId) {
  return routePaths[pageId] || routePaths.home;
}

function initialPage() {
  if (typeof window === "undefined") return "home";
  return pageFromLocation(window);
}

function App() {
  const inputRef = useRef(null);
  const canvasRef = useRef(null);
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
  const [metrics, setMetrics] = useState(emptyMetrics);
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
  const [appStatus, setAppStatus] = useState({
    text: "Preparing compiler",
    className: "status-chip",
  });
  const [workflowStage, setWorkflowStage] = useState("ready");
  const [workingAction, setWorkingAction] = useState("");
  const [activePage, setActivePage] = useState(initialPage);

  const filteredModels = useMemo(() => {
    const normalized = modelQuery.trim().toLowerCase();
    if (!normalized) return models;
    return models.filter((modelItem) => {
      const haystack = `${modelItem.id || ""} ${modelItem.label || ""} ${modelItem.provider || ""}`.toLowerCase();
      return haystack.includes(normalized);
    });
  }, [modelQuery, models]);

  const visibleModels = useMemo(() => {
    const selectedOption = models.find((modelItem) => String(modelItem.id || "") === selectedModel) || {
      id: selectedModel,
      label: selectedModel,
    };
    if (!filteredModels.length) return [selectedOption];
    const includesSelectedModel = filteredModels.some((modelItem) => String(modelItem.id || "") === selectedModel);
    return includesSelectedModel ? filteredModels : [selectedOption, ...filteredModels];
  }, [filteredModels, models, selectedModel]);

  useEffect(() => {
    renderEmptyState();
    boot();
  }, []);

  useEffect(() => {
    function syncPageFromLocation() {
      setActivePage(pageFromLocation(window.location));
    }

    window.addEventListener("hashchange", syncPageFromLocation);
    window.addEventListener("popstate", syncPageFromLocation);
    return () => {
      window.removeEventListener("hashchange", syncPageFromLocation);
      window.removeEventListener("popstate", syncPageFromLocation);
    };
  }, []);

  useEffect(() => {
    if (activePage !== "workbench") return undefined;
    return startSignalCanvas(canvasRef.current);
  }, [activePage]);

  async function boot() {
    try {
      const [health, modelPayload, samplePayload] = await Promise.all([
        fetchJson("/api/health"),
        fetchJson("/api/models"),
        fetchJson("/api/samples"),
      ]);
      const nextModels = modelPayload.models || [];
      const nextModel = modelPayload.default_model || health.default_model || selectedModel;
      setModels(nextModels);
      setSamples(samplePayload.samples || []);
      setSelectedModel(nextModel);
      setHistory(readHistory());
      setAppStatus({
        text: health.nim_configured ? "Ready + NIM" : "Ready",
        className: "status-chip ready",
      });
    } catch (bootError) {
      setAppStatus({
        text: "Server unavailable",
        className: "status-chip missing",
      });
    }
  }

  function renderEmptyState() {
    setLastCompile(null);
    setWorkflowStage("ready");
    setOptimizedOutput(EMPTY_OUTPUT);
    setMetrics(emptyMetrics);
    setBreakdown([]);
    setEntities([]);
    setChanges([]);
    setLintFindings([]);
    setSegments([]);
    setDiffItems([]);
    setSemantic(null);
    setHistory(readHistory());
  }

  async function analyzePrompt() {
    if (!inputValue.trim()) {
      showError("Paste a prompt before analyzing.");
      inputRef.current?.focus();
      return;
    }

    await runAction("analyze", async () => {
      setWorkflowStage("analyze");
      const result = await postJson("/api/analyze", {
        input: inputValue,
        model: getControlValue("#modelSelect", selectedModel),
      });
      renderAnalyze(result);
      await renderLintForCurrentPrompt();
      setWorkflowStage("measure");
      clearError();
    });
  }

  async function compilePrompt() {
    if (!inputValue.trim()) {
      showError("Paste a prompt before compiling.");
      inputRef.current?.focus();
      return;
    }

    await runAction("compile", async () => {
      setWorkflowStage("compile");
      const result = await postJson("/v1/compile", compilePayload());
      setLastCompile(result);
      renderCompile(result);
      await renderLintForCurrentPrompt();
      saveHistory(inputValue, result);
      setWorkflowStage("measure");
      clearError();
    });
  }

  async function lintPrompt() {
    if (!inputValue.trim()) {
      showError("Paste a prompt before linting.");
      inputRef.current?.focus();
      return;
    }

    await runAction("lint", async () => {
      setWorkflowStage("analyze");
      await renderLintForCurrentPrompt();
      setWorkflowStage("measure");
      clearError();
    });
  }

  async function generateExtensivePrompt() {
    const idea = promptIdea.trim();
    if (!idea) {
      showError("Describe the website or app before generating a prompt.");
      document.querySelector("#promptIdeaInput")?.focus();
      return;
    }

    await runAction("generate", async () => {
      setWorkflowStage("analyze");
      const result = await postJson("/api/generate-prompt", {
        idea,
        kind: promptKind || "website",
        model: getControlValue("#modelSelect", selectedModel),
      });
      const generatedPrompt = result.generated_prompt || "";
      setInputValue(generatedPrompt);
      setLastCompile(null);
      setOptimizedOutput(EMPTY_OUTPUT);
      setMetrics([
        ["Generated", estimateReadableLength(generatedPrompt)],
        ["Type", result.kind || promptKind || "website"],
        ["Model", result.model || selectedModel],
        ["Next", "Analyze or compile"],
      ]);
      setBreakdown([]);
      setEntities([]);
      setChanges([{ type: "plan", label: "generated extensive prompt" }]);
      setSegments([]);
      setDiffItems([]);
      setSemantic(null);
      await postJson("/v1/lint", { input: generatedPrompt }).then((resultLint) => {
        setLintFindings(resultLint.findings || []);
      });
      setWorkflowStage("measure");
      inputRef.current?.focus();
      clearError();
    });
  }

  async function summarizeWithNim() {
    if (!inputValue.trim()) {
      showError("Paste a prompt before using NIM summarization.");
      inputRef.current?.focus();
      return;
    }

    const approved = window.confirm("This sends the current prompt text to NVIDIA NIM. Continue?");
    if (!approved) return;

    await runAction("nim", async () => {
      setWorkflowStage("compile");
      const result = await postJson("/api/nim/summarize", {
        text: inputValue,
        model: getControlValue("#modelSelect", selectedModel),
      });
      const summary = result.summary || "";
      setOptimizedOutput(summary);
      setMetrics([
        ["Original", estimateReadableLength(inputValue)],
        ["Optimized", estimateReadableLength(summary)],
        ["Mode", "NIM"],
        ["Model", result.model || selectedModel],
      ]);
      setEntities(result.preservation?.checked_entities || []);
      setChanges([
        {
          type: "change",
          label: result.preservation?.ok
            ? "NIM summary preserved protected values."
            : "NIM summary is missing protected values.",
        },
      ]);
      setWorkflowStage("measure");
      clearError();
    });
  }

  async function copyOptimizedPrompt() {
    if (!optimizedOutput || optimizedOutput === EMPTY_OUTPUT) return;

    try {
      await navigator.clipboard.writeText(optimizedOutput);
      setWorkingAction("copied");
      window.setTimeout(() => setWorkingAction(""), 900);
    } catch (copyError) {
      showError("Clipboard write failed. Select and copy the optimized prompt manually.");
    }
  }

  function exportOptimizedText() {
    if (!optimizedOutput || optimizedOutput === EMPTY_OUTPUT) return;
    download("promptcompiler-optimized.txt", optimizedOutput, "text/plain");
  }

  async function exportJson() {
    if (!inputValue.trim()) return;

    await runAction("exportJson", async () => {
      const payload = await postJson("/v1/compile", compilePayload());
      download("promptcompiler-export.json", JSON.stringify(payload, null, 2), "application/json");
    });
  }

  function loadSelectedSample() {
    const sampleId = getControlValue("#sampleSelect", selectedSampleId);
    const sample = samples.find((item) => item.id === sampleId);
    if (!sample) {
      showError("Choose a sample before loading.");
      return;
    }
    setInputValue(sample.input || "");
    setLastCompile(null);
    setOptimizedOutput(EMPTY_OUTPUT);
    setWorkflowStage("ready");
    clearError();
  }

  async function importPromptFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setInputValue(await file.text());
      setLastCompile(null);
      setOptimizedOutput(EMPTY_OUTPUT);
      clearError();
    } catch (fileError) {
      showError("Could not read the selected prompt file.");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function compilePayload() {
    const targetBudget = Number(getControlValue("#targetBudgetInput", ""));
    const maxWords = Number(getControlValue("#maxWordsInput", ""));
    const retrievalTopK = Number(getControlValue("#retrievalTopKInput", ""));
    const selectedMode = getControlValue("#modeSelect", mode);
    return {
      input: inputValue,
      model: getControlValue("#modelSelect", selectedModel),
      mode: selectedMode,
      target_token_budget: Number.isFinite(targetBudget) && targetBudget > 0 ? targetBudget : null,
      context_policy: {
        system_prompt_ref: getControlValue("#systemPromptRef", "") || null,
        cache_static_prefix: getCheckedValue("#cacheStaticPrefix"),
        retrieval_top_k: Number.isFinite(retrievalTopK) && retrievalTopK > 0 ? retrievalTopK : null,
      },
      output_policy: {
        max_words: Number.isFinite(maxWords) && maxWords > 0 ? maxWords : null,
        format: getControlValue("#outputFormat", "plain"),
        explain: getCheckedValue("#explainToggle"),
      },
      cache_policy: {
        enabled: getCheckedValue("#cacheEnabled"),
      },
      dry_run: getCheckedValue("#dryRunInput"),
    };
  }

  async function renderLintForCurrentPrompt() {
    const result = await postJson("/v1/lint", { input: inputValue });
    setLintFindings(result.findings || []);
    return result;
  }

  function renderAnalyze(result) {
    setMetrics([
      ["Original", result.total_tokens],
      ["Segments", result.segment_count],
      ["Opportunity", `${Math.round((result.compression_opportunity || 0) * 100)}%`],
      ["Model", result.model || selectedModel],
    ]);
    setBreakdown(objectRows(result.by_type || {}));
    setEntities(result.protected_entities || []);
    setSegments(result.segments || []);
    setSemantic(null);
  }

  function renderCompile(result) {
    const compile = result.compile || result;
    const optimizedText = result.optimized_prompt || compile.optimized_text || "";
    const originalTokens = result.original_token_count ?? compile.original_tokens ?? 0;
    const optimizedTokens = result.optimized_token_count ?? compile.optimized_tokens ?? 0;
    const tokensSaved = compile.tokens_saved ?? Math.max(0, originalTokens - optimizedTokens);
    const savings = result.token_reduction_percent ?? ((compile.savings_ratio || 0) * 100);

    setOptimizedOutput(optimizedText);
    setMetrics([
      ["Original", originalTokens],
      ["Optimized", optimizedTokens],
      ["Saved", tokensSaved],
      ["Savings", `${Number(savings || 0).toFixed(1)}%`],
      ["Mode", result.mode || getControlValue("#modeSelect", mode)],
      ["Route", result.route?.tier || "-"],
      ["Cache", result.cache?.status || "-"],
      ["Model", result.model || selectedModel],
    ]);
    setBreakdown(diffBreakdownRows(compile.diff || result.diff || []));
    setEntities(result.preservation?.checked_entities || compile.preservation?.checked_entities || []);
    setChanges(buildChangeRows(compile, result));
    setDiffItems(compile.diff || result.diff || []);
    setSemantic(result.semantic || compile.semantic || null);
  }

  function saveHistory(prompt, result) {
    const item = {
      id: String(Date.now()),
      model: result.model || selectedModel,
      prompt,
      result,
      savedAt: new Date().toISOString(),
    };
    const next = [item, ...readHistory()].slice(0, 8);
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
    } catch (historyError) {
      return;
    }
    setHistory(next);
  }

  function replayHistory(item) {
    setInputValue(item.prompt || "");
    setLastCompile(item.result || null);
    if (item.result) renderCompile(item.result);
  }

  async function runAction(actionName, action) {
    setWorkingAction(actionName);
    try {
      await action();
    } catch (actionError) {
      showError(actionError.message);
    } finally {
      setWorkingAction((current) => (current === actionName ? "" : current));
    }
  }

  function showError(message) {
    setError(message);
  }

  function clearError() {
    setError("");
  }

  function navigateToPage(pageId) {
    const nextPage = navItems.some((item) => item.id === pageId) ? pageId : "home";
    setActivePage(nextPage);
    const nextPath = pathFromPage(nextPage);
    if (window.location.pathname !== nextPath) {
      window.history.pushState(null, "", nextPath);
    }
    window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  const canExport = Boolean(optimizedOutput && optimizedOutput !== EMPTY_OUTPUT);
  const isWorkbenchPage = activePage === "workbench";
  const designReference = "nvg8.io inspired dark motion system";
  const action = (label, target, variant = "primary") => ({
    label,
    target,
    path: pathFromPage(target),
    variant,
    onNavigate: navigateToPage,
  });
  const journeySteps = pipelineJourney.map((step) => ({
    number: step.step,
    title: step.title,
    body: step.body,
  }));
  const pageContent = {
    home: {
      hero: { eyebrow: homeHero.eyebrow, title: homeHero.title, intro: homeHero.body },
      actions: [action(homeHero.primaryAction.label, homeHero.primaryAction.target), action(homeHero.secondaryAction.label, homeHero.secondaryAction.target, "secondary")],
      metrics: motionStats,
      features: valuePillars,
      stages: journeySteps.slice(0, 4),
    },
    "how-it-works": {
      hero: {
        eyebrow: pageMeta["how-it-works"].eyebrow,
        title: pageMeta["how-it-works"].title,
        intro: pageMeta["how-it-works"].description,
      },
      actions: [action("Open Workbench", "workbench"), action("Explore Platform", "platform", "secondary")],
      pipeline: journeySteps,
    },
    platform: {
      hero: { eyebrow: pageMeta.platform.eyebrow, title: pageMeta.platform.title, intro: pageMeta.platform.description },
      actions: [action("API reference", "api-reference"), action("Security Model", "security", "secondary")],
      pieces: platformSections.map((section) => ({
        label: section.id.replaceAll("-", " "),
        title: section.title,
        body: `${section.body} Includes ${section.items.join(", ")}.`,
      })),
    },
    security: {
      hero: { eyebrow: pageMeta.security.eyebrow, title: pageMeta.security.title, intro: pageMeta.security.description },
      actions: [action("Open Workbench", "workbench"), action("Read Docs", "docs", "secondary")],
      principles: securitySections.map((section) => ({ label: "Control", title: section.title, body: section.body })),
    },
    "use-cases": {
      hero: { eyebrow: pageMeta["use-cases"].eyebrow, title: pageMeta["use-cases"].title, intro: pageMeta["use-cases"].description },
      actions: [action("Try a Sample", "workbench"), action("Platform Surface", "platform", "secondary")],
      useCases: useCases.map((item) => ({ label: item.outcome, title: item.title, body: item.body })),
    },
    "api-reference": {
      hero: { eyebrow: pageMeta["api-reference"].eyebrow, title: pageMeta["api-reference"].title, intro: pageMeta["api-reference"].description },
      actions: [action("Open Workbench", "workbench"), action("Observability", "observability", "secondary")],
      endpoints: apiReferenceSections,
    },
    observability: {
      hero: { eyebrow: pageMeta.observability.eyebrow, title: pageMeta.observability.title, intro: pageMeta.observability.description },
      actions: [action("Open Workbench", "workbench"), action("API reference", "api-reference", "secondary")],
      signals: observabilitySections,
    },
    docs: {
      hero: { eyebrow: pageMeta.docs.eyebrow, title: pageMeta.docs.title, intro: pageMeta.docs.description },
      actions: [action("Open Workbench", "workbench"), action("How It Works", "how-it-works", "secondary")],
      topics: docsSections.map((section) => ({ label: "Guide", title: section.title, body: section.body })),
      commands: docsSections.flatMap((section) => section.commands),
    },
  };

  function renderPage() {
    if (activePage === "home") return <HomePage content={pageContent.home} onNavigate={navigateToPage} />;
    if (activePage === "how-it-works") return <HowItWorksPage content={pageContent["how-it-works"]} onNavigate={navigateToPage} />;
    if (activePage === "platform") return <PlatformPage content={pageContent.platform} onNavigate={navigateToPage} />;
    if (activePage === "security") return <SecurityPage content={pageContent.security} onNavigate={navigateToPage} />;
    if (activePage === "use-cases") return <UseCasesPage content={pageContent["use-cases"]} onNavigate={navigateToPage} />;
    if (activePage === "api-reference") return <ApiReferencePage content={pageContent["api-reference"]} onNavigate={navigateToPage} />;
    if (activePage === "observability") return <ObservabilityPage content={pageContent.observability} onNavigate={navigateToPage} />;
    if (activePage === "docs") return <DocsPage content={pageContent.docs} onNavigate={navigateToPage} />;
    if (WorkbenchPage) return null;
    return null;
  }

  return (
    <div className="premium-shell" data-design-reference={designReference}>
      <header className="topbar" aria-label="PromptCompiler navigation">
        <button className="brand-lockup brand-button" type="button" data-page-target="home" onClick={() => navigateToPage("home")} aria-label="PromptCompiler home">
          <span className="brand-mark">PC</span>
          <span>
            <strong>PromptCompiler</strong>
            <small>Local context control</small>
          </span>
        </button>
        <nav className="topnav" aria-label="Page sections">
          {navItems.map((item) => (
            <button
              className={activePage === item.id ? "active" : ""}
              type="button"
              aria-current={activePage === item.id ? "page" : undefined}
              data-page-target={item.id}
              data-page-path={pathFromPage(item.id)}
              key={item.id}
              onClick={() => navigateToPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <span id="appStatus" className={appStatus.className}>
          {appStatus.text}
        </span>
      </header>

      <main className="workspace-shell">
        {renderPage()}
        {isWorkbenchPage ? (
          <div className="workspace page-view" data-page-id="workbench">
        <section id="heroPanel" className="hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">Local-first prompt intelligence</p>
            <h1>Compress, protect, and route long LLM context before it reaches the model.</h1>
            <p className="hero-deck">
              Local-first by design, PromptCompiler turns raw prompts, message JSON, RAG chunks, and tool output into
              leaner model-ready context with preserved pins, protected values, traceable diffs, and token analytics.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#inputPanel">
                Open Workbench
              </a>
              <a className="ghost-link" href="#pipelinePanel">
                See How It Works
              </a>
            </div>
          </div>

          <div className="hero-visual" aria-label="PromptCompiler signal map">
            <div className="page-transition-beam" aria-hidden="true"></div>
            <div className="motion-stream" aria-hidden="true"></div>
            <div className="motion-orbit" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div className="motion-marquee" aria-hidden="true">
              <span>analyze</span>
              <span>preserve</span>
              <span>compile</span>
              <span>trace</span>
              <span>route</span>
            </div>
            <canvas id="signalCanvas" ref={canvasRef} width="720" height="520"></canvas>
            <div className="visual-caption">
              <span>Live compile map</span>
              <strong>Parse -&gt; Protect -&gt; Compile -&gt; Measure</strong>
            </div>
          </div>

          <div className="hero-metrics" aria-label="Core platform signals">
            <div>
              <span>Modes</span>
              <strong>3</strong>
              <small>lossless, balanced, aggressive</small>
            </div>
            <div>
              <span>Retention</span>
              <strong>0</strong>
              <small>raw payload storage by default</small>
            </div>
            <div>
              <span>Flow</span>
              <strong>4</strong>
              <small>visible pipeline checkpoints</small>
            </div>
          </div>
        </section>

        <section id="controlPanel" className="panel command-panel full-span">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Command deck</p>
              <h2>Prepare the compile run</h2>
              <p className="section-note">Choose the model, compression policy, retrieval shape, and output constraints.</p>
            </div>
            <div className="button-row">
              <button id="lintButton" className="secondary" type="button" disabled={workingAction === "lint"} onClick={lintPrompt}>
                {workingAction === "lint" ? "Working" : "Lint"}
              </button>
              <button
                id="analyzeButton"
                className="secondary"
                type="button"
                disabled={workingAction === "analyze"}
                onClick={analyzePrompt}
              >
                {workingAction === "analyze" ? "Working" : "Analyze"}
              </button>
              <button
                id="compileButton"
                className="primary"
                type="button"
                disabled={workingAction === "compile"}
                onClick={compilePrompt}
              >
                {workingAction === "compile" ? "Working" : "Compile & Optimize"}
              </button>
              <button id="nimButton" className="secondary" type="button" disabled={workingAction === "nim"} onClick={summarizeWithNim}>
                {workingAction === "nim" ? "Working" : "NIM Summarize"}
              </button>
            </div>
          </div>

          <div className="toolbar-grid">
            <label className="field">
              <span>Model</span>
              <select id="modelSelect" aria-label="Model" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
                {visibleModels.map((modelItem) => {
                  const id = String(modelItem.id || "");
                  const label = modelItem.label ? `${modelItem.label} (${id})` : id;
                  return (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  );
                })}
              </select>
            </label>
            <label className="field">
              <span>Search Models</span>
              <input
                id="modelSearch"
                type="search"
                value={modelQuery}
                onChange={(event) => setModelQuery(event.target.value)}
                placeholder="Search models"
                aria-label="Search models"
              />
            </label>
            <label className="field">
              <span>Samples</span>
              <select id="sampleSelect" aria-label="Sample prompt" value={selectedSampleId} onChange={(event) => setSelectedSampleId(event.target.value)}>
                <option value="">Choose a sample</option>
                {samples.map((sample) => (
                  <option key={sample.id} value={sample.id}>
                    {sample.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="field file-field">
              <span>Prompt File</span>
              <div className="inline-actions">
                <button id="loadSampleButton" className="secondary" type="button" onClick={loadSelectedSample}>
                  Load Sample
                </button>
                <button className="secondary file-button" type="button" onClick={() => fileInputRef.current?.click()}>
                  Import
                </button>
                <input
                  id="importInput"
                  className="visually-hidden-file"
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.json,.md"
                  aria-label="Import prompt file"
                  onChange={importPromptFile}
                />
              </div>
            </div>
          </div>

          <div className="generator-grid">
            <label className="field generator-topic">
              <span>Generate Prompt</span>
              <input
                id="promptIdeaInput"
                type="text"
                value={promptIdea}
                onChange={(event) => setPromptIdea(event.target.value)}
                placeholder="Describe the website or app you want to build"
                aria-label="Prompt generation topic"
              />
            </label>
            <label className="field">
              <span>Prompt Type</span>
              <select id="promptKindSelect" aria-label="Prompt generation type" value={promptKind} onChange={(event) => setPromptKind(event.target.value)}>
                <option value="website">Website</option>
                <option value="app">App</option>
                <option value="landing page">Landing Page</option>
                <option value="dashboard">Dashboard</option>
              </select>
            </label>
            <button
              id="generatePromptButton"
              className="secondary wide-command"
              type="button"
              disabled={workingAction === "generate"}
              onClick={generateExtensivePrompt}
            >
              {workingAction === "generate" ? "Working" : "Generate Extensive Prompt"}
            </button>
          </div>

          <div className="policy-grid">
            <label className="field">
              <span>Compression Mode</span>
              <select id="modeSelect" aria-label="Compression mode" defaultValue="balanced" onChange={(event) => setMode(event.target.value)}>
                <option value="lossless">Lossless</option>
                <option value="balanced">Balanced</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </label>
            <label className="field">
              <span>Target Budget</span>
              <input id="targetBudgetInput" type="number" min="1" step="1" placeholder="Optional token budget" aria-label="Target token budget" />
            </label>
            <label className="field">
              <span>System Ref</span>
              <select id="systemPromptRef" aria-label="System prompt reference" defaultValue="">
                <option value="">None</option>
                <option value="concise">Concise</option>
                <option value="json_only">JSON Only</option>
                <option value="bullets_only">Bullets Only</option>
                <option value="no_explanation">No Explanation</option>
              </select>
            </label>
            <label className="field">
              <span>Output</span>
              <select id="outputFormat" aria-label="Output format" defaultValue="plain">
                <option value="plain">Plain</option>
                <option value="json">JSON</option>
                <option value="bullets">Bullets</option>
              </select>
            </label>
            <label className="field">
              <span>Max Words</span>
              <input id="maxWordsInput" type="number" min="1" step="1" placeholder="Optional" aria-label="Max words" />
            </label>
            <label className="field">
              <span>Retrieve Top K</span>
              <input id="retrievalTopKInput" type="number" min="1" step="1" placeholder="5" aria-label="Retrieval top k" />
            </label>
            <label className="check-field">
              <input id="cacheStaticPrefix" type="checkbox" />
              <span>Cache prefix</span>
            </label>
            <label className="check-field">
              <input id="cacheEnabled" type="checkbox" />
              <span>Compile cache</span>
            </label>
            <label className="check-field">
              <input id="explainToggle" type="checkbox" defaultChecked />
              <span>Explain</span>
            </label>
            <label className="check-field">
              <input id="dryRunInput" type="checkbox" />
              <span>Dry run plan only</span>
            </label>
          </div>
        </section>

        <section id="inputPanel" className="panel input-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">01 Input</p>
              <h2>Raw context</h2>
              <p className="section-note">Paste prompts, provider message JSON, RAG excerpts, logs, or tool output.</p>
            </div>
          </div>
          <textarea
            id="promptInput"
            ref={inputRef}
            spellCheck="false"
            value={inputValue}
            onChange={(event) => {
              setInputValue(event.target.value);
              clearError();
            }}
            placeholder="Paste your prompt, messages JSON, RAG context, or tool output here..."
            aria-label="Prompt to compile"
          ></textarea>
          {error ? (
            <div id="errorBox" className="error-box">
              {error}
            </div>
          ) : (
            <div id="errorBox" className="error-box" hidden></div>
          )}
        </section>

        <section id="outputPanel" className="panel output-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">02 Output</p>
              <h2>Optimized prompt</h2>
              <p className="section-note">Compiled context appears here first, before analytics, so the core result stays visible.</p>
            </div>
            <div className="button-row">
              <button id="copyButton" className="secondary" type="button" disabled={!canExport} onClick={copyOptimizedPrompt}>
                {workingAction === "copied" ? "Copied" : "Copy"}
              </button>
              <button id="exportTextButton" className="secondary" type="button" disabled={!canExport} onClick={exportOptimizedText}>
                Export Text
              </button>
              <button id="exportJsonButton" className="secondary" type="button" disabled={!canExport || workingAction === "exportJson"} onClick={exportJson}>
                {workingAction === "exportJson" ? "Working" : "Export JSON"}
              </button>
            </div>
          </div>
          <pre id="optimizedOutput" aria-live="polite">
            {optimizedOutput}
          </pre>
        </section>

        <section id="pipelinePanel" className="panel full-span pipeline-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">What happens inside</p>
              <h2>What happens inside the compiler pipeline</h2>
              <p className="section-note">
                Each run moves through deterministic checkpoints, then reports what changed and what stayed protected.
              </p>
            </div>
          </div>
          <div className="stage-grid">
            {pipelineStages.map((stage) => (
              <article className="stage-card" key={stage.number}>
                <span>{stage.number}</span>
                <h3>{stage.title}</h3>
                <p>{stage.body}</p>
              </article>
            ))}
          </div>
        </section>

        <aside className="panel workflow-panel" aria-label="Compile workflow state">
          <div className="panel-heading compact-heading">
            <div>
              <p className="eyebrow">Run state</p>
              <h2>Workflow</h2>
            </div>
          </div>
          <ol id="workflowRail" className="workflow-rail">
            {workflowSteps.map((step, index) => {
              const activeIndex = workflowSteps.findIndex((item) => item.id === workflowStage);
              const className = [index === activeIndex ? "active" : "", index < activeIndex ? "complete" : ""].filter(Boolean).join(" ");
              return (
                <li data-stage={step.id} className={className} key={step.id}>
                  <span></span>
                  <strong>{step.title}</strong>
                  <small>{step.body}</small>
                </li>
              );
            })}
          </ol>
        </aside>

        <section id="analyticsPanel" className="panel analytics-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">03 Analytics</p>
              <h2>Run economics</h2>
              <p className="section-note">Token savings, structure, protected values, lint findings, and compiler changes.</p>
            </div>
          </div>
          <div id="metrics" className="metric-grid">
            {metrics.map(([label, value]) => (
              <div className="metric" key={label}>
                <span>{label}</span>
                <strong>{String(value)}</strong>
              </div>
            ))}
          </div>
          <div className="analytics-grid">
            <StackList title="Breakdown" id="breakdown" rows={breakdown} emptyMessage="Analyze or compile a prompt to see structure." />
            <EntityList values={entities} />
            <ChangeList rows={changes} />
            <LintList findings={lintFindings} />
          </div>
        </section>

        <section id="proofPanel" className="panel full-span proof-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Local-first proof layer</p>
              <h2>Built for inspectable agent context</h2>
              <p className="section-note">The interface exposes the important guarantees instead of hiding them behind logs.</p>
            </div>
          </div>
          <div className="proof-grid">
            {proofCards.map((card) => (
              <article className="proof-card" key={card.label}>
                <span>{card.label}</span>
                <strong>{card.title}</strong>
                <p>{card.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="inspectorPanel" className="panel full-span inspector-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">04 Inspector</p>
              <h2>Prompt anatomy</h2>
              <p className="section-note">Segments, pins, protected values, semantic chunks, and compile diff.</p>
            </div>
          </div>
          <div className="inspector-grid">
            <div>
              <h3>Segments</h3>
              <div className="table-wrap">
                <table id="segmentsTable">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Type</th>
                      <th>Role</th>
                      <th>Tokens</th>
                      <th>Status</th>
                      <th>Protected Values</th>
                    </tr>
                  </thead>
                  <tbody>
                    {segments.length ? (
                      segments.map((segment) => (
                        <tr key={segment.id}>
                          <td>{segment.id}</td>
                          <td>{segment.type}</td>
                          <td>{segment.role}</td>
                          <td>{String(segment.tokens)}</td>
                          <td>{segment.pinned ? "Pinned" : "Open"}</td>
                          <td>{(segment.entities || []).join(", ")}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="6">Analyze a prompt to inspect segments.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            <DiffList items={diffItems} />
            <SemanticList semantic={semantic} />
          </div>
        </section>

        <section id="historyPanel" className="panel full-span history-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">05 Memory</p>
              <h2>Local history</h2>
              <p className="section-note">Recent compiles are stored in this browser only for quick replay.</p>
            </div>
          </div>
          <div id="historyList" className="history-list">
            {history.length ? (
              history.map((item) => {
                const original = item.result?.original_token_count ?? item.result?.original_tokens ?? 0;
                const optimized = item.result?.optimized_token_count ?? item.result?.optimized_tokens ?? original;
                const savedTokens = item.result?.tokens_saved ?? item.result?.compile?.tokens_saved ?? Math.max(0, original - optimized);
                return (
                  <button className="history-item" type="button" data-history-id={item.id} key={item.id} onClick={() => replayHistory(item)}>
                    <span>{new Date(item.savedAt).toLocaleString()}</span>
                    <strong>{String(savedTokens)} saved</strong>
                  </button>
                );
              })
            ) : (
              <div className="empty-row">Compile a prompt to create local history.</div>
            )}
          </div>
        </section>
          </div>
        ) : null}
      </main>
    </div>
  );
}

function StackList({ title, id, rows, emptyMessage }) {
  return (
    <div>
      <h3>{title}</h3>
      <div id={id} className="stack-list">
        {rows.length ? (
          rows.map(([label, value]) => (
            <div className="row-pill" key={label}>
              <span>{label}</span>
              <strong>{String(value)}</strong>
            </div>
          ))
        ) : (
          <div className="empty-row">{emptyMessage}</div>
        )}
      </div>
    </div>
  );
}

function EntityList({ values }) {
  return (
    <div>
      <h3>Protected Values</h3>
      <div id="entities" className="stack-list">
        {values.length ? values.map((value) => <div className="entity" key={value}>{value}</div>) : <div className="empty-row">No protected values found.</div>}
      </div>
    </div>
  );
}

function ChangeList({ rows }) {
  return (
    <div>
      <h3>Changes</h3>
      <div id="changes" className="stack-list">
        {rows.length ? (
          rows.map((item, index) => (
            <div className={`change ${item.type || "change"}`} key={`${item.label}-${index}`}>
              {item.label}
            </div>
          ))
        ) : (
          <div className="empty-row">Compile a prompt to see what changed.</div>
        )}
      </div>
    </div>
  );
}

function LintList({ findings }) {
  return (
    <div>
      <h3>Lint</h3>
      <div id="lintFindings" className="stack-list">
        {findings.length ? (
          findings.map((item, index) => (
            <div className={`change ${String(item.severity || "medium")}`} key={`${item.code || "LINT"}-${index}`}>
              {`${item.code || "LINT"}: ${item.message || ""}`}
            </div>
          ))
        ) : (
          <div className="empty-row">Lint a prompt to see token waste.</div>
        )}
      </div>
    </div>
  );
}

function DiffList({ items }) {
  return (
    <div>
      <h3>Diff</h3>
      <div id="diffList" className="diff-list">
        {items.length ? (
          items.map((item, index) => {
            const reason = item.reason || diffReason(item);
            return (
              <div className={`diff-item ${item.status || "kept"}`} key={`${item.segment_id || "segment"}-${index}`}>
                <div className="diff-heading">
                  <strong>{item.segment_id || "segment"}</strong>
                  <span>{item.status || "kept"}</span>
                </div>
                <p>{reason}</p>
              </div>
            );
          })
        ) : (
          <div className="empty-row">Compile a prompt to inspect the diff.</div>
        )}
      </div>
    </div>
  );
}

function SemanticList({ semantic }) {
  const chunks = semantic?.chunks || [];
  if (!chunks.length) {
    return (
      <div>
        <h3>Semantic Signals</h3>
        <div id="semanticScores" className="semantic-list">
          <div className="empty-row">Compile a prompt to inspect semantic chunks.</div>
        </div>
      </div>
    );
  }

  const summary = semantic.summary || {};
  return (
    <div>
      <h3>Semantic Signals</h3>
      <div id="semanticScores" className="semantic-list">
        <div className="semantic-summary">
          <span>{String(summary.retained_chunks ?? chunks.length)} retained</span>
          <span>{String(summary.removed_chunks ?? 0)} removed</span>
          <span>{String(summary.rag_chunks ?? 0)} rag</span>
        </div>
        {chunks.slice(0, 12).map((chunk) => {
          const source = chunk.source || chunk.citation || "no source";
          const type = chunk.segment_type || "chunk";
          const decision = chunk.decision || "retained";
          return (
            <div className={`semantic-item ${decision}`} key={chunk.id || source}>
              <div className="semantic-heading">
                <strong>{chunk.id || "chunk"}</strong>
                <span>{`${type} ${decision}`}</span>
              </div>
              <p>{source}</p>
              <dl>
                <div>
                  <dt>Rel</dt>
                  <dd>{scoreLabel(chunk.query_relevance_score)}</dd>
                </div>
                <div>
                  <dt>Sim</dt>
                  <dd>{scoreLabel(chunk.inter_chunk_similarity_score)}</dd>
                </div>
                <div>
                  <dt>Novel</dt>
                  <dd>{scoreLabel(chunk.novelty_score)}</dd>
                </div>
                <div>
                  <dt>Risk</dt>
                  <dd>{scoreLabel(chunk.compression_risk_score)}</dd>
                </div>
              </dl>
            </div>
          );
        })}
      </div>
    </div>
  );
}

async function fetchJson(url) {
  const response = await fetch(url);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.error || `Request failed with ${response.status}`);
  }
  return data;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch (jsonError) {
    data = { error: text || `Request failed with ${response.status}` };
  }
  if (!response.ok) {
    throw new Error(data.error || `Request failed with ${response.status}`);
  }
  return data;
}

function buildChangeRows(compile, result) {
  const planActions = (compile.plan || result.plan)?.actions || [];
  const warnings = compile.warnings || result.warnings || [];
  return [
    ...warnings.map((warning) => ({ type: "warning", label: warning })),
    ...compileMetadataRows(result).map((item) => ({ type: "plan", label: item })),
    ...(compile.changes || result.changes || []).map((item) => ({ type: "change", label: changeLabel(item) })),
    ...planActions.map((action) => ({ type: "plan", label: planActionLabel(action) })),
  ];
}

function compileMetadataRows(result) {
  const rows = [];
  if (result.route?.tier) {
    rows.push(`route ${result.route.tier}: ${result.route.reason || "policy"}`);
  }
  if (result.cache?.status) {
    rows.push(`cache ${result.cache.status}`);
  }
  if (result.provider_cache_hints?.static_prefix_cacheable) {
    rows.push("provider prefix cacheable");
  }
  if (result.context_policy?.system_prompt_ref) {
    rows.push(`system_ref ${result.context_policy.system_prompt_ref}`);
  }
  if (result.output_policy?.instruction) {
    rows.push(`output ${result.output_policy.instruction}`);
  }
  return rows;
}

function changeLabel(item) {
  if (item.type === "duplicate_removed") {
    return `Removed duplicate ${item.segment_id}; kept ${item.kept_segment_id}.`;
  }
  if (item.type === "segment_compacted") {
    return `Compacted ${item.segment_id}; removed ${item.lines_removed} repeated or omitted lines.`;
  }
  if (item.type === "rag_chunk_pruned") {
    return `Pruned redundant RAG chunk ${(item.chunk_ids || []).join(", ")}; retained ${item.retained_chunk_id}.`;
  }
  return item.type || "Compiler change";
}

function planActionLabel(action) {
  const target = (action.segment_ids || []).join(", ");
  const reason = action.reason || action.action || "Planned transformation";
  return `${action.action || "plan"}${target ? ` on ${target}` : ""}: ${reason}`;
}

function diffReason(item) {
  if (item.status === "removed") {
    return "Removed from optimized prompt.";
  }
  if (item.status === "changed") {
    return "Compacted while preserving protected values and pins.";
  }
  if (item.pinned) {
    return "Pinned segment preserved exactly.";
  }
  return "Segment retained.";
}

function objectRows(values) {
  return Object.entries(values);
}

function diffBreakdownRows(diffItems) {
  const counts = diffItems.reduce((acc, item) => {
    const key = `type:${item.type || "unknown"}`;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  return objectRows(counts);
}

function readHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch (historyError) {
    return [];
  }
}

function getControlValue(selector, fallback) {
  return document.querySelector(selector)?.value ?? fallback;
}

function getCheckedValue(selector) {
  return Boolean(document.querySelector(selector)?.checked);
}

function estimateReadableLength(text) {
  return text ? text.trim().split(/\s+/).filter(Boolean).length : 0;
}

function scoreLabel(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "-";
}

function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function startSignalCanvas(signalCanvas) {
  if (!signalCanvas) return undefined;
  const context = signalCanvas.getContext("2d");
  if (!context) return undefined;

  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  let frame = 0;
  let frameId = 0;

  function draw() {
    const width = signalCanvas.width;
    const height = signalCanvas.height;
    const phase = frame / 28;

    context.clearRect(0, 0, width, height);
    context.fillStyle = "#10120f";
    context.fillRect(0, 0, width, height);

    context.globalAlpha = 1;
    context.strokeStyle = "rgba(255, 253, 246, 0.08)";
    context.lineWidth = 1;
    for (let x = 42; x < width; x += 58) {
      context.beginPath();
      context.moveTo(x, 0);
      context.lineTo(x - 78, height);
      context.stroke();
    }
    for (let y = 52; y < height; y += 64) {
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(width, y + 22);
      context.stroke();
    }

    const nodes = [
      { x: 110, y: 120, color: "#c7f85a", label: "parse" },
      { x: 278, y: 206, color: "#3f8cff", label: "protect" },
      { x: 462, y: 168, color: "#ff6f4e", label: "compile" },
      { x: 598, y: 306, color: "#8b63ff", label: "measure" },
      { x: 250, y: 366, color: "#0f8c7f", label: "diff" },
    ];

    context.lineWidth = 2;
    for (let index = 0; index < nodes.length; index += 1) {
      const current = nodes[index];
      const next = nodes[(index + 1) % nodes.length];
      const pulse = (Math.sin(phase + index) + 1) / 2;
      context.strokeStyle = `rgba(255, 253, 246, ${0.18 + pulse * 0.28})`;
      context.beginPath();
      context.moveTo(current.x, current.y);
      context.bezierCurveTo(
        (current.x + next.x) / 2,
        current.y - 90 + index * 18,
        (current.x + next.x) / 2,
        next.y + 80 - index * 14,
        next.x,
        next.y,
      );
      context.stroke();
    }

    nodes.forEach((node, index) => {
      const pulse = (Math.sin(phase + index * 0.8) + 1) / 2;
      context.fillStyle = node.color;
      context.globalAlpha = 0.18 + pulse * 0.18;
      context.beginPath();
      context.arc(node.x, node.y, 38 + pulse * 10, 0, Math.PI * 2);
      context.fill();

      context.globalAlpha = 1;
      context.fillStyle = node.color;
      context.beginPath();
      context.arc(node.x, node.y, 7, 0, Math.PI * 2);
      context.fill();

      context.fillStyle = "rgba(255, 253, 246, 0.92)";
      context.font = "700 12px ui-sans-serif, system-ui, sans-serif";
      context.fillText(node.label, node.x + 14, node.y + 4);
    });

    const cards = [
      { x: 64, y: 400, w: 146, h: 46, color: "#c7f85a", title: "tokens", value: "-31%" },
      { x: 238, y: 64, w: 160, h: 46, color: "#3f8cff", title: "pins", value: "safe" },
      { x: 438, y: 384, w: 164, h: 46, color: "#ff6f4e", title: "trace", value: "ready" },
    ];

    cards.forEach((card) => {
      context.globalAlpha = 1;
      context.fillStyle = "rgba(255, 253, 246, 0.08)";
      context.strokeStyle = "rgba(255, 253, 246, 0.18)";
      context.lineWidth = 1;
      roundRect(context, card.x, card.y, card.w, card.h, 8);
      context.fill();
      context.stroke();
      context.fillStyle = card.color;
      context.font = "800 11px ui-sans-serif, system-ui, sans-serif";
      context.fillText(card.title.toUpperCase(), card.x + 12, card.y + 18);
      context.fillStyle = "#fffdf6";
      context.font = "800 16px ui-sans-serif, system-ui, sans-serif";
      context.fillText(card.value, card.x + 12, card.y + 36);
    });

    window.__promptCompilerVizReady = true;
    frame += 1;
    if (!prefersReducedMotion) {
      frameId = window.requestAnimationFrame(draw);
    }
  }

  draw();
  return () => {
    if (frameId) window.cancelAnimationFrame(frameId);
  };
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.lineTo(x + width - radius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + radius);
  context.lineTo(x + width, y + height - radius);
  context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  context.lineTo(x + radius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - radius);
  context.lineTo(x, y + radius);
  context.quadraticCurveTo(x, y, x + radius, y);
  context.closePath();
}

export default App;
