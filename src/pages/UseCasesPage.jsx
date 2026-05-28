import { PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";
import { IconTile } from "../components/IconTile.jsx";
import { useCases } from "../content/useCases.js";

export default function UseCasesPage({ onNavigate }) {
  const h = useCases.hero;
  return (
    <PageFrame pageId="use-cases" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate, "workbench", "platform")}
    >
      <SectionBlock eyebrow="Use Cases" title="Real-world applications">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.25rem" }}>
          {useCases.cases.map((c) => (
            <div key={c.title} className="icon-tile" style={{ cursor: "default" }}>
              <h3 className="icon-tile-title">{c.title}</h3>
              <p className="icon-tile-body">{c.body}</p>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.75rem" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{c.outcome}</span>
                {c.savings && <span className="savings-badge" style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem", padding: "0.15rem 0.5rem", borderRadius: "999px", fontSize: "0.65rem", fontWeight: 600, background: "rgba(199,248,90,0.15)", color: "var(--accent-lime)", border: "1px solid rgba(199,248,90,0.3)" }}>~{c.savings}</span>}
              </div>
            </div>
          ))}
        </div>
      </SectionBlock>
    </PageFrame>
  );
}
