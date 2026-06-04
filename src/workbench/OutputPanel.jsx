import { useWorkbench } from "./context/CompilerContext.jsx";

export function OutputPanel() {
  const { optimizedOutput, handleCopy, handleExportTxt, handleExportJson, canExport, lastCompile, report } = useWorkbench();

  return (
    <>
      <UsabilityVerdict verdict={report?.verdict} />
      <TrustBadge profile={report?.trustProfile} />
      <OptimizationInsight insight={report?.insight} />
      <PromptRecommendation profile={report?.trustProfile} />
      <TokenAccountingPanel accounting={report?.trustProfile?.accounting} />
      <div className="optimized-output-scroll" aria-label="Scrollable optimized prompt">
        <pre id="optimizedOutput" className="optimized-output-text">{optimizedOutput}</pre>
      </div>
      <TrustExplanationRows rows={report?.trustProfile?.explanationRows} />
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

function TrustBadge({ profile }) {
  if (!profile) return null;
  return (
    <section id="trustBadge" className={`trust-badge trust-${profile.confidence?.tone || "unknown"}`}>
      <div>
        <span>Trust</span>
        <strong>{profile.confidence?.label || "Unknown"}</strong>
      </div>
      <p>{profile.confidence?.reason || "Run compile to verify this output."}</p>
    </section>
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

function OptimizationInsight({ insight }) {
  if (!insight) return null;
  return (
    <section id="optimizationInsight" className={`optimization-insight insight-${insight.status || "info"}`}>
      <strong>{insight.title}</strong>
      <span>{insight.body}</span>
    </section>
  );
}

function PromptRecommendation({ profile }) {
  if (!profile) return null;
  return (
    <section id="promptRecommendation" className="prompt-recommendation-card">
      <div>
        <span>Prompt type</span>
        <strong>{profile.promptType}</strong>
      </div>
      <div>
        <span>Best optimization</span>
        <strong>{profile.bestOptimization}</strong>
      </div>
      <div>
        <span>Safe compression</span>
        <strong>{profile.safeCompressionPotential}</strong>
      </div>
    </section>
  );
}

function TokenAccountingPanel({ accounting }) {
  if (!accounting) return null;
  return (
    <section id="tokenAccountingPanel" className="token-accounting-panel">
      <div className="token-accounting-heading">
        <strong>{accounting.label}</strong>
        <span>{accounting.method}</span>
      </div>
      <div className="token-accounting-grid">
        <span>Original <strong>{displayToken(accounting.originalTokens)}</strong></span>
        <span>Optimized <strong>{displayToken(accounting.optimizedTokens)}</strong></span>
        <span>Pasted back <strong>{displayToken(accounting.optimizedReuseTokens)}</strong></span>
        <span>Section overhead <strong>{displayToken(accounting.segmentOverheadTokens)}</strong></span>
      </div>
      <p>{accounting.note}</p>
    </section>
  );
}

function TrustExplanationRows({ rows }) {
  if (!rows?.length) return null;
  return (
    <section id="trustExplanationRows" className="trust-explanation-rows">
      {rows.map((row) => (
        <div key={row.label} className="trust-explanation-row">
          <span>{row.label}</span>
          <p>{row.body}</p>
        </div>
      ))}
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

function displayToken(value) {
  return value === null || value === undefined ? "-" : `${value}t`;
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
