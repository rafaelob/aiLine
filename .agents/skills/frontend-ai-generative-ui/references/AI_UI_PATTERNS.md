<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-06-04 (AI SDK 5+/6) -->

# AI UI Patterns Guide

## Vercel AI SDK Architecture

Three layers: **Core** (`ai`) -- provider-agnostic functions (`streamText`, `streamObject`, `generateText`, `convertToModelMessages`); **UI** (`@ai-sdk/react`) -- hooks (`useChat`, `useCompletion`, `useObject`); **RSC** (`ai/rsc`) -- Server Components (`streamUI`, `createStreamableUI`), legacy but still available.

Docs: https://ai-sdk.dev/docs (AI SDK 6 stable; v7 in public beta)

## useChat Pattern (React)

```tsx
// AI SDK 5+/6 -- verify current API at ai-sdk.dev/docs
'use client';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';

function ChatUI() {
  const [input, setInput] = useState('');
  // useChat no longer owns input state; manage it locally.
  const { messages, sendMessage, status, stop, regenerate, error } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
    onToolCall: async ({ toolCall }) => { /* client-side tool execution */ },
  });
  const isStreaming = status === 'streaming' || status === 'submitted';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage({ text: input });
    setInput('');
  };

  return (
    <div role="log" aria-label="Chat messages">
      {messages.map(m => <MessageBubble key={m.id} message={m} />)}
      {isStreaming && <TypingIndicator />}
      <form onSubmit={handleSubmit}>
        <ChatInput value={input} onChange={e => setInput(e.target.value)}
          isLoading={isStreaming} onStop={stop} />
      </form>
    </div>
  );
}
```

## Server-Side Streaming (Route Handler)

```ts
// AI SDK 5+/6 -- verify current API at ai-sdk.dev/docs
import { streamText, convertToModelMessages, tool, stepCountIs, type UIMessage } from 'ai';
import { z } from 'zod';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: yourProvider('model-name'),
    messages: convertToModelMessages(messages),
    tools: {
      getWeather: tool({
        description: 'Get weather for a location',
        inputSchema: z.object({ location: z.string() }),
        execute: async ({ location }) => ({ temperature: 72, condition: 'sunny' }),
      }),
    },
    stopWhen: stepCountIs(5),
  });
  return result.toUIMessageStreamResponse();
}
```

## Generative UI (recommended: UIMessage parts)

In AI SDK 5+/6 the preferred pattern renders components by switching on `part.type`
(`tool-<name>`) inside `message.parts.map(...)`. The server defines tools with typed
`inputSchema`/`outputSchema` (see the route handler above); the client maps each tool
part to a component.

```tsx
// AI SDK 5+/6 client -- verify current API at ai-sdk.dev/docs
function MessageBubble({ message }: { message: UIMessage }) {
  return (
    <div role="article">
      {message.parts.map((part, i) => {
        switch (part.type) {
          case 'text':
            return <MarkdownRenderer key={i} content={part.text} />;
          case 'tool-showWeather':
            // part.state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error'
            return part.state === 'output-available'
              ? <WeatherCard key={i} data={part.output} />
              : <WeatherSkeleton key={i} />;
          default:
            return null; // fallback for unknown part types
        }
      })}
    </div>
  );
}
```

### Legacy: streamUI (AI SDK RSC)

Still available under `ai/rsc` for server-streamed React components, but the
message-parts approach above is preferred for new apps.

```tsx
// Legacy AI SDK RSC -- verify streamUI API at ai-sdk.dev/docs
import { streamUI } from 'ai/rsc';

async function submitMessage(input: string) {
  'use server';
  const result = await streamUI({
    model: yourProvider('model-name'),
    messages: [{ role: 'user', content: input }],
    text: ({ content, done }) => <MarkdownRenderer content={content} isStreaming={!done} />,
    tools: {
      showWeather: {
        description: 'Display weather for a location',
        inputSchema: z.object({ location: z.string() }),
        generate: async function* ({ location }) {
          yield <WeatherSkeleton />;
          return <WeatherCard data={await fetchWeather(location)} />;
        },
      },
    },
  });
  return result.value;
}
```

## Streaming Markdown

Challenges: incomplete formatting (`**bold` unclosed), partial code blocks, broken links. Strategies: buffer until formatting boundary completes, use a tolerant parser (remark with recovery), or post-process to close open tags for display only.

## Chat Accessibility

```html
<div role="log" aria-live="polite" aria-label="Conversation"><!-- messages --></div>
<div aria-live="assertive" class="sr-only" role="status"><!-- status announcements --></div>
```

| Key | Action |
|-----|--------|
| Enter | Send | Shift+Enter | New line | Escape | Stop/close |
| Ctrl+Shift+C | Copy last response | Up Arrow (empty) | Edit last message |

Screen readers: announce role before content, tool call status, message count, arrow-key navigation.

## Tool Call Rendering

Lifecycle: LLM decides to call -> show indicator -> args streaming -> spinner/skeleton -> result component -> resume text. Map tools to components: weather -> `<WeatherCard />`, code -> `<CodeBlock />`, search -> `<SearchResults />`, unknown -> `<GenericToolResult />` with JSON.

## Error Handling

| Error | UX |
|-------|-----|
| Network failure | Retry button, preserve input, show last state |
| Rate limit (429) | Cooldown timer, queue request |
| Context too long | Suggest new conversation or summarize |
| Tool failure | Inline error, allow LLM retry |
| Stream interrupted | Partial response + "interrupted" indicator |
| Provider outage | Fallback provider if configured |

## Performance

- **Virtualize** message list for > 100 messages
- **Memoize** messages -- only streaming message re-renders per token
- **Debounce** markdown parsing (every N tokens or on idle)
- **Lazy-load** artifacts (charts, code editors, images) within bubbles
- **Backpressure**: buffer tokens, flush on `requestAnimationFrame`
