import { FeatureGrid, PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";

const useCases = [
  {
    label: "Product teams",
    title: "Turn large product briefs into focused implementation prompts",
    body: "Compress PRDs, acceptance criteria, examples, and constraints while preserving product decisions and required outputs.",
  },
  {
    label: "Support operations",
    title: "Reduce case context before model-assisted replies",
    body: "Keep customer IDs, dates, policy terms, and escalation facts visible while removing repeated transcript noise.",
  },
  {
    label: "RAG applications",
    title: "Prune retrieval chunks before expensive model calls",
    body: "Use lexical or semantic signals to keep the most useful context and explain why other chunks were dropped.",
  },
  {
    label: "Agents",
    title: "Clean tool output before the next reasoning step",
    body: "Summarize logs, traces, and tool results into compact context without losing important operational facts.",
  },
  {
    label: "Legal and compliance",
    title: "Audit what changed before external processing",
    body: "Diffs, preservation checks, and zero-retention traces help reviewers decide whether a prompt can be sent onward.",
  },
  {
    label: "Developers",
    title: "Add prompt compression to existing apps",
    body: "Use the API, SDK, or proxy route to add token reduction without rebuilding application prompt orchestration from scratch.",
  },
];

const outcomes = [
  { label: "Cost", title: "Lower repeated context spend", body: "Repeated blocks, oversized retrieval context, and tool noise become measurable optimization targets." },
  { label: "Quality", title: "More structured model inputs", body: "Linting and output policy make prompts easier for models and humans to inspect." },
  { label: "Governance", title: "Evidence for prompt changes", body: "Teams can review diffs, savings, and preservation reports instead of trusting an opaque optimizer." },
];

export default function UseCasesPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="use-cases"
      eyebrow={hero.eyebrow || "Use cases"}
      title={hero.title || "PromptCompiler fits any workflow where context is valuable but too expensive to send raw."}
      intro={
        hero.intro ||
        "Use cases range from product planning and support automation to RAG, agent loops, compliance review, and developer platform integrations."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "platform")}
    >
      <SectionBlock id="use-case-grid" eyebrow="Teams" title="Where the compiler helps">
        <FeatureGrid items={content.useCases} fallback={useCases} />
      </SectionBlock>
      <SectionBlock id="use-case-outcomes" eyebrow="Outcomes" title="Why teams add a compiler layer">
        <FeatureGrid items={content.outcomes} fallback={outcomes} />
      </SectionBlock>
    </PageFrame>
  );
}
