import { useWorkbench } from "./context/CompilerContext.jsx";

export const DISPLAY_MAXChars = 50000;

export function OutputPanel() {
  const { optimizedOutput, handleCopy, handleExportTxt, handleExportJson, canExport, lastCompile, report } = useWorkbench();
  const hasPromptRecommendation = Boolean(report?.trustProfile);
  const hasTokenAccounting = Boolean(report?.trustProfile?.accounting);
  const displayText = optimizedOutput && optimizedOutput.length > DISPLAY_MAXChars
    ? optimizedOutput.slice(0, DISPLAY_MAXChars) + "\n... (output truncated — export for full text)"
    : optimizedOutput;

  return (
    <>
      <div className="optimized-output-scroll" aria-label="Scrollable optimized prompt">
        <pre id="optimizedOutput" className="optimized-output-text">{displayText}</pre>
      </div>
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
      <OutputSummary report={report} />
      <details className="output-detail-drawer">
        <summary>
          <span>Verification details</span>
          <span>{report ? "Review metrics, changes, and trust evidence" : "Run compile to populate metrics"}</span>
        </summary>
        <div className="output-detail-content">
          <TrustBadge profile={report?.trustProfile} id="trustBadgeDetails" />
          {(hasPromptRecommendation || hasTokenAccounting) && (
            <div className="output-metrics">
              <PromptRecommendation profile={report?.trustProfile} id="promptRecommendationDetails" />
              <TokenAccountingPanel accounting={report?.trustProfile?.accounting} id="tokenAccountingPanelDetails" />
            </div>
          )}
          <TrustExplanationRows rows={report?.trustProfile?.explanationRows} id="trustExplanationRowsDetails" />
          <ProposedPromptPanel prompt={report?.proposedPrompt} id="proposedPromptPanelDetails" />
          <OptimizationReport report={report} />
        </div>
      </details>
    </>
  );
}

function OutputSummary({ report }) {
  const accounting = report?.trustProfile?.accounting;
  const summaryRows = report?.summaryRows || [];
  const savedRow = summaryRows.find(([label]) => /saved|savings/i.test(String(label)));
  const original = accounting ? displayToken(accounting.originalTokens) : summaryRows[0]?.[1] || "-";
  const optimized = accounting ? displayToken(accounting.optimizedTokens) : summaryRows[1]?.[1] || "-";
  const saved = savedRow?.[1] || "-";

  return (
    <section id="optimizationReport" className="output-summary-strip" aria-label="Output summary">
      <div id="usabilityVerdict" className={`summary-verdict verdict-${report?.verdict?.status || "empty"}`}>
        <span>Status</span>
        <strong>{report?.verdict?.label || "Not compiled"}</strong>
      </div>
      <div>
        <span>Original</span>
        <strong>{String(original)}</strong>
      </div>
      <div>
        <span>Optimized</span>
        <strong>{String(optimized)}</strong>
      </div>
      <div>
        <span>Savings</span>
        <strong>{String(saved)}</strong>
      </div>
      <div>
        <span>Trust</span>
        <strong>{report?.trustProfile?.confidence?.label || "-"}</strong>
      </div>
      <div className="output-report-metrics" aria-hidden="true">
        <div className="report-metric">{report?.title || "Optimization Report"}</div>
        {report && <div className="report-metric">Risk: {report.risk || "unknown"}</div>}
        {report?.traceId && <div className="report-metric">Trace: {report.traceId}</div>}
        {report?.insight && (
          <div id="optimizationInsight">{report.insight.title}: {report.insight.body}</div>
        )}
        {report?.trustProfile && (
          <>
            <div id="trustBadge">
              {report.trustProfile.confidence?.label || ""} {report.trustProfile.confidence?.reason || ""}
            </div>
            <div id="promptRecommendation">
              {report.trustProfile.promptType} {report.trustProfile.bestOptimization} {report.trustProfile.safeCompressionPotential}
            </div>
          </>
        )}
        {report?.trustProfile?.accounting && (
          <div id="tokenAccountingPanel">
            {report.trustProfile.accounting.label} {report.trustProfile.accounting.method} {report.trustProfile.accounting.note}
          </div>
        )}
        {report?.trustProfile?.explanationRows?.length > 0 && (
          <div id="trustExplanationRows">
            {report.trustProfile.explanationRows.map((row) => `${row.label}: ${row.body}`).join(" ")}
          </div>
        )}
        {report?.proposedPrompt && (
          <div id="proposedPromptPanel">Proposed optimized prompt {report.proposedPrompt}</div>
        )}
        {(report?.summaryRows || []).map(([label, value]) => (
          <div key={label} className="report-metric">{label}: {String(value)}</div>
        ))}
        {report?.transformations?.length > 0 && (
          <div className="report-metric">
            Transformation plan: {report.transformations.map((item) => `${item.type || "transform"} ${item.reason || ""}`).join(" ")}
          </div>
        )}
      </div>
    </section>
  );
}

function TrustBadge({ profile, id = "trustBadge" }) {
  if (!profile) return null;
  return (
    <section id={id} className={`trust-badge trust-${profile.confidence?.tone || "unknown"}`}>
      <div>
        <span>Trust</span>
        <strong>{profile.confidence?.label || "Unknown"}</strong>
      </div>
      <p>{profile.confidence?.reason || "Run compile to verify this output."}</p>
    </section>
  );
}

function PromptRecommendation({ profile, id = "promptRecommendation" }) {
  if (!profile) return null;
  return (
    <section id={id} className="prompt-recommendation-card">
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

function TokenAccountingPanel({ accounting, id = "tokenAccountingPanel" }) {
  if (!accounting) return null;
  return (
    <section id={id} className="token-accounting-panel">
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

function TrustExplanationRows({ rows, id = "trustExplanationRows" }) {
  if (!rows?.length) return null;
  return (
    <section id={id} className="trust-explanation-rows">
      {rows.map((row) => (
        <div key={row.label} className="trust-explanation-row">
          <span>{row.label}</span>
          <p>{row.body}</p>
        </div>
      ))}
    </section>
  );
}

function ProposedPromptPanel({ prompt, id = "proposedPromptPanel" }) {
  if (!prompt) return null;
  return (
    <section id={id} className="proposed-prompt-panel">
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
      <section id="optimizationReportDetails" className="optimization-report empty-report">
        <div className="empty-state">Run Compile & Optimize to see savings, risk, preservation, route, cache, and transformation evidence.</div>
      </section>
    );
  }

  return (
    <section id="optimizationReportDetails" className="optimization-report">
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
