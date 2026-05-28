import { PageFrame, SectionBlock, pageActions, FeatureGrid } from "../components/PremiumPageLayout.jsx";
import { IconTile } from "../components/IconTile.jsx";
import { platform } from "../content/platform.js";

export default function PlatformPage({ onNavigate }) {
  const h = platform.hero;
  return (
    <PageFrame pageId="platform" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate, "api-reference", "security")}
    >
      <SectionBlock eyebrow="Capabilities" title="Integration surface">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
          {platform.capabilities.map((c) => (
            <IconTile key={c.title} icon={c.icon} title={c.title} body={c.body} variant="lime" />
          ))}
        </div>
      </SectionBlock>
      <SectionBlock eyebrow="Components" title="Architecture">
        <div className="details-list-clean">
          {platform.architecture.map((a) => (
            <div key={a.component} className="detail-item-clean">
              <dt>{a.component}</dt>
              <dd>{a.description}</dd>
            </div>
          ))}
        </div>
      </SectionBlock>
      <SectionBlock eyebrow="Stack" title="Tech stack">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
          {platform.techStack.map((t) => (
            <div key={t.name} className="metric-item-clean" style={{ padding: "1rem" }}>
              <strong className="metric-value-clean" style={{ fontSize: "1.2rem" }}>{t.name}</strong>
              <small className="metric-detail-clean">{t.role}</small>
            </div>
          ))}
        </div>
      </SectionBlock>
    </PageFrame>
  );
}
