import { CodeExample, FeatureGrid, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const endpointFlow = [
  { number: "01", title: "Analyze", body: "Inspect the raw prompt, count tokens, identify segments, and surface protected values before changing text." },
  { number: "02", title: "Compile", body: "Apply mode, budget, cache, context, output, and semantic policy to produce optimized prompt output." },
  { number: "03", title: "Inspect", body: "Read diffs, warnings, preservation reports, semantic chunks, route metadata, and cache status from the response." },
  { number: "04", title: "Integrate", body: "Use the SDK or OpenAI-compatible proxy when application code needs the same compile behavior." },
];

const endpoints = [
  { label: "POST", title: "/v1/analyze", body: "Returns segments, duplicate groups, protected entities, and compression opportunity for a prompt." },
  { label: "POST", title: "/v1/compile", body: "Returns optimized text, token deltas, policy metadata, warnings, diffs, semantic signals, and trace identifiers." },
  { label: "POST", title: "/v1/retrieve", body: "Scores retrieval candidates so weak chunks can be pruned before a model request." },
  { label: "POST", title: "/v1/lint", body: "Reports prompt quality findings that explain waste, ambiguity, or risky structure." },
  { label: "GET", title: "/v1/metrics", body: "Summarizes local request and savings metrics for dashboard and review workflows." },
  { label: "POST", title: "/v1/proxy/openai/chat/completions", body: "Accepts chat-completion shaped requests and returns OpenAI-compatible output with PromptCompiler trace headers." },
];

const requestLines = [
  "await fetch('/v1/compile', {",
  "  method: 'POST',",
  "  headers: { 'Content-Type': 'application/json' },",
  "  body: JSON.stringify({",
  "    input: promptText,",
  "    model: 'openai/gpt-oss-120b',",
  "    mode: 'balanced',",
  "    target_token_budget: 2400,",
  "    context_policy: { retrieval_top_k: 4, cache_static_prefix: true },",
  "    output_policy: { format: 'plain', explain: true },",
  "    cache_policy: { enabled: true }",
  "  })",
  "})",
];

export default function ApiReferencePage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="api-reference"
      eyebrow={hero.eyebrow || "API reference"}
      title={hero.title || "Use PromptCompiler as a local API layer before model calls."}
      intro={
        hero.intro ||
        "The API reference explains every local endpoint as part of one flow: analyze context, compile by policy, inspect evidence, then integrate through application code or the proxy."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "docs")}
    >
      <SectionBlock id="api-flow" eyebrow="Request lifecycle" title="API Reference: from raw context to inspectable output">
        <StepGrid steps={content.endpointFlow} fallback={endpointFlow} />
      </SectionBlock>
      <SectionBlock id="api-endpoints" eyebrow="Endpoints" title="Each endpoint maps to a visible product behavior">
        <FeatureGrid items={content.endpoints} fallback={endpoints} />
      </SectionBlock>
      <CodeExample title={content.exampleTitle || "Compile request from a React or server route"} lines={content.requestLines || requestLines} />
    </PageFrame>
  );
}
