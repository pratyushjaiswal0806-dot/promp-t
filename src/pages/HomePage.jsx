import { PageFrame, SectionBlock, FeatureGrid, MetricGrid, StepGrid, CodeExample, pageActions } from "../components/PremiumPageLayout.jsx";
import { home } from "../content/home.js";

export default function HomePage({ onNavigate }) {
  const h = home.hero;
  return (
    <PageFrame pageId="home" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate)}
    >
      {/* Key metrics */}
      <SectionBlock eyebrow="By the numbers" title="What you get">
        <MetricGrid items={home.metrics} />
      </SectionBlock>

      {/* Before / After comparison */}
      <SectionBlock eyebrow={home.beforeAfter.eyebrow} title={home.beforeAfter.title}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "0.5rem" }}>
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--muted)", fontFamily: "var(--font-mono)", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
              {home.beforeAfter.before.label}
            </div>
            <pre style={{
              background: "var(--surface-dark)", border: "2px solid var(--line)",
              padding: "1rem", fontSize: "0.72rem", lineHeight: "1.5",
              fontFamily: "var(--font-mono)", color: "var(--text)",
              whiteSpace: "pre-wrap", overflowX: "auto",
            }}>{home.beforeAfter.before.code}</pre>
          </div>
          <div>
            <div style={{ fontSize: "0.65rem", color: "var(--accent-lime-text)", fontFamily: "var(--font-mono)", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
              {home.beforeAfter.after.label}
            </div>
            <pre style={{
              background: "rgba(199,248,90,0.06)", border: "2px solid var(--accent-lime)",
              padding: "1rem", fontSize: "0.72rem", lineHeight: "1.5",
              fontFamily: "var(--font-mono)", color: "var(--accent-lime-text)",
              whiteSpace: "pre-wrap", overflowX: "auto",
            }}>{home.beforeAfter.after.code}</pre>
          </div>
        </div>
      </SectionBlock>

      {/* Feature grid */}
      <SectionBlock eyebrow="How it works" title="Parse, protect, compile, measure">
        <FeatureGrid items={home.features} />
      </SectionBlock>

      {/* Pipeline stages */}
      <SectionBlock eyebrow="Workflow" title="Four steps from raw to optimized">
        <StepGrid steps={home.stages} />
      </SectionBlock>

      {/* Benchmark verification */}
      <SectionBlock eyebrow="Benchmarks" title="Verified on 30 diverse prompt pairs">
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {home.benchmarks.map((b, i) => (
            <div key={i} style={{
              display: "grid", gridTemplateColumns: "140px 1fr",
              gap: "1rem", alignItems: "center",
              padding: "0.6rem 0.75rem",
              borderLeft: "3px solid var(--accent-lime)",
              background: "var(--surface-dark)",
            }}>
              <strong style={{ fontSize: "0.8rem", color: "var(--accent-lime)" }}>{b.corpus}</strong>
              <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{b.coverage}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", border: "1px solid var(--line)", background: "var(--surface-dark)", fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--muted)" }}>
          $ python3 -m benchmarks.evaluate<br />
          <span style={{ color: "var(--accent-lime)" }}>→ results written to benchmarks/results/baseline.json</span>
        </div>
      </SectionBlock>

      {/* Use case cards */}
      <SectionBlock title="Built for real LLM context problems">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.5rem", padding: "1rem 0" }}>
          {home.useCaseLinks.map((uc, index) => {
            const styleClass = `card-premium zine-style-${(index % 3) + 1}`;
            return (
              <div key={uc.title} className={styleClass}>
                <div className="card-premium-img-wrap">
                  <div className="card-premium-img-overlay"></div>
                  <img src={uc.image} alt={uc.title} className="card-premium-img" />
                </div>
                <h3 className="card-premium-title">{uc.title}</h3>
                <p className="card-premium-body">{uc.body}</p>
                <button type="button" className="card-premium-button" onClick={() => onNavigate(uc.target)}>
                  Learn More →
                </button>
              </div>
            );
          })}
        </div>
      </SectionBlock>

      {/* CLI quick start */}
      <SectionBlock eyebrow="CLI" title="One command to compile">
        <CodeExample
          title="Compile a prompt file"
          lines={[
            "$ promptcompiler compile input.json --mode balanced",
            "",
            "{",
            "  original_tokens: 1847,",
            "  optimized_tokens: 1243,",
            '  tokens_saved: 604,',
            '  savings_ratio: 0.327,',
            '  changes: [',
            '    { type: "duplicate_removed", removed: 2 },',
            '    { type: "segment_compacted", removed: 8 },',
            '  ]',
            "}",
          ]}
        />
      </SectionBlock>
    </PageFrame>
  );
}