import { useWorkbench } from "./context/CompilerContext.jsx";

export function HistoryPanel() {
  const {
    history,
    replayHistory,
    rerunHistory,
    compareHistoryModes,
    modeComparisons,
    traceLookupId,
    setTraceLookupId,
    traceLookupResult,
    handleTraceLookup,
    workingAction,
  } = useWorkbench();

  return (
    <div id="historyList" className="history-workflow">
      <div className="trace-lookup">
        <input
          id="traceLookupInput"
          value={traceLookupId}
          onChange={(event) => setTraceLookupId(event.target.value)}
          placeholder="Open trace by ID"
        />
        <button type="button" className="btn btn-sm" disabled={workingAction === "trace"} onClick={() => handleTraceLookup()}>
          Open Trace
        </button>
      </div>

      {traceLookupResult && (
        <div className="trace-result">
          <strong>{traceLookupResult.trace_id}</strong>
          <span>{traceLookupResult.endpoint} · {traceLookupResult.cache_status} · {traceLookupResult.evaluation_status}</span>
        </div>
      )}

      <div className="history-grid">
        {history.length ? (
          history.map((item) => {
            const c = item.result?.compile || item.result || {};
            const orig = item.result?.original_token_count ?? c.original_tokens ?? 0;
            const opt = item.result?.optimized_token_count ?? c.optimized_tokens ?? orig;
            const saved = c.tokens_saved ?? Math.max(0, orig - opt);
            const traceId = item.result?.trace_id || item.summary?.trace_id;
            return (
              <div className="history-card" key={item.id}>
                <button type="button" onClick={() => replayHistory(item)}>
                  <span className="time">{new Date(item.savedAt).toLocaleTimeString()}</span>
                  <strong className="saved">{String(saved)} tokens saved</strong>
                  <span>{item.mode || item.result?.mode || "balanced"}</span>
                </button>
                <div className="history-actions">
                  <button type="button" onClick={() => rerunHistory(item, "lossless")}>Lossless</button>
                  <button type="button" onClick={() => rerunHistory(item, "balanced")}>Balanced</button>
                  <button type="button" onClick={() => rerunHistory(item, "aggressive")}>Aggressive</button>
                  <button type="button" onClick={() => compareHistoryModes(item)}>Compare</button>
                  {traceId && <button type="button" onClick={() => handleTraceLookup(traceId)}>Trace</button>}
                </div>
              </div>
            );
          })
        ) : (
          <div className="empty-state" style={{ gridColumn: "1 / -1" }}>Compile a prompt to save runs locally.</div>
        )}
      </div>

      {modeComparisons.length > 0 && (
        <div className="table-wrap compare-table">
          <table>
            <thead>
              <tr>
                <th>Mode</th>
                <th>Optimized</th>
                <th>Saved</th>
                <th>Risk</th>
                <th>Warnings</th>
              </tr>
            </thead>
            <tbody>
              {modeComparisons.map((row) => (
                <tr key={row.mode}>
                  <td>{row.mode}</td>
                  <td>{row.error || row.optimizedTokens}</td>
                  <td>{row.error ? "-" : row.saved}</td>
                  <td>{row.error ? "error" : row.risk}</td>
                  <td>{row.error ? row.error : row.warnings}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
