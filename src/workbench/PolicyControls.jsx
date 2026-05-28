import { useWorkbench } from "./context/CompilerContext.jsx";

export function PolicyControls() {
  const { selectedModel, setSelectedModel, modelQuery, setModelQuery, visibleModels, mode, setMode } = useWorkbench();

  return (
    <>
      <div className="sidebar-section-title">Model</div>
      <div className="control-field" style={{ marginBottom: "0.75rem" }}>
        <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} style={{ width: "100%", background: "var(--surface)", border: "1px solid var(--line)", padding: "0.4rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)" }}>
          {visibleModels.map((m) => {
            const id = String(m.id || "");
            const label = m.label ? `${m.label} (${id})` : id;
            return <option key={id} value={id}>{label}</option>;
          })}
        </select>
      </div>
      <div className="control-field" style={{ marginBottom: "0.75rem" }}>
        <input type="search" value={modelQuery} onChange={(e) => setModelQuery(e.target.value)} placeholder="Search models..." style={{ width: "100%", background: "var(--surface)", border: "1px solid var(--line)", padding: "0.4rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)", outline: "none" }} />
      </div>
      <div className="sidebar-section-title">Mode</div>
      <div className="control-field" style={{ marginBottom: "0.75rem" }}>
        <select value={mode} onChange={(e) => setMode(e.target.value)} style={{ width: "100%", background: "var(--surface)", border: "1px solid var(--line)", padding: "0.4rem 0.5rem", color: "var(--text)", fontSize: "0.75rem", borderRadius: "var(--radius-sm)" }}>
          <option value="lossless">Lossless</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </div>
    </>
  );
}
