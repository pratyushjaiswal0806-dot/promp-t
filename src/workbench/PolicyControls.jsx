import { WORKFLOW_PRESETS } from "../services/payload.js";
import { useWorkbench } from "./context/CompilerContext.jsx";

const inputStyle = {
  width: "100%",
  background: "var(--surface)",
  border: "1px solid var(--line)",
  padding: "0.4rem 0.5rem",
  color: "var(--text)",
  fontSize: "0.75rem",
  borderRadius: "var(--radius-sm)",
  outline: "none",
};

const checkboxLabelStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.45rem",
  fontSize: "0.74rem",
  color: "var(--text)",
  marginBottom: "0.45rem",
};

export function PolicyControls() {
  const {
    selectedModel,
    setSelectedModel,
    modelQuery,
    setModelQuery,
    visibleModels,
    mode,
    setMode,
    workflowPresetId,
    applyWorkflowPreset,
    controls,
    updateControl,
  } = useWorkbench();

  const setBool = (key) => (event) => updateControl(key, event.target.checked);
  const setValue = (key) => (event) => updateControl(key, event.target.value);
  const isReusableContext = mode === "context_file";

  return (
    <>
      <div className="sidebar-section-title">Core Setup</div>
      <div className="control-field">
        <label className="control-label" htmlFor="workflowPresetSelect">Preset</label>
        <select
          id="workflowPresetSelect"
          value={workflowPresetId}
          onChange={(event) => applyWorkflowPreset(event.target.value)}
          style={inputStyle}
        >
          <option value="">Manual optimization</option>
          {WORKFLOW_PRESETS.map((preset) => (
            <option key={preset.id} value={preset.id}>{preset.label}</option>
          ))}
        </select>
      </div>

      <div className="control-field">
        <label className="control-label" htmlFor="modelSelect">Model</label>
        <select
          id="modelSelect"
          value={selectedModel}
          onChange={(event) => setSelectedModel(event.target.value)}
          style={inputStyle}
        >
          {visibleModels.map((m) => {
            const id = String(m.id || "");
            const label = m.label || id;
            return <option key={id} value={id}>{label}</option>;
          })}
        </select>
      </div>

      <div className="control-field">
        <label className="control-label" htmlFor="modeSelect">Mode</label>
        <select id="modeSelect" value={mode} onChange={(event) => setMode(event.target.value)} style={inputStyle}>
          <option value="lossless">Lossless</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
          <option value="context_file">Reusable Context</option>
        </select>
      </div>
      <div className="control-field">
        <label className="control-label" htmlFor="targetBudgetInput">Target token budget</label>
        <input
          id="targetBudgetInput"
          type="number"
          min="1"
          inputMode="numeric"
          value={controls.targetTokenBudget}
          onChange={setValue("targetTokenBudget")}
          placeholder="No hard budget"
          style={inputStyle}
        />
      </div>
      <div className="semantic-quick-controls" aria-label="Semantic compression controls">
        <label style={checkboxLabelStyle}>
          <input
            id="autoSemanticInput"
            type="checkbox"
            checked={Boolean(controls.autoSemantic)}
            onChange={setBool("autoSemantic")}
          />
          Auto semantic for RAG
        </label>
        <label style={checkboxLabelStyle}>
          <input
            id="deterministicSemanticInput"
            type="checkbox"
            checked={Boolean(controls.deterministicSemantic)}
            onChange={setBool("deterministicSemantic")}
          />
          Force semantic scoring
        </label>
        <p>Auto mode enables local embedding scoring only when source/citation context is detected.</p>
      </div>

      {isReusableContext && (
        <section className="reusable-context-panel" aria-label="Reusable context options">
          <div className="sidebar-section-title">Reusable Context</div>
          <div className="control-field">
            <label className="control-label" htmlFor="reuseExpectedCallsInput">Expected reuse calls</label>
            <input
              id="reuseExpectedCallsInput"
              type="number"
              min="1"
              inputMode="numeric"
              value={controls.reuseExpectedCalls}
              onChange={setValue("reuseExpectedCalls")}
              placeholder="10"
              style={inputStyle}
            />
          </div>
          <label style={checkboxLabelStyle}>
            <input
              id="includeDecodePromptInput"
              type="checkbox"
              checked={controls.includeDecodePrompt}
              onChange={setBool("includeDecodePrompt")}
            />
            Include decode prompt
          </label>
          <div className="control-field">
            <label className="control-label" htmlFor="validationModeSelect">Validation</label>
            <select
              id="validationModeSelect"
              value={controls.validationMode}
              onChange={setValue("validationMode")}
              style={inputStyle}
            >
              <option value="strict">Strict</option>
              <option value="loose">Loose</option>
            </select>
          </div>
        </section>
      )}

      <details className="advanced-control-group" id="runAdvancedControls">
        <summary>Run options</summary>
        <div className="control-field">
          <input
            id="modelSearch"
            type="search"
            value={modelQuery}
            onChange={(event) => setModelQuery(event.target.value)}
            placeholder="Search models..."
            style={inputStyle}
          />
        </div>
        <label style={checkboxLabelStyle}>
          <input id="dryRunInput" type="checkbox" checked={controls.dryRun} onChange={setBool("dryRun")} />
          Dry run
        </label>
        <label style={checkboxLabelStyle}>
          <input id="zeroRetentionInput" type="checkbox" checked={controls.zeroRetention} onChange={setBool("zeroRetention")} />
          Zero-retention trace
        </label>
        <label style={checkboxLabelStyle}>
          <input id="cacheEnabled" type="checkbox" checked={controls.cacheEnabled} onChange={setBool("cacheEnabled")} />
          Cache-enabled compile
        </label>
      </details>

      <details className="advanced-control-group" id="outputAdvancedControls">
        <summary>Output</summary>
        <div className="control-field">
          <select id="outputFormat" value={controls.outputFormat} onChange={setValue("outputFormat")} style={inputStyle}>
            <option value="plain">Plain text</option>
            <option value="json">JSON only</option>
            <option value="bullets">Bullets only</option>
          </select>
        </div>
        <div className="control-field">
          <label className="control-label" htmlFor="maxWordsInput">Max words</label>
          <input
            id="maxWordsInput"
            type="number"
            min="1"
            inputMode="numeric"
            value={controls.maxWords}
            onChange={setValue("maxWords")}
            placeholder="No word cap"
            style={inputStyle}
          />
        </div>
        <label style={checkboxLabelStyle}>
          <input id="explainToggle" type="checkbox" checked={controls.explain} onChange={setBool("explain")} />
          Allow explanation
        </label>
      </details>

      <details className="advanced-control-group" id="contextAdvancedControls">
        <summary>Context</summary>
        <div className="control-field">
          <select id="systemPromptRef" value={controls.systemPromptRef} onChange={setValue("systemPromptRef")} style={inputStyle}>
            <option value="">No system ref</option>
            <option value="concise">concise</option>
            <option value="json_only">json_only</option>
            <option value="bullets_only">bullets_only</option>
            <option value="no_explanation">no_explanation</option>
          </select>
        </div>
        {!isReusableContext && (
          <>
            <div className="control-field">
              <label className="control-label" htmlFor="reuseExpectedCallsInput">Expected reuse calls</label>
              <input
                id="reuseExpectedCallsInput"
                type="number"
                min="1"
                inputMode="numeric"
                value={controls.reuseExpectedCalls}
                onChange={setValue("reuseExpectedCalls")}
                placeholder="10"
                style={inputStyle}
              />
            </div>
            <label style={checkboxLabelStyle}>
              <input
                id="includeDecodePromptInput"
                type="checkbox"
                checked={controls.includeDecodePrompt}
                onChange={setBool("includeDecodePrompt")}
              />
              Include decode prompt
            </label>
            <div className="control-field">
              <label className="control-label" htmlFor="validationModeSelect">Validation</label>
              <select
                id="validationModeSelect"
                value={controls.validationMode}
                onChange={setValue("validationMode")}
                style={inputStyle}
              >
                <option value="strict">Strict</option>
                <option value="loose">Loose</option>
              </select>
            </div>
          </>
        )}
        <div className="control-field">
          <label className="control-label" htmlFor="retrievalTopKInput">Retrieval top-k</label>
          <input
            id="retrievalTopKInput"
            type="number"
            min="1"
            inputMode="numeric"
            value={controls.retrievalTopK}
            onChange={setValue("retrievalTopK")}
            placeholder="Backend default"
            style={inputStyle}
          />
        </div>
        <label style={checkboxLabelStyle}>
          <input id="cacheStaticPrefix" type="checkbox" checked={controls.cacheStaticPrefix} onChange={setBool("cacheStaticPrefix")} />
          Cache static prefix
        </label>
      </details>

      <details className="advanced-control-group" id="toolsAdvancedControls">
        <summary>Tools + trace</summary>
        <label style={checkboxLabelStyle}>
          <input id="toolCompactInput" type="checkbox" checked={controls.toolCompact} onChange={setBool("toolCompact")} />
          Tool compaction
        </label>
        <div className="control-field">
          <label className="control-label" htmlFor="maxToolsInput">Max tools</label>
          <input
            id="maxToolsInput"
            type="number"
            min="1"
            inputMode="numeric"
            value={controls.maxTools}
            onChange={setValue("maxTools")}
            placeholder="Backend default"
            style={inputStyle}
          />
        </div>
        <div className="control-field">
          <label className="control-label" htmlFor="sessionIdInput">Session ID</label>
          <input
            id="sessionIdInput"
            value={controls.sessionId}
            onChange={setValue("sessionId")}
            placeholder="Optional"
            style={inputStyle}
          />
        </div>
      </details>
    </>
  );
}
