import { CodeExample, DetailList, FeatureGrid, PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";

const pieces = [
  { label: "HTTP API", title: "/v1/compile", body: "Accepts prompt input plus context, output, cache, and dry-run policy for application integration." },
  { label: "Analysis", title: "/api/analyze and /v1/lint", body: "Expose segment inspection and quality checks before a team commits to optimized output." },
  { label: "SDK", title: "PromptCompilerClient", body: "Gives Python workflows a stable compile, lint, and metrics client without hand-writing requests." },
  { label: "Proxy", title: "OpenAI-compatible route", body: "Lets applications place PromptCompiler in front of chat completions to reduce context before forwarding." },
  { label: "Storage", title: "Session and metrics traces", body: "Keeps operational metadata, savings, request counts, and retention posture available for review." },
  { label: "Model context", title: "Routing and cache hints", body: "Surfaces route tier, selected model, cache status, and static prefix policy in the result." },
];

const contracts = [
  { term: "Input", description: "Raw prompt text plus optional model, mode, target token budget, and policy objects." },
  { term: "Output", description: "Optimized prompt, token counts, savings percentage, preservation report, diff list, semantic report, route metadata, and cache status." },
  { term: "Trace", description: "Request metadata is suitable for product analytics without requiring raw prompt retention." },
];

const exampleLines = [
  "const payload = {",
  "  input: promptText,",
  "  model: \"openai/gpt-oss-120b\",",
  "  mode: \"balanced\",",
  "  target_token_budget: 2400,",
  "  output_policy: { explain: true },",
  "};",
  "",
  "const result = await fetch(\"/v1/compile\", {",
  "  method: \"POST\",",
  "  headers: { \"Content-Type\": \"application/json\" },",
  "  body: JSON.stringify(payload),",
  "}).then((response) => response.json());",
];

export default function PlatformPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="platform"
      eyebrow={hero.eyebrow || "Developer platform"}
      title={hero.title || "APIs, SDKs, proxy flows, and traces for production prompt operations."}
      intro={
        hero.intro ||
        "The platform page explains how PromptCompiler moves beyond the visual workbench into application code, automation, routing, observability, and repeatable prompt governance."
      }
      actions={content.actions || pageActions(onNavigate, "docs", "security")}
    >
      <SectionBlock id="platform-pieces" eyebrow="Surface area" title="Platform pieces">
        <FeatureGrid items={content.pieces} fallback={pieces} />
      </SectionBlock>
      <SectionBlock id="platform-contracts" eyebrow="Contracts" title="Inputs and outputs are intentionally structured">
        <DetailList items={content.contracts} fallback={contracts} />
      </SectionBlock>
      <CodeExample title={content.exampleTitle || "Compile from an app frontend or server route"} lines={content.exampleLines || exampleLines} />
    </PageFrame>
  );
}
