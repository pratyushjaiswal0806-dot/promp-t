import { PageFrame, SectionBlock, pageActions, FeatureGrid } from "../components/PremiumPageLayout.jsx";
import { ComparisonTable } from "../components/ComparisonTable.jsx";
import { FadeIn } from "../components/ui/FadeIn.jsx";
import { security } from "../content/security.js";

export default function SecurityPage({ onNavigate }) {
  const h = security.hero;
  return (
    <PageFrame pageId="security" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate, "workbench", "docs")}
    >
      <SectionBlock eyebrow="Principles" title="Security model">
        <FeatureGrid items={security.principles} />
      </SectionBlock>
      <SectionBlock eyebrow="Comparison" title="PromptCompiler vs cloud alternatives">
        <ComparisonTable headers={security.comparisonData.headers} rows={security.comparisonData.rows} />
      </SectionBlock>
    </PageFrame>
  );
}
