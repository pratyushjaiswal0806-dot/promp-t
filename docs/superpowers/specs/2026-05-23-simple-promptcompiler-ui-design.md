# Simple PromptCompiler UI Design

## Goal

Replace the multi-panel workbench with a direct prompt compiler flow: paste a prompt, compile and optimize it, review the optimized prompt, then inspect analytics.

## Product Flow

The first screen shows one large prompt input and one primary action, `Compile & Optimize`. The app does not preload a sample into the input. A user pastes their prompt, clicks the action, and receives the optimized prompt directly below the input.

The optimized prompt area appears before analytics and includes `Copy` and `Export Text` actions. Analytics are shown after the optimized prompt so the main task stays first. The analytics include token counts, savings, segment breakdown, protected values found by the compiler, and a concise list of changes.

## Interface Scope

The main page removes the visible workflow strip, model search, model selector, sample loading, import, manual protected-value controls, selected-text pinning, NIM summarization, diff filters, segment table, history, and JSON export. The app can still use the default model returned by the server internally.

## Data Flow

On boot, the app fetches `/api/health` and `/api/models` only to determine status and the default model. It does not fetch or load samples into the input. Clicking `Compile & Optimize` sends `{ input, model }` to `/api/compile`. The response drives the optimized output and analytics.

## Error Handling

Empty prompts and server failures are shown in the existing error box. Copy failures keep the optimized text visible and show a manual-copy message. Export is disabled unless a compile result exists.

## Testing

Update the browser E2E test to assert the simplified surface, compile a real prompt, confirm optimized output appears before analytics, and keep the mobile overflow check. Run the focused E2E test and then the full unittest suite.
