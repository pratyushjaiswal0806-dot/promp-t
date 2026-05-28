import { useRef, useCallback } from "react";
import { useWorkbench } from "./context/CompilerContext.jsx";

export function InputPanel() {
  const { inputRef, inputValue, setInputValue, error, clearError, promptIdea, setPromptIdea, promptKind, setPromptKind, handleGenerate, selectedSampleId, setSelectedSampleId, loadSample, importFile, handleLint, handleAnalyze, handleCompile, handleNim, workingAction } = useWorkbench();
  const fileRef = useRef(null);

  const onFileChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) importFile(file);
    if (fileRef.current) fileRef.current.value = "";
  }, [importFile]);

  return (
    <>
      <textarea
        ref={inputRef}
        spellCheck="false"
        value={inputValue}
        onChange={(e) => { setInputValue(e.target.value); clearError(); }}
        placeholder="Paste prompt instructions, messages JSON, or RAG logs here..."
        aria-label="Prompt to compile"
      />
      <div className="action-bar" style={{ padding: "0.5rem 0.75rem", borderTop: "1px solid var(--line)", gap: "0.35rem", flexWrap: "wrap" }}>
        <select value={selectedSampleId} onChange={(e) => setSelectedSampleId(e.target.value)} aria-label="Sample prompt" style={{ background: "var(--surface-dark)", border: "1px solid var(--line)", padding: "0.3rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)" }}>
          <option value="">Load sample</option>
          {useWorkbench().samples.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <button className="btn btn-sm" onClick={loadSample}>Load</button>
        <button className="btn btn-sm" onClick={() => fileRef.current?.click()}>Import</button>
        <input ref={fileRef} type="file" accept=".txt,.json,.md" style={{ display: "none" }} onChange={onFileChange} />
      </div>
      <div className="action-bar" style={{ padding: "0.25rem 0.75rem 0.5rem", gap: "0.35rem", flexWrap: "wrap" }}>
        <input value={promptIdea} onChange={(e) => setPromptIdea(e.target.value)} placeholder="Describe your app..." style={{ flex: 1, minWidth: "120px", background: "var(--surface-dark)", border: "1px solid var(--line)", padding: "0.3rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)", outline: "none" }} />
        <select value={promptKind} onChange={(e) => setPromptKind(e.target.value)} style={{ background: "var(--surface-dark)", border: "1px solid var(--line)", padding: "0.3rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)" }}>
          <option value="website">Website</option>
          <option value="app">App</option>
          <option value="api">API</option>
        </select>
        <button className="btn btn-sm" disabled={workingAction === "generate"} onClick={handleGenerate}>
          {workingAction === "generate" ? "..." : "Generate"}
        </button>
      </div>
      <div className="action-bar" style={{ padding: "0.25rem 0.75rem 0.75rem", gap: "0.35rem" }}>
        <button className="btn btn-sm btn-ghost" disabled={workingAction === "lint"} onClick={handleLint}>
          {workingAction === "lint" ? "Working" : "Lint"}
        </button>
        <button className="btn btn-sm" disabled={workingAction === "analyze"} onClick={handleAnalyze}>
          {workingAction === "analyze" ? "Working" : "Analyze"}
        </button>
        <button className="btn btn-sm btn-primary" disabled={workingAction === "compile"} onClick={handleCompile}>
          {workingAction === "compile" ? "Compiling..." : "Compile"}
        </button>
        <button className="btn btn-sm btn-ghost" disabled={workingAction === "nim"} onClick={handleNim}>
          {workingAction === "nim" ? "NIM..." : "NIM"}
        </button>
      </div>
      {error && <div className="error-box" style={{ margin: "0 0.75rem 0.75rem" }}>{error}</div>}
    </>
  );
}
