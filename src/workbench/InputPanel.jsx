import { useRef, useCallback } from "react";
import { useWorkbench } from "./context/CompilerContext.jsx";

export function InputPanel() {
  const {
    inputRef,
    inputValue,
    setInputValue,
    error,
    clearError,
    promptIdea,
    setPromptIdea,
    promptKind,
    setPromptKind,
    handleGenerate,
    samples,
    selectedSampleId,
    setSelectedSampleId,
    loadSample,
    importFile,
    handleLint,
    handleAnalyze,
    handleCompile,
    handleNim,
    workingAction,
  } = useWorkbench();
  const fileRef = useRef(null);

  const onFileChange = useCallback((event) => {
    const file = event.target.files?.[0];
    if (file) importFile(file);
    if (fileRef.current) fileRef.current.value = "";
  }, [importFile]);

  return (
    <>
      <textarea
        id="promptInput"
        ref={inputRef}
        spellCheck="false"
        value={inputValue}
        onChange={(event) => { setInputValue(event.target.value); clearError(); }}
        placeholder="Paste prompt instructions, messages JSON, RAG chunks, or tool logs here..."
        aria-label="Prompt to compile"
      />

      <div className="action-bar input-utility-bar">
        <select
          id="sampleSelect"
          value={selectedSampleId}
          onChange={(event) => setSelectedSampleId(event.target.value)}
          aria-label="Sample prompt"
          className="compact-input"
        >
          <option value="">Load sample</option>
          {samples.map((sample) => <option key={sample.id} value={sample.id}>{sample.name}</option>)}
        </select>
        <button id="loadSampleButton" className="btn btn-sm" type="button" onClick={loadSample}>Load</button>
        <button className="btn btn-sm file-button" type="button" onClick={() => fileRef.current?.click()}>Import</button>
        <input
          id="importInput"
          ref={fileRef}
          type="file"
          accept=".txt,.json,.md"
          className="visually-hidden-file"
          onChange={onFileChange}
        />
      </div>

      <div className="primary-run-bar">
        <button
          id="compileButton"
          className="btn btn-sm btn-primary compile-primary"
          type="button"
          disabled={workingAction === "compile"}
          onClick={handleCompile}
        >
          {workingAction === "compile" ? "Compiling..." : "Compile & Optimize"}
        </button>
      </div>

      <details className="secondary-actions">
        <summary>Secondary actions</summary>
        <div className="action-bar secondary-action-grid">
          <button id="analyzeButton" className="btn btn-sm" type="button" disabled={workingAction === "analyze"} onClick={handleAnalyze}>
            {workingAction === "analyze" ? "Analyzing" : "Analyze"}
          </button>
          <button id="lintButton" className="btn btn-sm btn-ghost" type="button" disabled={workingAction === "lint"} onClick={handleLint}>
            {workingAction === "lint" ? "Linting" : "Lint"}
          </button>
          <button id="nimButton" className="btn btn-sm btn-ghost" type="button" disabled={workingAction === "nim"} onClick={handleNim}>
            {workingAction === "nim" ? "NIM..." : "NIM"}
          </button>
        </div>

        <div className="prompt-generate-row">
          <input
            id="promptIdeaInput"
            value={promptIdea}
            onChange={(event) => setPromptIdea(event.target.value)}
            placeholder="Describe an app or workflow..."
            className="compact-input"
          />
          <select
            id="promptKindSelect"
            value={promptKind}
            onChange={(event) => setPromptKind(event.target.value)}
            className="compact-input compact-select"
          >
            <option value="website">Website</option>
            <option value="app">App</option>
            <option value="api">API</option>
          </select>
          <button id="generatePromptButton" className="btn btn-sm" type="button" disabled={workingAction === "generate"} onClick={handleGenerate}>
            {workingAction === "generate" ? "Generating" : "Generate"}
          </button>
        </div>
      </details>

      {error && <div className="error-box" style={{ margin: "0 0.75rem 0.75rem" }}>{error}</div>}
    </>
  );
}
