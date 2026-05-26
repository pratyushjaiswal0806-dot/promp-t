import { CodeExample, DetailList, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const gettingStarted = [
  { number: "01", title: "Start the app", body: "Run the local PromptCompiler server and open the Vite frontend served by the existing project workflow." },
  { number: "02", title: "Load context", body: "Paste a prompt, import a file, load a sample, or generate an extensive prompt from a product idea." },
  { number: "03", title: "Choose policy", body: "Pick the model, mode, token budget, retrieval setting, cache behavior, and output constraints." },
  { number: "04", title: "Review evidence", body: "Check savings, diffs, lint findings, protected values, route metadata, semantic reports, and export options." },
];

const concepts = [
  { term: "Mode", description: "The savings and risk profile for the compile run: lossless, balanced, or aggressive." },
  { term: "Target token budget", description: "The desired output size used to guide reductions and explain whether the goal was met." },
  { term: "Protected entities", description: "Values and pinned instructions that should survive compression and appear in the preservation report." },
  { term: "Semantic report", description: "Signals that explain retrieval overlap, chunk relevance, or meaning-preservation checks." },
  { term: "Trace", description: "Operational metadata about a run, useful for metrics and review without storing raw prompts by default." },
];

const apiLines = [
  "POST /v1/compile",
  "",
  "{",
  "  \"input\": \"Long prompt text...\",",
  "  \"model\": \"openai/gpt-oss-120b\",",
  "  \"mode\": \"balanced\",",
  "  \"context_policy\": { \"retrieval_top_k\": 4 },",
  "  \"output_policy\": { \"explain\": true },",
  "  \"cache_policy\": { \"enabled\": true },",
  "  \"dry_run\": false",
  "}",
];

export default function DocsPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="docs"
      eyebrow={hero.eyebrow || "Docs and quickstart"}
      title={hero.title || "Learn the concepts, then compile your first production-ready prompt."}
      intro={
        hero.intro ||
        "The docs page gives users a practical map of the local app, the workbench controls, the API contract, and the core terms they need before integrating PromptCompiler."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "platform")}
    >
      <SectionBlock id="docs-start" eyebrow="Quickstart" title="Getting started">
        <StepGrid steps={content.gettingStarted} fallback={gettingStarted} />
      </SectionBlock>
      <SectionBlock id="docs-concepts" eyebrow="Concepts" title="Terms users should know">
        <DetailList items={content.concepts} fallback={concepts} />
      </SectionBlock>
      <CodeExample title={content.apiTitle || "Minimal compile request"} lines={content.apiLines || apiLines} />
    </PageFrame>
  );
}
