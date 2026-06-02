import { useWorkbench } from "./context/CompilerContext.jsx";

export function OutputPanel() {
  const { optimizedOutput, handleCopy, handleExportTxt, handleExportJson, canExport, lastCompile, report } = useWorkbench();

  return (
    <>
      <UsabilityVerdict verdict={report?.verdict} />
      <pre id="optimizedOutput" className="optimized-output-text">{optimizedOutput}</pre>
      <ProposedPromptPanel prompt={report?.proposedPrompt} />
      <div className="action-bar output-action-bar">
        <button className="btn btn-sm" type="button" disabled={!canExport} onClick={handleCopy}>
          Copy
        </button>
        <button id="exportTextButton" className="btn btn-sm" type="button" disabled={!canExport} onClick={handleExportTxt}>
          Export Text
        </button>
        <button id="exportJsonButton" className="btn btn-sm" type="button" disabled={!lastCompile} onClick={handleExportJson}>
          Export JSON
        </button>
      </div>
      <OptimizationReport report={report} />
    </>
  );
}

function UsabilityVerdict({ verdict }) {
  if (!verdict) return null;
  return (
    <section id="usabilityVerdict" className={`usability-verdict verdict-${verdict.status || "unknown"}`}>
      <strong>{verdict.label}</strong>
      <span>{verdict.reason}</span>
    </section>
  );
}

function ProposedPromptPanel({ prompt }) {
  if (!prompt) return null;
  return (
    <section id="proposedPromptPanel" className="proposed-prompt-panel">
      <div className="proposed-prompt-heading">
        <strong>Proposed optimized prompt</strong>
        <span>Dry-run preview</span>
      </div>
      <pre>{prompt}</pre>
    </section>
  );
}

function OptimizationReport({ report }) {
  if (!report) {
    return (
      <section id="optimizationReport" className="optimization-report empty-report">
        <div className="empty-state">Run Compile & Optimize to see savings, risk, preservation, route, cache, and transformation evidence.</div>
      </section>
    );
  }

  return (
    <section id="optimizationReport" className="optimization-report">
      <div className="report-heading">
        <div>
          <span className="eyebrow">Verify</span>
          <h3>{report.title || "Optimization Report"}</h3>
        </div>
        <span className={`risk-pill risk-${String(report.risk || "unknown").toLowerCase()}`}>{report.risk || "unknown"}</span>
      </div>

      <div className="report-grid">
        {(report.summaryRows || []).map(([label, value]) => (
          <div key={label} className="report-metric">
            <span>{label}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>

      <div className="report-status-row">
        <span>Preservation: <strong>{report.preservation}</strong></span>
        {report.traceId && <span>Trace: <code>{report.traceId}</code></span>}
      </div>

      {report.missingEntities?.length > 0 && (
        <div className="warning-list">
          <strong>Missing entities</strong>
          {report.missingEntities.map((entity) => <span key={entity}>{entity}</span>)}
        </div>
      )}

      {report.warnings?.length > 0 && (
        <div className="warning-list">
          <strong>Warnings</strong>
          {report.warnings.map((warning) => <span key={warning}>{warning}</span>)}
        </div>
      )}

      <div className="transform-plan">
        <strong>Transformation plan</strong>
        {(report.transformations || []).length ? (
          report.transformations.map((item, index) => (
            <div key={`${item.type || "transform"}-${index}`} className="transform-row">
              <span>{item.type || "transform"}</span>
              <p>{item.reason || "Applied by compiler."}</p>
              {item.estimated_tokens_saved !== null && item.estimated_tokens_saved !== undefined && (
                <em>{item.estimated_tokens_saved}t</em>
              )}
            </div>
          ))
        ) : (
          <div className="empty-state">No transformations were needed.</div>
        )}
      </div>
    </section>
  );
}
