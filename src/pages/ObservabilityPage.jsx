import { DetailList, FeatureGrid, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const signals = [
  { label: "Tokens", title: "Savings are visible immediately", body: "Original tokens, optimized tokens, saved tokens, and savings percentage are shown next to the generated output." },
  { label: "Route", title: "Routing context is part of the run", body: "Route tier, reason, selected model, and provider cache hints appear in the compile result instead of hiding in logs." },
  { label: "Cache", title: "Cache policy is explicit", body: "Compile-cache and static-prefix settings are visible controls and visible result metadata." },
  { label: "Semantic", title: "RAG decisions have evidence", body: "Chunk relevance, novelty, similarity, risk, source metadata, and retain/remove decisions are exposed in the semantic inspector." },
];

const reviewLoop = [
  { number: "01", title: "Run", body: "Compile or analyze a prompt from the workbench, API, SDK, or proxy route." },
  { number: "02", title: "Compare", body: "Inspect optimized text, segment diffs, lint findings, protected values, and semantic chunk decisions." },
  { number: "03", title: "Trace", body: "Use trace IDs, route context, cache status, token savings, and policy output for review or metrics." },
  { number: "04", title: "Replay", body: "Use local browser history for quick checks and server metrics for operational visibility." },
];

const terms = [
  { term: "Trace metadata", description: "Request-level facts such as mode, route, cache status, savings, and warnings without treating raw prompt payloads as analytics data." },
  { term: "Diff evidence", description: "A segment-level explanation of what was kept, removed, compacted, pinned, or semantically pruned." },
  { term: "Lint findings", description: "Quality and waste warnings that explain why a prompt may be expensive or vague before it is sent downstream." },
  { term: "History", description: "Browser-local replay entries that help users compare recent compiles without requiring a server-side prompt transcript." },
];

export default function ObservabilityPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="observability"
      eyebrow={hero.eyebrow || "Observability"}
      title={hero.title || "Understand every compile run through metrics, diffs, traces, and warnings."}
      intro={
        hero.intro ||
        "Observability is the product's evidence layer. It explains why the prompt changed, how much context was saved, whether protected values survived, and which signals should guide review."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "api-reference")}
    >
      <SectionBlock id="observability-signals" eyebrow="Live signals" title="The UI turns compiler internals into reviewable signals">
        <FeatureGrid items={content.signals} fallback={signals} />
      </SectionBlock>
      <SectionBlock id="observability-loop" eyebrow="Review loop" title="How teams move from output to evidence">
        <StepGrid steps={content.reviewLoop} fallback={reviewLoop} />
      </SectionBlock>
      <SectionBlock id="observability-terms" eyebrow="Concepts" title="What each observability surface explains">
        <DetailList items={content.terms} fallback={terms} />
      </SectionBlock>
    </PageFrame>
  );
}
