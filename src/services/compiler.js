import { getJson, postJson } from "./api.js";

export async function getHealth() { return getJson("/api/health"); }

export async function getModels() { return getJson("/api/models"); }

export async function getSamples() { return getJson("/api/samples"); }

export async function analyze(input, model) {
  return postJson("/api/analyze", { input, model });
}

export async function compile(params) {
  return postJson("/v1/compile", params);
}

export async function lint(input) {
  return postJson("/v1/lint", { input });
}

export async function generatePrompt(idea, kind, model) {
  return postJson("/api/generate-prompt", { idea, kind, model });
}

export async function nimSummarize(text, model) {
  return postJson("/api/nim/summarize", { text, model });
}
