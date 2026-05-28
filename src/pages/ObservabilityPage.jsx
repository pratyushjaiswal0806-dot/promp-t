import { PageFrame, SectionBlock, pageActions, FeatureGrid } from "../components/PremiumPageLayout.jsx";
import { CodeBlock } from "../components/CodeBlock.jsx";
import { FadeIn } from "../components/ui/FadeIn.jsx";
import { observability } from "../content/observability.js";

export default function ObservabilityPage({ onNavigate }) {
  const h = observability.hero;
  return (
    <PageFrame pageId="observability" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate, "workbench", "api-reference")}
    >
      <SectionBlock eyebrow="Signals" title="Observability signals">
        <FeatureGrid items={observability.signals} />
      </SectionBlock>
      <SectionBlock eyebrow="Trace Example" title="Sample compile trace">
        <CodeBlock title="Compile trace" lines={observability.traceExample.split("\n")} />
      </SectionBlock>
      {observability.signals.map((s) => (
        <SectionBlock key={s.label} eyebrow={s.label} title="" note={s.body} />
      ))}
    </PageFrame>
  );
}
