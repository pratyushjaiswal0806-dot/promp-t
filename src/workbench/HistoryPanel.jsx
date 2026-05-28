import { useWorkbench } from "./context/CompilerContext.jsx";

export function HistoryPanel() {
  const { history, replayHistory } = useWorkbench();

  return (
    <div className="history-grid">
      {history.length ? (
        history.map((item) => {
          const c = item.result?.compile || item.result || {};
          const orig = item.result?.original_token_count ?? c.original_tokens ?? 0;
          const opt = item.result?.optimized_token_count ?? c.optimized_tokens ?? orig;
          const saved = c.tokens_saved ?? Math.max(0, orig - opt);
          return (
            <button className="history-card" key={item.id} type="button" onClick={() => replayHistory(item)}>
              <span className="time">{new Date(item.savedAt).toLocaleTimeString()}</span>
              <strong className="saved">{String(saved)} tokens saved</strong>
            </button>
          );
        })
      ) : (
        <div className="empty-state" style={{ gridColumn: "1 / -1" }}>Compile a prompt to save runs locally.</div>
      )}
    </div>
  );
}
