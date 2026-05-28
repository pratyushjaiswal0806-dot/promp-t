import { PageFrame, SectionBlock, pageActions } from "../components/PremiumPageLayout.jsx";
import { FlowDiagram } from "../components/FlowDiagram.jsx";
import { Accordion } from "../components/Accordion.jsx";
import { FadeIn } from "../components/ui/FadeIn.jsx";
import { howItWorks } from "../content/howItWorks.js";

const pipelineDetail = [
  { number: "01", title: "Parse", body: "Splits raw input into structured segments with roles, RAG chunks, tool output, and repeated blocks. Output: ContextGraph with typed segments.", input: "Raw text", output: "ContextGraph" },
  { number: "02", title: "Normalize", body: "Canonicalizes whitespace, trims segments, and normalizes line endings for consistent downstream processing.", input: "ContextGraph", output: "Normalized segments" },
  { number: "03", title: "Dedup", body: "Identifies and removes duplicate or near-duplicate segments using content-addressed hashing.", input: "Normalized segments", output: "Deduped segments" },
  { number: "04", title: "Entity Resolve", body: "Scans for pinned instructions, case IDs, URLs, names, and other protected entities. Tracks them for warning generation.", input: "Deduped segments", output: "Entity[]" },
  { number: "05", title: "Summarize", body: "Semantic scoring removes low-value RAG chunks while preserving protected entities and critical context.", input: "Segments + Entities", output: "Scored segments" },
  { number: "06", title: "Budget", body: "Applies token budget constraints: lossless (no reduction), balanced (moderate), aggressive (maximum).", input: "Scored segments", output: "Budgeted segments" },
  { number: "07", title: "Emit", body: "Serializes the optimized context graph back to text with trace metadata, diffs, and savings report.", input: "Budgeted segments", output: "Optimized text + Trace" },
];

export default function HowItWorksPage({ onNavigate }) {
  const h = howItWorks.hero;
  return (
    <PageFrame pageId="how-it-works" eyebrow={h.eyebrow} title={h.title} intro={h.intro}
      actions={pageActions(onNavigate)}
    >
      <SectionBlock eyebrow="Pipeline" title="7 deterministic passes">
        <FlowDiagram nodes={howItWorks.flowNodes} />
      </SectionBlock>
      <SectionBlock eyebrow="Detail" title="What each pass does">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {pipelineDetail.map((p) => (
            <FadeIn key={p.number} direction="up">
              <div className="step-item-clean" style={{ display: "flex", gap: "1.5rem", padding: "1.25rem", border: "1px solid var(--line)", borderRadius: "var(--radius-md)" }}>
                <span className="step-number-clean" style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--accent-lime)", minWidth: "40px" }}>{p.number}</span>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>{p.title}</h3>
                  <p style={{ fontSize: "0.9rem", color: "var(--muted)", lineHeight: 1.6, marginBottom: "0.5rem" }}>{p.body}</p>
                  <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--muted)" }}>
                    <span>Input: <strong style={{ color: "var(--accent-lime)" }}>{p.input}</strong></span>
                    <span>→</span>
                    <span>Output: <strong style={{ color: "var(--accent-lime)" }}>{p.output}</strong></span>
                  </div>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </SectionBlock>
      <SectionBlock eyebrow="FAQ" title="Common questions">
        <Accordion items={howItWorks.faq} />
      </SectionBlock>
    </PageFrame>
  );
}
