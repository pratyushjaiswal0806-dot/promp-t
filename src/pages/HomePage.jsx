import { FeatureGrid, MetricGrid, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const metrics = [
  { label: "Pipeline", value: "4", detail: "parse, protect, compile, measure" },
  { label: "Modes", value: "3", detail: "lossless, balanced, aggressive" },
  { label: "Retention", value: "0", detail: "raw prompt storage by default" },
];

const features = [
  {
    label: "Product",
    title: "A workbench for long-context prompts",
    body: "Paste raw instructions, RAG chunks, tool output, or message JSON and turn it into compact model-ready context.",
  },
  {
    label: "Control",
    title: "Every change is explainable",
    body: "PromptCompiler reports token savings, diffs, protected values, lint findings, cache hints, and semantic signals.",
  },
  {
    label: "Platform",
    title: "Built for local-first workflows",
    body: "The frontend explains the same compiler primitives exposed through the HTTP API, SDK, proxy, and traces.",
  },
];

const stages = [
  { number: "01", title: "Input", body: "Collects prompt text, role blocks, retrieval snippets, and output constraints in one reviewable surface." },
  { number: "02", title: "Policy", body: "Lets users choose compression mode, token budget, retrieval top-k, cache behavior, and dry-run mode." },
  { number: "03", title: "Compile", body: "Runs deterministic transformations while preserving pinned instructions and protected values." },
  { number: "04", title: "Evidence", body: "Shows what changed, what stayed protected, and whether the result is safe to send downstream." },
];

export default function HomePage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="home"
      eyebrow={hero.eyebrow || "Premium prompt operations"}
      title={hero.title || "PromptCompiler turns bloated LLM context into controlled, explainable prompts."}
      intro={
        hero.intro ||
        "A local-first prompt intelligence surface for teams that need to reduce tokens, preserve critical facts, and understand every transformation before model calls are made."
      }
      actions={content.actions || pageActions(onNavigate)}
    >
      <MetricGrid items={content.metrics} fallback={metrics} />
      <SectionBlock
        id="home-product"
        eyebrow="What it does"
        title="One product surface for prompt compression, preservation, routing, and review"
        note="The homepage introduces PromptCompiler as an operating layer between raw context and production LLM calls."
      >
        <FeatureGrid items={content.features} fallback={features} />
      </SectionBlock>
      <SectionBlock
        id="home-flow"
        eyebrow="Core loop"
        title="From raw prompt to trusted payload"
        note="The visible workflow makes the compiler understandable before users move into the workbench."
      >
        <StepGrid steps={content.stages} fallback={stages} />
      </SectionBlock>
    </PageFrame>
  );
}
