<!-- written-against: ai@7.0, @ai-sdk/react@4.0 (2026-11-11). Verify against the installed version and the pages in SKILL.md Sources. -->

# AI UI patterns: snippets that encode house decisions

Only what the official docs do not decide for you. Hook options, chunk types and part fields: read the
installed types, then the Sources pages in `SKILL.md`.

## 1. The `useChat` component

Default transport, input state owned by the component, a status region separate from the streaming
message, and a stop control that is only offered while a response is in flight.

```tsx
'use client';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';

export function ChatUI() {
  const [input, setInput] = useState('');
  const { messages, sendMessage, status, stop, regenerate, error, addToolApprovalResponse } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  });
  const busy = status === 'submitted' || status === 'streaming';
  const statusText =
    status === 'streaming' ? 'Generating' : error ? 'Interrupted' : status === 'ready' && messages.length ? 'Response complete' : '';

  return (
    <section aria-label="Conversation">
      <div role="status" className="sr-only">{statusText}</div>
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} onApproval={addToolApprovalResponse} />
      ))}
      {error && <InterruptedNotice onRetry={() => regenerate()} />}
      <form onSubmit={(e) => { e.preventDefault(); sendMessage({ text: input }); setInput(''); }}>
        <Composer value={input} onChange={setInput} busy={busy} onStop={stop} />
      </form>
    </section>
  );
}
```

The `role="status"` region is the only live region; the message list is not one (`accessibility`).
`Composer`, the Esc rule and the real stop endpoint belong to `frontend-agent-chat-shell`.

## 2. Route handler (AI SDK 7)

```ts
import { streamText, convertToModelMessages, createUIMessageStreamResponse, toUIMessageStream,
         isStepCount, type UIMessage } from 'ai';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: getModel(),                                 // resolved from config; never a literal id here
    instructions: SYSTEM_PROMPT,
    messages: await convertToModelMessages(messages),
    tools,                                             // typed tools, see the tool-usage page
    stopWhen: isStepCount(5),
  });
  return createUIMessageStreamResponse({
    stream: toUIMessageStream({ stream: result.stream, originalMessages: messages, sendSources: true }),
  });
}
```

Why `originalMessages`: without it every turn gets a new message id and the client shows a duplicate
assistant message. Whether `sendSources` is an option of `toUIMessageStream` in the installed 7.x is
UNVERIFIED (the chatbot page names it for the helper; the 7.0 migration page does not list it): check the
installed types. On a Python backend the same contract is the UI message stream protocol (Sources: stream
protocol), emitted by `sse-starlette`.

## 3. Part renderer

```tsx
function MessageBubble({ message, onApproval }: { message: UIMessage; onApproval: Approve }) {
  return (
    <div>
      {message.parts.map((part, i) => {
        switch (part.type) {
          case 'text':
            return <Markdown key={i} text={part.text} />;              // tolerant of unclosed fences
          case 'data-citation':
            return <CitationMarker key={i} {...part.data} />;           // { sourceId, page, excerpt }
          case 'tool-showWeather':
            return <ToolPart key={i} part={part} onApproval={onApproval} render={WeatherCard} />;
          default:
            return part.type.startsWith('tool-') || part.type === 'dynamic-tool'
              ? <ToolRow key={i} part={part} />                         // compact row, collapsed Details
              : null;                                                   // unknown part: render nothing
        }
      })}
    </div>
  );
}
```

`ToolPart` switches on every `part.state`: `input-streaming` and `input-available` show the step
status text, `output-available` renders the component, `output-error` renders an inline error,
`approval-requested` renders Approve/Deny (none when `part.approval.isAutomatic`), `approval-responded`
shows the decision, `output-denied` shows the reason.

## 4. Custom citation part (server side)

```ts
writer.write({
  type: 'data-citation',
  id: `cit-${n}`,                                       // same id updates the same part
  data: { sourceId, page, excerpt },
});
```

`source-url` and `source-document` carry the source; page and excerpt do not exist on them, hence the
custom part. A citation click sets the active source id; the panel scrolls to and highlights that item.

## 5. Failure table

| Failure | UX |
|---|---|
| Network failure | Retry, keep the input, keep the last state |
| Rate limit (429) | Cooldown shown, send queued or disabled with the reason |
| Context too long | Suggest a new conversation or a summary |
| Tool failure | Inline error in the tool row; the model may retry |
| Stream interrupted | Partial answer plus an "interrupted" marker and Retry |
| Provider outage | Say which; fall back only if configured, and say so |

## 6. Cost of a token

- Memoize messages; only the streaming one re-renders per token.
- Parse markdown on a boundary or on idle, not per token; close open fences for display only.
- Lazy-load heavy artifact renderers (charts, editors) inside the bubble.
- Flush buffered tokens once per animation frame.
