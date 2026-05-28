import { useWorkbench } from "./context/CompilerContext.jsx";

export function OutputPanel() {
  const { optimizedOutput, handleCopy, handleExportTxt, canExport } = useWorkbench();

  return (
    <>
      <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{optimizedOutput}</pre>
      <div className="action-bar" style={{ padding: "0.5rem 0.75rem", borderTop: "1px solid var(--line)", gap: "0.5rem" }}>
        <button className="btn btn-sm" disabled={!canExport} onClick={handleCopy}>
          Copy
        </button>
        <button className="btn btn-sm" disabled={!canExport} onClick={handleExportTxt}>
          Export
        </button>
      </div>
    </>
  );
}
