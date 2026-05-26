import { DetailList, PageFrame, SectionBlock, StepGrid, pageActions } from "../components/PremiumPageLayout.jsx";

const pipeline = [
  { number: "01", title: "Parse", body: "PromptCompiler separates instructions, role content, repeated fragments, retrieval chunks, tool output, and likely protected entities." },
  { number: "02", title: "Protect", body: "Pinned instructions, identifiers, contract terms, case numbers, and values marked as important are guarded before reduction." },
  { number: "03", title: "Score", body: "The compiler estimates token cost, duplicate weight, semantic overlap, and retrieval usefulness before picking transformations." },
  { number: "04", title: "Compile", body: "Lossless, balanced, or aggressive rules rewrite the prompt while respecting budget and preservation policy." },
  { number: "05", title: "Lint", body: "Findings call out vague requests, risky omissions, oversized sections, and places where structure could improve model behavior." },
  { number: "06", title: "Measure", body: "Diffs, token counts, savings, protected values, route context, and cache status turn the result into evidence." },
];

const modes = [
  { term: "Lossless", description: "Removes redundancy and normalizes structure while preserving source meaning as tightly as possible." },
  { term: "Balanced", description: "Targets meaningful savings while keeping the prompt readable, reviewable, and close to the original intent." },
  { term: "Aggressive", description: "Prioritizes budget pressure and may drop lower-value context when policy allows it." },
  { term: "Dry run", description: "Produces analysis without committing to a final transformed prompt, useful for audit and education." },
];

export default function HowItWorksPage({ content = {}, onNavigate }) {
  const hero = content.hero || {};

  return (
    <PageFrame
      pageId="how-it-works"
      eyebrow={hero.eyebrow || "Compiler pipeline"}
      title={hero.title || "A visible pipeline for reducing context without losing the parts that matter."}
      intro={
        hero.intro ||
        "PromptCompiler is explainable by design. It breaks prompt optimization into clear stages so users can understand what was removed, rewritten, protected, and measured."
      }
      actions={content.actions || pageActions(onNavigate, "workbench", "platform")}
    >
      <SectionBlock
        id="how-pipeline"
        eyebrow="Pipeline"
        title="Every stage has a job and a visible output"
        note="The multipage site can teach the compiler as a sequence rather than a black-box optimizer."
      >
        <StepGrid steps={content.pipeline} fallback={pipeline} />
      </SectionBlock>
      <SectionBlock id="how-modes" eyebrow="Modes" title="Compression modes define the risk and savings profile">
        <DetailList items={content.modes} fallback={modes} />
      </SectionBlock>
    </PageFrame>
  );
}
