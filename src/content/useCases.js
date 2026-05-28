export const useCases = {
  hero: {
    eyebrow: "Where It Fits",
    title: "Use Cases",
    intro: "Real workflows that benefit from prompt compilation — with measurable token savings.",
  },
  cases: [
    { title: "Coding-agent logs", body: "Reduce long terminal output, file snippets, and tool traces before handing context to a planning or debugging model.", outcome: "Lower token load with inspectable diffs.", savings: "40-60%" },
    { title: "RAG answer assembly", body: "Score retrieved chunks, prune weak matches, and keep protected facts before composing a final model request.", outcome: "Cleaner context windows for retrieval flows.", savings: "30-50%" },
    { title: "Support and RMA context", body: "Preserve case numbers, order IDs, product names, and customer constraints while removing repeated conversation text.", outcome: "Safer compression for operational prompts.", savings: "25-45%" },
    { title: "Prompt generation", body: "Generate a detailed website or app prompt, then compile and inspect it before sending the final version downstream.", outcome: "Faster prompt drafting with measurable savings.", savings: "20-35%" },
    { title: "Model routing prep", body: "Attach token counts, savings, cache hints, and route metadata so agents can choose the right model tier.", outcome: "More predictable cost and latency decisions.", savings: "varies" },
  ],
};
