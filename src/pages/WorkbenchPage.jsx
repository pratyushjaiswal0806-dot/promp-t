import { PageFrame, SectionBlock, pageActions, FeatureGrid, StepGrid, DetailList } from "../components/PremiumPageLayout.jsx";

const controls = [
  { label: "model picker", title: "Model picker", body: "Shows the target model because token accounting, routing, and context limits depend on where the optimized prompt will run." },
  { label: "compression mode", title: "Compression mode", body: "Lets users choose whether the compiler should stay lossless, balance savings with meaning, or make aggressive reductions." },
  { label: "token budget", title: "Token budget", body: "Turns optimization into a measurable target instead of a vague shorter-is-better request." },
  { label: "retrieval top-k", title: "Retrieval top-k", body: "Keeps only the most relevant RAG chunks when policy allows semantic or lexical pruning." },
  { label: "output format", title: "Output format", body: "Shapes the optimized prompt for plain text, JSON-like payloads, or downstream application contracts." },
  { label: "dry run", title: "Dry run", body: "Explains potential savings and warnings without changing the final prompt handed to the user." },
];

const workflow = [
  { number: "01", title: "Paste or load", body: "Start with prompt text, generated app specs, sample prompts, or uploaded files." },
  { number: "02", title: "Analyze", body: "Inspect segment types, repeated blocks, protected entities, and lint findings before compilation." },
  { number: "03", title: "Compile", body: "Apply the selected mode and policies to produce a smaller prompt with traceable changes." },
  { number: "04", title: "Export", body: "Copy text, download output, or export JSON evidence for review and automation." },
];

const panels = [
  { term: "Input panel", description: "Where users author, paste, generate, or import the raw source prompt." },
  { term: "Output panel", description: "Displays the optimized prompt and keeps copy/export controls close to the result." },
  { term: "Inspector", description: "Shows diffs, segments, preservation checks, and semantic reports so the user can audit the transformation." },
  { term: "History", description: "Keeps recent compile runs available locally for replay while avoiding raw prompt storage in server traces." },
];

export default function WorkbenchPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};
  return (
    <PageFrame
      pageId="workbench"
      eyebrow={hero.eyebrow || "Interactive workbench"}
      title={hero.title || "Tune, compile, inspect, and export prompts from one dense control surface."}
      intro={
        hero.intro ||
        "The workbench is the hands-on PromptCompiler view: a policy cockpit for deciding how much context to keep, what to protect, and how to prove that the optimized prompt is usable."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "how-it-works")}
    >
      <SectionBlock eyebrow="Controls" title="Controls exist to make optimization explicit" note="Each control maps to compiler behavior, not decoration. Users can predict why the output changed.">
        <FeatureGrid items={content.controls} fallback={controls} />
      </SectionBlock>
      <SectionBlock eyebrow="Workflow" title="The daily compile loop">
        <StepGrid steps={content.workflow} fallback={workflow} />
      </SectionBlock>
      <SectionBlock eyebrow="Panels" title="What each workspace region is responsible for">
        <DetailList items={content.panels} fallback={panels} />
      </SectionBlock>
    </PageFrame>
  );
}
