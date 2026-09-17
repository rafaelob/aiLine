---
name: frontend-ai-generative-ui
description: >-
  Stream model output, render tool results, or let the LLM pick UI from prompts.
  Covers provider adapters, SSE/Fetch, stop/regenerate, and typed tool calls.
  Use for message-level generative UI ("UI generativa", "chat com streaming").
  Session shell uses frontend-agent-chat-shell.
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.1.4
  category: content-production
  subcategory: technical-writing
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - content-production
  - frontend
  - ai
  - generative
  - ui
  - project_level
  - user_level:intermediate
  audience: developer
  output_format: markdown
  modality: text
---

# AI and Generative UI

Design and implementation playbook for building frontend interfaces that consume LLM output in real time, render streaming content, display tool call results, and dynamically generate UI components from AI responses. Covers multiple approaches: Vercel AI SDK, LangChain.js, raw SSE/Fetch streaming, and framework-agnostic patterns. Includes chat interfaces, streaming patterns, generative UI, and accessibility for AI-driven UIs.

## Scope

- Building chat interfaces that stream LLM responses in real time
- Implementing tool call rendering (function results, artifacts, code blocks)
- Using Vercel AI SDK (useChat, useCompletion, streamUI) for React/Next.js
- Designing generative UI where the LLM selects which components to render
- Building prompt-to-UI workflows (v0/Bolt-style iterative refinement)
- Handling optimistic rendering, skeleton states, and progressive content reveal
- Ensuring AI UIs are accessible (screen readers, keyboard navigation, focus management)

## Inputs to Collect

1. **LLM provider** -- OpenAI, Anthropic, Google, local model, or multi-provider?
2. **Streaming mode** -- text streaming, tool call streaming, or component streaming (streamUI)?
3. **UI framework** -- React/Next.js, Vue/Nuxt, Svelte, or other?
4. **Chat features** -- message threading, branching, editing, regeneration, artifact display?
5. **Tool calls** -- which tools does the LLM invoke, and how should results render?
6. **Auth model** -- per-user API keys, server-side proxy, or shared quota?
7. **Accessibility requirements** -- WCAG level, screen reader testing scope?

## Execution Playbook

### Step 1: Architecture for AI UI

Design the data flow between client, server, and LLM:

```
User Input -> Server Route/Action -> LLM API (streaming) -> Client (progressive render)
                                  -> Tool Calls -> Tool Execution -> Result Render
```

Key decisions:
- **Server-side streaming**: always proxy LLM calls through your server (never expose API keys to client)
- **Protocol**: use Server-Sent Events (SSE) or the AI SDK's streaming protocol for delivering chunks
- **State management**: messages array with streaming append, tool call state tracking, error/retry state

### Step 2: Streaming Approaches (Framework-Agnostic First)

Before choosing an SDK, understand the fundamental streaming patterns:

- **Raw SSE/Fetch streaming**: use the Fetch API with `ReadableStream` to consume Server-Sent Events from any LLM provider. Framework-agnostic; works with any backend. This is the lowest-level approach and gives full control.
- **LangChain.js**: provides streaming abstractions (`streamEvents`, `streamLog`) that work with multiple LLM providers. Good for complex chains and agent workflows. Can be used with any frontend framework.
- **Vercel AI SDK**: provides React/Vue/Svelte hooks and server utilities for streaming. Most integrated experience for Next.js/React projects.

**Decision framework**: Use raw SSE/Fetch for maximum control and no dependencies. Use LangChain.js when you need agent orchestration and multi-provider support. Use Vercel AI SDK when you want the fastest path to a polished React/Next.js chat UI.

### Step 2b: Vercel AI SDK Integration (Option)

The AI SDK provides framework-level primitives for streaming AI responses. AI SDK 7 is the current stable major (released 2026-06-25); AI SDK 6 is the prior stable line. AI SDK 5 remains a maintained older line. All use the transport-based architecture introduced in v5. Key v7 breaking changes: Node.js 22+ required; ESM-only (no CommonJS `require()`); `system` option renamed to `instructions`; `onFinish` renamed to `onEnd`; OpenTelemetry moved to `@ai-sdk/otel`. Use codemods for migration.

**Client hooks** (`@ai-sdk/react`):
- `useChat` -- transport-based chat with message history, streaming, and tool call support. In v5: no longer owns input state; `sendMessage({ role, parts: [...] })` replaces the old `input`/`handleSubmit` couple; messages are `UIMessage` objects with a typed `parts` array (text / reasoning / tool-call / file / data parts).
- `useCompletion` -- single-prompt completion with streaming
- `useObject` -- stream structured JSON objects from LLM (schema-validated)

**Server-side** (`ai`):
- `streamText` -- stream text responses from any supported provider
- `streamObject` -- stream structured data with Zod/Valibot/Effect schema validation
- `generateText` / `generateObject` -- non-streaming equivalents
- `tool({ description, inputSchema, execute })` -- define typed tools; inputs/outputs are type-safe end-to-end
- `createUIMessageStream` / `createUIMessageStreamResponse` -- custom UIMessage parts (replaces the removed `writeMessageAnnotation`/`writeData` from v4)
- `DefaultChatTransport` -- swap the fetch transport for WebSockets, SSE, or direct provider connections

**Key v5/v6 changes to be aware of**:
- `UIMessage` vs `ModelMessage`: UIMessage is the UI state source of truth (includes rendering/status metadata); ModelMessage is optimized for provider calls. Convert via `convertToModelMessages(messages)` on the server.
- `maxSteps` -- cap multi-step tool call chains.
- Tool approval flow (shipped in v6 stable): gate execute with `addToolApprovalResponse`; per-tool strict mode.
- **AI Elements**: the official prebuilt composable UI building blocks (replaces the older ChatSDK examples). Install via `npx ai-elements`.
- Provider packages: `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/google`, `@ai-sdk/azure`, etc. -- use the provider-specific package instead of the deprecated monolithic imports.
- SSE is the default streaming protocol (the old `streamProtocol: 'text' | 'data'` options are unified under transport implementations).

**Alternatives**: LangChain.js (for agent orchestration), Mastra (agent framework), or raw `fetch` + `ReadableStream` for full control. Provider SDK streaming endpoints all emit SSE and are usable directly from any framework: OpenAI's Responses API (`stream: true`) is preferred over legacy Chat Completions streaming for new apps; Anthropic's Messages API emits typed SSE events (`message_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`, with tool use streaming `input_json_delta`); Gemini uses the `google-genai` SDK (`generate_content_stream`/`generateContentStream`) -- never the deprecated `google-generative-ai`.

AI SDKs evolve rapidly; always check the installed version (`package.json`) before applying hook signatures and server utilities.

**React 19 server-action patterns**: `useActionState` + `useFormStatus` + `useOptimistic` pair naturally with streaming server actions; combine with AI Elements or your own component registry for a fully server-first chat UI.

Read `references/AI_UI_PATTERNS.md` when wiring the client `useChat` hook or the server-side route handler: it has the working `useChat` component (transport, tool-call handling, stop/regenerate), the `streamText` route handler with typed tools, and the legacy `streamUI` (RSC) pattern.

### Step 2c: Multimodal Input Handling (File/Image Upload)

When users upload images, PDFs, or audio to the AI, **never relay raw files through client code** (API key exposure). Always proxy through your server:

1. Client uploads file to your server endpoint (multipart/form-data).
2. Server validates MIME type and file size against provider limits.
3. Server converts to base64 or uploads to the provider Files API, then passes to the LLM.

**Provider limits and paths (verified 2026-06-29):**

| Provider | Max per image | Max total payload | Notes |
|---|---|---|---|
| OpenAI Chat Completions | 8 MB | 512 MB | Images >8 MB are **silently dropped** (no error) — use Responses API or file_id for larger |
| OpenAI Responses API | 50 MB via file_id | 512 MB | Upload via Files API (purpose=`'vision'`), pass `input_image.file_id` |
| Anthropic | 5 MB per image | 32 MB total request | Pass as base64 `image` source or `document` for PDFs |
| Gemini | 20 MB recommended inline | 100 MB payload | Larger files: use File API (`client.files.upload`) → pass `fileData.fileUri` |

**Accepted source forms (OpenAI):** `input_image.image_url` (HTTPS URL), `input_image.image_url` (base64 data URL), `input_image.file_id` (Files API). For large or repeated images, upload once to Files API and reuse `file_id`.

### Step 3: Streaming Rendering

Render LLM output progressively as tokens arrive:

- **Text streaming**: append tokens to a growing string; use CSS `white-space: pre-wrap` for formatting
- **Markdown streaming**: use a streaming-aware markdown renderer (e.g., react-markdown with streaming input); handle partial markdown gracefully (unclosed bold, incomplete code blocks)
- **Code block streaming**: detect code fence opening, render with syntax highlighting, update as tokens arrive
- **Tool call streaming**: show a loading indicator when a tool call starts; render the result when complete; handle partial argument streaming for long tool calls
- **Skeleton states**: show typing indicators or skeleton placeholders before first token arrives; transition smoothly to real content

### Step 4: Generative UI (Component Streaming)

In generative UI, the LLM decides which UI components to render. Two modern approaches:

1. **AI SDK 5+ UIMessage parts**: define tools with typed `inputSchema`/`outputSchema`; on the client, switch on `part.type` (`tool-<name>`) inside `message.parts.map(...)` and render the matching component. This is the current recommended pattern and works with React Server Components.
2. **Custom data parts**: use `createUIMessageStream` + `writer.write({ type: 'data-<name>', id, data })` to push arbitrary structured payloads the UI can render progressively.
3. **Legacy `streamUI` / React Server Components streaming** (AI SDK RSC): still available under `ai/rsc` for server-rendered React components streamed to the client, but the message-parts approach is preferred for new apps.

Design considerations:
- Each tool name maps to one component; keep a registry.
- Components handle their own loading/error/partial states (`part.state` can be `input-streaming`, `input-available`, `output-available`, `output-error`).
- Keep components stateless where possible (data comes from tool input/output).
- Implement a fallback renderer for unknown part types.

**Code Interpreter artifact pipeline:** When the LLM uses Code Interpreter (OpenAI containers), binary artifacts (charts, processed images, CSVs, PDFs) are stored ephemerally in the container — **idle containers expire after 20 minutes**. The server must:
1. Detect Code Interpreter tool call completion.
2. Download each output file: `GET /v1/containers/{container_id}/files/{file_id}/content` before the container expires.
3. Store the file (blob storage, DB, or disk) and generate a stable URL.
4. Return the URL in the tool result so the frontend can render it.

The frontend renders the artifact via the secure URL/blob — never rely on direct container file access from the browser. Handle binary output types: charts as PNG, DataFrames as CSV, reports as PDF.

**Design considerations**:
- Define a component registry mapping tool names to React components
- Each component handles its own loading/error states
- Keep components stateless where possible (data comes from tool call args/results)
- Implement fallback rendering for unknown tool types

### Step 5: Chat Interface UX Patterns

- **Message list**: virtualized list for long conversations; auto-scroll to bottom on new messages; scroll-to-bottom button when user scrolls up
- **Composer chrome** is not this skill's: the input area contract (autosize, Enter vs Shift+Enter, IME safety, drafts, attachments, model/effort chip, dictation vs voice session, send-morphs-to-stop) belongs to `frontend-agent-chat-shell`, along with the sidebar, sessions and stream resume. This skill stops at the message bubble.
- **Message actions**: copy, regenerate, edit-and-resubmit, branch conversation
- **Artifact display**: render code, charts, tables, images inline or in side panels; support copy/download
- **Error handling**: show retry button on API failures; preserve user input on error; show rate limit feedback
- **Multi-turn context**: display system message / context indicators; show token count / context window usage if relevant

### Step 6: Accessibility for AI UIs

AI interfaces have unique accessibility challenges:

- **Live regions**: use `aria-live="polite"` on the streaming message area so screen readers announce new content without interrupting
- **Status announcements**: announce "generating response", "response complete", "error occurred" via visually-hidden live region
- **Focus management**: keep focus on the input after sending; do not move focus to the streaming response unless user navigates there
- **Keyboard navigation**: Tab through messages, Enter to interact with artifacts, Escape to stop generation
- **Reduced motion**: respect `prefers-reduced-motion` for typing indicators and streaming animations
- **Semantic markup**: use `role="log"` for message lists, `role="status"` for generation indicators; mark user vs assistant messages with clear labels

## Deliverables / Definition of Done

- [ ] LLM streaming integrated via server-side proxy (no client-side API key exposure)
- [ ] Chat UI renders streaming text progressively with proper markdown handling
- [ ] Tool calls display loading state and render results in appropriate components
- [ ] Generative UI components render from LLM tool calls (if applicable)
- [ ] Error handling covers API failures, rate limits, and network issues
- [ ] Keyboard navigation works for all chat interactions
- [ ] Screen reader announces streaming status and new messages
- [ ] Stop generation button works during streaming
- [ ] Performance: first token renders <100ms after receipt; no jank during streaming

## Common Pitfalls / Gotchas

1. **Exposing API keys client-side** -- always proxy through your server; never embed provider keys in client bundles.
2. **Re-rendering entire message list on each token** -- use memoization; only re-render the streaming message.
3. **Breaking markdown mid-stream** -- partial markdown (unclosed `**`, incomplete ` ``` `) causes rendering glitches; use a parser that handles incomplete input.
4. **No abort/stop mechanism** -- always implement AbortController; users must be able to stop generation.
5. **Ignoring screen readers** -- streaming text without aria-live means blind users get no feedback during generation.
6. **Blocking UI on tool calls** -- tool calls can be slow; show intermediate state and keep the UI responsive.
7. **Hardcoding provider assumptions** -- use provider abstraction (AI SDK, LangChain.js, or your own) so you can swap providers without UI changes.
8. **Locking to one SDK** -- the streaming UI patterns (progressive rendering, tool call lifecycle, error handling) are universal; choose your SDK based on project needs, not habit.

## Example Prompts

- "Build a streaming chat interface using Vercel AI SDK with Next.js App Router."
- "Implement generative UI where the LLM can render weather cards, stock charts, and code editors."
- "Add tool call rendering to my existing chat: show loading spinners and display results inline."
- "Make my AI chat accessible: add aria-live regions, keyboard nav, and screen reader announcements."
- "Design a prompt-to-UI workflow where users iteratively refine generated components."

## Invocation

```
Use the frontend-ai-generative-ui skill to [describe your AI UI need].
```

## Sources

https://ai-sdk.dev/docs | https://ai-sdk.dev/elements | https://react.dev | https://platform.openai.com/docs/api-reference/responses | https://docs.anthropic.com/en/api/messages-streaming | https://ai.google.dev/gemini-api/docs | https://js.langchain.com/docs
