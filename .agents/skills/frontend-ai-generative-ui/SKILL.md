---
name: frontend-ai-generative-ui
description: "Use when changing Vercel AI SDK chat UIs (ai, @ai-sdk/react): useChat, SSE streaming, tool and data parts, citations, generative UI where the LLM picks components. Not the session shell -> frontend-agent-chat-shell."
license: Apache-2.0
metadata:
  version: "2.0.0"
---

# AI and Generative UI

Everything inside the message bubble: how model output streams in, how tool results and structured parts
render, and what the reader can do with a finished answer. The session shell around it belongs to
`frontend-agent-chat-shell`.

Written against `ai` 7.0 and `@ai-sdk/react` 4.0 (npm latest 7.0.169 and 4.0.173 on 2026-11-11), with the
AI SDK docs read on that date. The v5, v6 and v7 breaking changes that still appear in code are the dated traps.

## Procedure

1. Resolve API facts locally: lockfile version (package.json is only the constraint), installed types and
   source (`node_modules/ai`, `@ai-sdk/react`, the provider package), repo call sites. Open a Sources URL
   only if a contract stays uncertain and network exists; check the installed major against the
   written-against line. On v5 or v6, run the official codemods before hand-editing.
2. Fix the transport and the stream contract (Decisions: Transport) before any component.
3. Model the message as `UIMessage` parts and write one renderer that is exhaustive over part types and states.
4. Add the message states that are not text: interrupted, low confidence, step status, citations.
5. Prove it with the checks in Verify.

## Decisions

**Server proxy.** Every model call goes through your server; a provider key never reaches a client bundle.
Uploads (images, PDFs, audio) are proxied through your server too; size and type limits are provider
facts that change, so take them from `openai-docs`, `gemini-api-dev` or `claude-api`, not from this skill.
OpenAI is called through the Responses API, never Chat Completions; Gemini through the `google-genai` SDK.
Never hardcode a model id in UI code or in a rule here.

**Transport.** Default: `useChat` with `DefaultChatTransport`. A Python backend emits the AI SDK UI message
stream protocol over SSE (`sse-starlette`): the `x-vercel-ai-ui-message-stream: v1` header, typed chunks,
`data: [DONE]` at the end. Raw `fetch` plus `ReadableStream` only when the backend cannot speak that
protocol; LangChain.js only where the project already uses it. A WebSocket transport exists; choose it only
when the client streams upward too (`realtime-websockets`).

**One truth: `UIMessage` parts.** The client holds `UIMessage` (typed `parts`); the model sees `ModelMessage`,
converted on the server with `await convertToModelMessages`. Persist `UIMessage`, give assistant messages
stable server ids, pass `originalMessages` to the stream helper so a continued turn updates one message
instead of adding a duplicate, and validate stored messages with `validateUIMessages` on load.

**One renderer, exhaustive.** Switch on `part.type` (`text`, `reasoning`, `source-url`, `source-document`,
`tool-<name>`, `dynamic-tool`, `data-<name>`) and on every `part.state` of a tool part, including the
approval states, even for tools that do not use approval. A tool name maps to one component through a
registry; components get their data from the part only. An unknown tool renders as a compact row (status
icon, tool label, collapsed); JSON appears only inside an expanded Details. An unknown part type renders
nothing and does not crash.

**Approval.** Where a tool needs approval, render Approve and Deny on `approval-requested` (skip them when
`part.approval.isAutomatic`) and call `addToolApprovalResponse` only for manual approvals; render
`output-denied` with its reason. Approval is a decision commit: `frontend-decision-support-surfaces`.

**Structured output and custom parts.** Structured object streaming is `streamText` with `Output.object`,
read through `partialOutputStream` on the server or `useObject` on the client. Push your own payloads as
`data-<name>` parts with an `id` (a repeated id updates the same part); mark ephemeral ones `transient` so
they stay out of history. Generative UI means the model picks a registered component through a typed tool;
the RSC route (`@ai-sdk/rsc`) is experimental and not for new apps.

**Message states are text, not decoration.** Besides streaming and complete, a message can be:
interrupted (visible marker plus Retry; wiring lives in `frontend-agent-chat-shell`), low confidence or
not found (its own labelled state, never styled as an error and never as a confident answer), and failed.
While working, show the specific step ("Reading Aditivo_01.pdf") instead of typing dots. Retry, Edit and
Copy sit next to a finished answer.

**Citations.** Numbered markers `[n]` in the text; a click highlights the cited item in the source panel
(its placement and mobile sheet: `frontend-agent-chat-shell`). Forward sources with `sendSources` and read
`source-url` and `source-document` parts. Page and quoted excerpt are not fields of those parts: carry
them in a custom `data-citation` part `{ sourceId, page, excerpt }`. After a scoped edit of cited text, mark
the citation stale (`frontend-canvas-doc-editor`).

**Rendering under load.** Only the streaming message re-renders per token; memoize the rest. Use a markdown
parser that tolerates unclosed fences and emphasis. Follow the stream only while the reader is at the
bottom; otherwise show jump-to-latest. Virtualize on a measured problem, not at an invented message count.

**Stop.** `stop()` closes the HTTP connection; it does not prove the model stopped. With stream resume the
server keeps generating, so a real stop needs the endpoint in `frontend-agent-chat-shell`. Esc follows the
shell rule: it closes whatever is open, and with nothing open it stops generation; it never clears the draft.

**Announcements.** One polite status region says Generating, Response complete or Interrupted. The
streaming message itself is not a live region. Everything else (focus, keyboard, motion, contrast):
`accessibility`.

**Errors.** Show a generic message; the server decides what reaches the client through the stream helper's
error option (the default masks it). Keep the user's input on failure. Rate-limit and outage copy:
`frontend-design`; retry and backoff policy: `error-handling`.

Read `references/AI_UI_PATTERNS.md` before wiring the `useChat` component, the route handler or the
citation part: it holds the current-major snippets and the error table.

## Verify

- The key is absent from the client bundle and the network panel; uploads go to your own endpoint.
- Reloading mid-conversation shows no duplicated assistant message.
- A tool in each state, including `approval-requested`, `output-denied` and an unknown tool name, renders
  without raw JSON in the thread and without a crash.
- A cut stream shows an interrupted marker with Retry, not a short answer that reads as complete.
- A citation click highlights the matching source; a low-confidence answer is labelled in text.
- A screen reader hears the status changes once and does not read every token.

## Dated traps

- `[ai@7.0, 2026-11-11]` Type errors or deprecation warnings on `system` and `onFinish` -> renamed `instructions` and `onEnd` (old names are deprecated aliases; `onEnd` usage covers all steps) -> rename; system messages inside `messages` are rejected unless `allowSystemInMessages` is set, so audit persisted histories.
- `[ai@7.0, 2026-11-11]` `stepCountIs` no longer found -> renamed `isStepCount`; `maxSteps` was already removed in 5.0 -> `stopWhen: isStepCount(n)`.
- `[ai@7.0, 2026-11-11]` `result.toUIMessageStreamResponse()` warns -> deprecated, removed in the next major -> `createUIMessageStreamResponse({ stream: toUIMessageStream({ stream: result.stream, originalMessages }) })`; `fullStream` is now `stream`.
- `[ai@7.0, 2026-11-11]` `require('ai')` fails -> ESM-only and Node 22 or later; telemetry moved to `@ai-sdk/otel`.
- `[ai@6.0, 2026-11-11]` The model receives a Promise or the build fails -> `convertToModelMessages` is async -> `await` it (codemod `add-await-converttomodelmessages`, run with `npx @ai-sdk/codemod v6`).
- `[ai@6.0, 2026-11-11]` `streamObject` and `generateObject` warn -> deprecated -> `streamText` or `generateText` with `output: Output.object({ schema })`.
- `[ai@5.0, 2026-11-11]` `import from 'ai/rsc'` fails -> the package is `@ai-sdk/rsc`, and the docs call it experimental.
- `[ai@7.0 docs, 2026-11-11]` Tool `needsApproval` is marked deprecated in the latest tool-usage page -> approval is configured with `toolApproval` on `streamText`; read the installed types before using either.
- `[ai-elements, 2026-11-11]` Its home page says it is moving to shadcn/ui and will be deprecated at the end of November 2026 -> check that page before adding it to a project.
- `[@ai-sdk/react@4.0, 2026-11-11]` A part renderer breaks on new content -> 7.0 adds `reasoning-file` parts and deprecates `{ type: 'image' }` message parts -> keep the renderer exhaustive with a safe default.

## Sources

| Topic | Official entry URL | Read when | Content checked |
|---|---|---|---|
| Migration to 7.0 | https://ai-sdk.dev/docs/migration-guides/migration-guide-7-0 | upgrading, or reading old v5/v6 code | 2026-11-11 |
| Migration to 6.0 | https://ai-sdk.dev/docs/migration-guides/migration-guide-6-0 | `convertToModelMessages`, `Output.object`, codemods | 2026-11-11 |
| Migration to 5.0 | https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0 | `UIMessage`, tool part names, `@ai-sdk/rsc` | 2026-11-11 |
| useChat, status, sources, metadata | https://ai-sdk.dev/docs/ai-sdk-ui/chatbot | wiring the hook or citations | 2026-11-11 |
| Tool parts and approval | https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-tool-usage | rendering tool states | 2026-11-11 |
| UI message stream protocol | https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol | a non-JS backend emits the stream | 2026-11-11 |
| Custom data parts | https://ai-sdk.dev/docs/ai-sdk-ui/streaming-data | pushing `data-*` parts | 2026-11-11 |
| Transports | https://ai-sdk.dev/docs/ai-sdk-ui/transport | choosing or customising the transport | 2026-11-11 |
| Message persistence and ids | https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence | storing and reloading chats | 2026-11-11 |
| Repeated assistant messages | https://ai-sdk.dev/docs/troubleshooting/repeated-assistant-messages | a turn shows twice | 2026-11-11 |
| Object streaming, `useObject` | https://ai-sdk.dev/docs/ai-sdk-ui/object-generation | streaming a structured object | 2026-11-11 |
| AI SDK RSC (experimental) | https://ai-sdk.dev/docs/ai-sdk-rsc/overview | the project already uses `streamUI` | 2026-11-11 |
| AI Elements | https://elements.ai-sdk.dev/ | adopting prebuilt chat components | 2026-11-11 |

## Works with

| Skill | Owns | Load when |
|---|---|---|
| `frontend-design` | Visual standard, error and empty-state wording | a message state or screen is designed |
| `accessibility` | Accessible interaction, live regions, focus, motion | the thread must work with a keyboard and a screen reader |
| `frontend-delivery-checklist` | The done gate | the chat is about to be called done |
| `testing-e2e-playwright` | Browser tests | a streaming journey needs a test |
| `pwa-engineering` | Install, offline, storage | the chat must work offline or queue sends |
