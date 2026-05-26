import { DetailList, FeatureGrid, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const principles = [
  { label: "Local-first", title: "Compile before provider calls", body: "The workbench and local API let users inspect prompt changes before sending optimized context to external models." },
  { label: "Zero-retention posture", title: "Traces avoid raw prompt storage", body: "Operational records focus on counts, savings, status, and metadata instead of retaining sensitive source text by default." },
  { label: "Preservation", title: "Critical values are checked", body: "Protected entities and pinned instructions are reported so users can catch risky omissions before export." },
];

const controls = [
  { term: "NIM confirmation", description: "External summarization asks for user confirmation because it sends current prompt text to NVIDIA NIM." },
  { term: "Dry run", description: "Lets teams inspect savings and risks without accepting transformed output." },
  { term: "Diff evidence", description: "Shows what changed, making accidental deletion or sensitive leakage easier to identify." },
  { term: "Cache policy", description: "Makes static-prefix and cache behavior explicit instead of silently changing request handling." },
];

const reviewSteps = [
  { number: "01", title: "Classify input", body: "Identify sensitive fields, pinned instructions, and context that cannot be lost." },
  { number: "02", title: "Run analysis", body: "Review segments, lint warnings, protected entities, and compression opportunity." },
  { number: "03", title: "Compile locally", body: "Apply selected policy and keep the optimized output reviewable before downstream use." },
  { number: "04", title: "Approve export", body: "Copy, download, proxy, or send only after the preservation and diff evidence looks correct." },
];

export default function SecurityPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="security"
      eyebrow={hero.eyebrow || "Security and privacy"}
      title={hero.title || "Local-first prompt control with explicit review before external model calls."}
      intro={
        hero.intro ||
        "PromptCompiler is designed for sensitive prompt operations: keep source context local where possible, avoid raw prompt retention in traces, and make risky transformations visible."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "docs")}
    >
      <SectionBlock id="security-principles" eyebrow="Posture" title="Security behavior users can understand">
        <FeatureGrid items={content.principles} fallback={principles} />
      </SectionBlock>
      <SectionBlock id="security-controls" eyebrow="Controls" title="Why safety controls are visible">
        <DetailList items={content.controls} fallback={controls} />
      </SectionBlock>
      <SectionBlock id="security-review" eyebrow="Review loop" title="A practical review path for sensitive prompts">
        <StepGrid steps={content.reviewSteps} fallback={reviewSteps} />
      </SectionBlock>
    </PageFrame>
  );
}
