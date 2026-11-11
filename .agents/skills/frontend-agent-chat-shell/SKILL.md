---
name: frontend-agent-chat-shell
description: "Use when changing the AI chat shell (\"barra lateral\", \"retomar stream\"): sessions, search, empty state, composer, source and artifact panels, stream resume and stop. Not message bubbles -> frontend-ai-generative-ui."
license: Apache-2.0
metadata:
  version: "2.0.0"
---

# Agent Chat Shell

The thread is not the product. Around it sits a shell: how a session is started, found, named, resumed and
branched, and how long work stays visible while the user looks elsewhere. Everything inside a message bubble
belongs to `frontend-ai-generative-ui`; editing inside a generated document belongs to
`frontend-canvas-doc-editor`; conversation content and persona to `conversational-ai-ux`.

Written against `ai` 7.0, `@ai-sdk/react` 4.0 and `resumable-stream` 2.2 (npm latest on 2026-11-11), with the
docs of those packages and of `sse-starlette` read on that date. Product observations in `references/`
carry their own dates and evidence classes.

## Procedure

1. Resolve API facts locally: lockfile version (package.json is only the constraint), installed types and
   source (`node_modules/ai`, `@ai-sdk/react`, `resumable-stream`; site-packages for `sse-starlette`), repo
   call sites. Open a Sources URL only if a contract stays uncertain and network exists; check the installed
   major against the written-against line.
2. Draw the seam in writing: shell versus in-thread; route the in-thread half to `frontend-ai-generative-ui`.
3. Choose two or three org primitives, lay out the zones, then decide whether a third surface exists.
4. Build the composer first, then wire session state to the URL.
5. Implement resume and the stop endpoint together: resume without stop gives a stop button that lies.
6. Design the shell states (empty, loading history, offline, interrupted, no access) before styling.
7. Prove it with Verify.

## Decisions

**Zones and sidebar order.** A collapsible left sidebar, a main canvas, and a third surface only when
artifacts justify it. Order, top to bottom: new-chat, search over chats (never behind a menu), libraries,
org primitives, recents with live status, role-gated entries (admin) just above the account block, account
and plan. The collapse order (full, narrower, icon rail, off-canvas drawer) is declared once, never left to
CSS accident; breakpoints and tokens come from `frontend-design`. Org primitives (pinned, projects, agent
gallery, notebooks, media, scheduled) are a menu: two or three, on record, never six.

**Empty state.** A greeting, the composer, three or four suggested prompts as buttons that fill the
composer (the user still sends), and one sentence on what the assistant can and cannot do. No tour, no
feature grid, at most one onboarding banner. A returning user with no recents sees that the archive is
empty, not a skeleton.

**Recents are a task surface.** Each row carries server-derived status (`idle`, `running`, `needs_input`,
`failed`); `needs_input` sorts above `running`; a failure stays visible until acknowledged; never show
optimistic status; do not animate every row. Paginate by cursor, not offset.

**Composer.** The active model and effort are visible before send when more than one exists. Dictation (speech
into the draft) and a voice-session (a live duplex surface) are two controls with two destinations. Enter
sends, Shift+Enter breaks the line, and IME composition never sends. Drafts persist per session. Attachments
validate type and size before upload and share one state machine for picker, paste and drop. Send morphs into
stop in place. Esc closes whatever is open (popover, panel, menu); with nothing open and a response
streaming it stops the generation; it never clears the draft. A composer covered by the mobile keyboard:
`pwa-engineering` and `frontend-design`.

**Artifact placement is a choice with a cost.** Side panel (iterated over many turns, costs width and a
mobile fallback), inline plus fullscreen (read once, one layout everywhere), or a dedicated route (the work
is the session, a second shell). Write the cost down before building. Whichever you pick: the open artifact
is in the URL, focus moves in on open and returns to the invoker on close without a trap, the mobile
fallback is a designed sheet or route, and open state is per session.

**Source panel.** Citations in a message open a source panel that follows the same mechanics: a non-modal
region on wide screens, a modal sheet on narrow ones. A citation click opens it, scrolls to the cited
item and highlights it; closing returns focus to the citation. The citation markup itself is
`frontend-ai-generative-ui`.

**Sessions, search, branching.** Titles generate after the first exchange and stay overridable; rename, pin
and delete carry undo. Search matches content, not only titles, and "no match" differs from "search
unavailable". Editing an earlier turn forks: a fork is a new session with a parent, its own row, title,
lineage and URL, and the original is never destroyed. Do not build synchronous multi-human threads; async
sharing is the model.

**Resume and stop.** Resume is an application-level stream id plus a server buffer the client replays, not
bare `Last-Event-ID`. It covers reload, tab close, connection loss and navigating away; device switch is not
covered, so never promise it in copy. A client abort is a disconnect, not a stop: do not hand the request
abort signal to the model call when resume is on, and give Stop its own endpoint that persists the partial
response, cancels the producer and clears `activeStreamId` only if it still equals the stream id that stop
targets (compare-and-clear; the client sends the id). Call it on explicit user action only, then abort
locally, and do not auto-reconnect after a stop. On reopen, reconcile server `activeStreamId` against local
history and deduplicate by id. A cut stream
renders as interrupted with Retry, never as a short complete answer.

**Python backends.** FastAPI with `sse-starlette` cancels the response generator on client disconnect and has
no replay. Run generation detached from the response (a task writing to the stream buffer), serve resume
from the buffer using `Last-Event-ID` and answer 204 when nothing is active, and let the stop endpoint
cancel the task.

**Transport default.** On Next: `useChat` with `resumable-stream` (needs a Redis-compatible store and a
store mapping chat to active stream). Hand-rolled SSE means rebuilding the buffer, the resume route and
the stop endpoint. Session id and open panel live in the router's URL state, not in a store shadowing it.

**Sharing.** Name the unit (a chat or a container), treat a public link as a fork point, revocation is not
deletion, and list what travels (files, instructions, memory scope) in the dialog.

**Multi-agent panel.** When several agents answer one prompt, show a roster strip with per-agent state,
land rounds as record mutations, cancel per round, and treat citation density as a panel parameter.

## References

- Read `references/chat-shell-composer-sessions.md` when building the sidebar, the composer or the sessions
  and search layer: wireframes, collapse order, keyboard/IME matrix, attachment state machine, evidence classes.
- Read `references/artifacts-resume-collaboration.md` before panel mechanics, resume, stop or sharing:
  endpoint contract, reopen reconcile matrix, the Python variant, verified vendor collaboration models.

## Verify

- Render at 1440, 390 and 320 (`frontend-delivery-checklist`); sidebar, panels and composer stay usable.
- Empty state shows 3-4 suggestions that fill the composer without sending.
- Reload mid-stream resumes; Stop ends the generation on the server, and a late stop does not clear a newer stream.
- A killed stream with no stop call renders interrupted with Retry after reopening the session.
- Esc: popover first, then stop; the draft survives.
- A citation click opens the source panel on the right item; closing restores focus; the narrow layout is a sheet.
- Recents never show a status the server did not report.

## Dated traps

- `[ai@7.0, 2026-11-11]` Stop looks done but the model keeps running and billing -> `stop()` and tab close only close the connection -> dedicated stop endpoint, called before the local abort.
- `[ai@7.0, 2026-11-11]` A late stop kills the answer the user just started -> the endpoint cleared the active stream unconditionally -> clear only if it still matches the stopped stream.
- `[ai@7.0, 2026-11-11]` Resume never works with an abort-aware route -> the request abort signal reaches the model call and a disconnect cancels the work -> do not pass it through when `resume` is on.
- `[resumable-stream@2.2, 2026-11-11]` The resume route returns nothing for a finished stream -> the library yields no stream once it ended (its README answers 422) -> handle that branch; the producer runs to completion even if the first reader leaves.
- `[sse-starlette, 2026-11-11]` A reconnect replays nothing -> the library has no buffer and cancels the generator on disconnect -> own buffer and detached task.
- `[claude.ai web, 2026-07-29]` A spec says claude.ai web chat can fork a conversation -> the only evidence is Claude Code's `/fork` (sweep of 2026-07-29, not re-checked) -> do not cite it as a web feature.

## Sources

| Topic | Official entry URL | Read when | Content checked |
|---|---|---|---|
| Resume streams, stop endpoint | https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams | wiring resume or stop | 2026-11-11 |
| Abort and resumable streams | https://ai-sdk.dev/docs/troubleshooting/abort-breaks-resumable-streams | Stop breaks resume | 2026-11-11 |
| Chat persistence and message ids | https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence | storing sessions and active stream ids | 2026-11-11 |
| Transports | https://ai-sdk.dev/docs/ai-sdk-ui/transport | the transport is not the default | 2026-11-11 |
| `resumable-stream` | https://github.com/vercel/resumable-stream | choosing the buffer store | 2026-11-11 |
| `sse-starlette` | https://github.com/sysid/sse-starlette | a FastAPI backend serves the stream | 2026-11-11 |

## Works with

| Skill | Owns | Load when |
|---|---|---|
| `frontend-design` | Visual standard, variants, tokens, breakpoints | the shell layout or a state is designed |
| `accessibility` | Accessible interaction, landmarks, focus, motion | drawer, panel and composer must work with keyboard and screen reader |
| `frontend-delivery-checklist` | The done gate | the shell is about to be called done |
| `testing-e2e-playwright` | Browser tests | a resume or stop journey needs a test |
| `pwa-engineering` | Install, offline, queued sends, keyboard-safe composer | the shell is installable or must survive offline |

Reference exemplar: `assets/chat-shell-mockup.html` is a maintained, brand-free mockup to adapt; the decisions
above are the specification, not the mockup.
