---
name: frontend-agent-chat-shell
description: >-
  Build the application shell around an AI chat thread: sessions/search/projects, sidebar,
  composer attachments/drafts, artifact placement, multi-agent panel, stream resume, and
  interrupted states. Use when building thread-level navigation and continuity; message rendering uses
  frontend-ai-generative-ui.
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.0.2
  category: content-production
  subcategory: technical-writing
  vendor: universal
  lifecycle: active
  coding_agent: true
  user_level: false
  project_level: true
  audience: developer
  output_format: markdown
  modality: text
  short-description: The product shell around an AI chat thread — sidebar, sessions, composer chrome,
    artifact placement, resume
  tags:
  - frontend
  - chat-shell
  - session-sidebar
  - composer
  - artifact-panel
  - stream-resume
  - agent-ui
  - empty-state
  - voice-session
  - branching
  - project_level
---

# Agent Chat Shell

> The thread is not the product. Around every AI chat thread sits a shell — how a session is started,
> found, named, resumed, branched, shared, and how long-running work stays visible while the user is
> looking elsewhere. That shell is where agent-chat products are weakest, because every tutorial
> stops at the message list.

## The seam: this skill stops at the bubble

**Everything inside a message bubble belongs to `frontend-ai-generative-ui`.**

| This skill owns | `frontend-ai-generative-ui` owns |
|---|---|
| Sidebar, stack order, org primitives | The message list, virtualization |
| Recents as a live task surface | Scroll anchoring, jump-to-latest |
| Empty-state hero, onboarding slot | Token/markdown/code streaming render |
| Composer chrome, model chip, dictation vs voice | Tool-call cards, thinking disclosure |
| Sessions/projects/history + search | Message actions (copy/regenerate/edit) |
| Artifact **placement**, panel mechanics | Artifact **content** rendering |
| Stream **resume**, interrupted-response honesty | `aria-live`/`role=log`, SDK wiring |
| Mobile shell, focus transfer | |

If the request is about what a rendered message looks like, route it. Editing *inside* a generated
artifact is not for this skill (use frontend-canvas-doc-editor): selection-scoped patches,
suggested edits, version history.

## Scope

- Building or redesigning a chat UI for an assistant or agent product.
- Adding a session sidebar, history search, projects, or an agent gallery.
- Designing composer chrome: model/effort chip, attachments, drafts, slash and @ popovers.
- Deciding where generated artifacts live (side panel, inline, or their own route).
- Background work must stay visible while the user works elsewhere.
- Streams must survive a refresh, a closed tab, or a dropped connection.
- Adding branching, sharing, or multi-user access to sessions.

## Do NOT use for

- Anything rendered inside a message bubble -> `frontend-ai-generative-ui`.
- Dialogue content, persona, tone, fallback/repair copy -> `conversational-ai-ux`.
- Transport mechanics (WebSocket/SSE plumbing, reconnect backoff) -> `realtime-websockets`.
- Trust, disclosure and AI-labelling UX -> `ai-trust-transparency-ux`.
- Remediating an already-dense screen -> `ui-density-refactor`.

## Provenance legend

Every claim carries its evidence class — an invariant you can lean on is not the same object as a
pattern one vendor ships.

- `[observed N/4]` — counted across four 2026-07-29 teardowns (ChatGPT Pro, Onyx v4.4.0, Claude,
  Gemini Ultra). **N=1 or 2 is a menu option, not a rule.**
- `[verified: source, date]` — external primary source, named and dated.
- `[portfolio requirement]` — our own products need it; not a market claim.
- `[optional pattern]` — defensible, deliberately not universal.

## Pillar 1 — three zones and a near-constant sidebar order

The shell is a collapsible left sidebar (~260-300px, collapsing to an icon rail), a main canvas, and
— conditionally — a third surface for artifacts (Pillar 4 decides whether it exists at all).

Sidebar stack order, top to bottom `[observed 4/4]`: **new-chat CTA** (most prominent control) ->
**search over chats** (never behind a menu) -> **libraries** -> **org primitives** -> **recents with
live status** (Pillar 2) -> *(role-gated entry such as an admin console sits HERE, just above the
account block)* -> **account + plan badge**.

**Org primitives are a menu, not a checklist** `[observed 4/4]`. Each product shipped two or three of
{pinned, projects, agent gallery, notebooks, media library, scheduled} at nav level; none shipped all.
A v1 shipping six has not made a product decision — it deferred one into the navigation, where the
user pays for it.

**Empty state is one moment, not a tour** `[observed 4/4]`: a localized greeting and a centered
composer, nothing else. At most one onboarding banner `[observed 1/4]`. No feature grid, no cards.

**Theme:** all four were dark at capture time `[observed 4/4]`, but that is `[optional pattern]`,
not an invariant — four screenshots of a default setting are not evidence that light mode is
second-class. Build both from tokens and let the user or OS decide.

**Variant — a multi-agent panel** `[observed]`: when several agents answer one prompt, the roster is
a **strip** with per-agent state, and rounds land by **mutation of a round record**, not token
streaming — nobody reads five streams. Cancel is therefore **per round**, mid-round, leaving finished
rounds intact, and **citation density is a panel parameter**: the answer is judged on whether each
claim traces. Seen in a production healthcare app; multi-*agent*, not Pillar 5's withdrawn
multi-*human* pattern.

## Pillar 2 — recents are a task surface, not a history list

`[observed 2/4]` for live status inside recents, `[portfolio requirement]` for anything that runs
long. Two of four surfaced in-flight work in the sidebar list itself: per-chat spinners, and a status
dot on a running generation. Where a session holds work that outlives the user's attention, that row
is the cheapest correct place to say so — state belongs where attention already is, not behind a bell
icon.

**Status-structured beats a single dot** `[optional pattern]`: richer surfaces group by state
instead of decorating a flat list — completed / needs-input / scheduled, or per-agent status with
the action currently running. `needs-input` pays for itself immediately: a job blocked on the user
is invisible in a flat list and unmissable in a grouped one.

Rules that hold regardless of grouping:

- A row's status derives from server state, never from local optimism.
- `needs-input` outranks `running` in sort order; a blocked job beats a busy one.
- Terminal failure stays visible until acknowledged; a job dying silently teaches the user to
  distrust the whole surface.
- Do not animate every row. Motion on a list is paid for by every row that is not moving.

## Pillar 3 — the composer is the identity anchor

The composer tells the user who they are talking to before they commit a message.

**Model/effort chip, visible pre-send** `[observed 3/4]` — three of four exposed the active model
(and in one, its effort level) as a chip in or beside the input; the fourth exposed tools and a
timer. Where more than one model or effort tier exists, showing it pre-send is what makes the choice
real rather than a settings-screen abstraction.

**Dictation and a voice session are two different affordances** `[observed 2/4]`. Two products placed
a microphone *and* a waveform control side by side — not two doors to one feature:

| Affordance | What it does | Where output lands |
|---|---|---|
| Dictation (mic) | speech -> text | into the draft, editable, user still sends |
| Voice session (waveform) | live duplex conversation | its own surface; the thread is a transcript |

Collapsing them into one button forces a user who wanted to dictate one sentence into a live call,
and is invisible in review because one button looks simpler.

**The rest of the contract** `[portfolio requirement]`: Enter sends, Shift+Enter newlines, and **IME
composition must not send** (check the composing flag inside the keydown handler, or every CJK and
dead-key user sends half a word); autosize to a ~8-line ceiling then scroll internally; per-session
draft persistence; an attachment pipeline with visible states and type/size validation *before*
upload; slash and `@` popovers where there are multiple agents; and a send control that **morphs
into stop in place** — a stop button appearing elsewhere loses the user's pointer. Before building,
read `references/chat-shell-composer-sessions.md` for the keyboard/IME matrix, the attachment state
machine, the sidebar collapse order, and the sessions/search contract.

## Pillar 4 — artifact placement: three patterns, and the choice is real

There is no universal "reserve a right panel". Canvas is no longer available in ChatGPT's current
models: writing and coding moved into **inline writing blocks and code blocks in the chat response**,
openable full screen, canvas surviving on legacy models until they sunset `[verified:
help.openai.com art. 20001246 + ChatGPT release notes, re-checked 2026-07-29]`. Yet a dedicated
surface stays alive elsewhere: Claude Artifacts and Gemini Canvas keep a side panel, and Onyx ships a
**dedicated route** — `web/src/app/craft/`, its own layout, agent loop left, live preview right
`[verified: Onyx v4.4.0 source tree, 2026-07-29]`.

- **Side panel** — iterated over many turns, compared against the thread. Costs width, a mobile
  fallback, a focus context.
- **Inline + fullscreen** — read or lightly edited, one per turn, one layout everywhere. No
  side-by-side; long artifacts push the thread away.
- **Dedicated route** — the work *is* the session. Own URL and layout; a second shell.

Before choosing, read `references/artifacts-resume-collaboration.md` §1.1 — a six-question selection
table with the costs to accept in writing.

Four mechanics are not optional whichever you pick `[portfolio requirement]`: **URL addressability**
(an open artifact is a location, or it cannot be shared, bookmarked or restored by back-button);
**focus transfer** in on open and back to the invoker on close, without trapping; a **mobile fallback
that is a real design**, sheet or route, not a media query; and **per-session** open/close state.

## Pillar 5 — sessions, search, and branching as a first-class primitive

- **Title autogeneration** after the first exchange, always overridable; rename, pin and delete carry
  undo, because delete without undo is a support-ticket generator.
- **History = pagination + full-text search** `[observed 4/4]`. Matching titles only is not search:
  users remember content.
- **Projects** are containers with their own instructions, files and sometimes memory scope, applied
  to every chat inside. **Agent galleries, gems and notebooks** are preconfigured entry points, not
  extra chats — the value is arriving pre-loaded.

**Branching is a first-class invariant, not a message-action footnote.** Editing an earlier turn
forks; the original must not be destroyed. It belongs to the shell rather than the message list
because a fork is a **new session with a parent** — it needs a row in recents, a title, visible
lineage to its origin, and its own URL. The message list owns only the affordance that triggers it.
The vendor wording is worth copying: chats "can be branched, not collaborated on synchronously", and
"Members can see the branched chat; chat creators can make it private by moving it out" — so branch
visibility needs a deliberate decision and an escape hatch
`[verified: help.openai.com "Projects in ChatGPT", 2026-07-29]`.

That same sentence states the anti-invariant: **synchronous co-presence in one thread is not the
model.** Group chats shipped 2025-11 and were retired 2026-07-09; do not build real-time
multiplayer because a competitor briefly had it. It says nothing against *asynchronous*
collaboration, which is alive and specified below.

> **Never claim claude.ai web chat has a fork feature** `[verified: sweep 2026-07-29 — no official
> feature; the only fork on claude.ai web is a third-party userscript]`. The `/fork` evidence is
> Claude **Code**.

## Pillar 6 — resume, and the honesty of an interrupted response

A cut stream must render as an **interrupted response with a retry**, never as a short answer that
reads as complete `[portfolio requirement]`: nothing tells the reader something is missing, so they
act on it.

Resumable streaming is not bare SSE `Last-Event-ID`; it is an application-level stream ID plus a
server-side buffer the client replays into
`[verified: ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams, 2026-07-29]`.
`useChat({ resume: true })` "automatically reconnects to active streams" via a GET to
`/api/chat/[id]/stream` — a handler you must write, backed by the `resumable-stream` buffer
(`assistant-ui`: `createResumableAssistantStreamResponse`). It covers **page reload, tab close,
connection loss and navigating away**; device switch is not addressed, so never promise it in copy.

**The correction that catches everyone:** "client-side aborts are treated as disconnects" and "that
abort is a disconnect signal, not a request to stop generation". So `stop()` does **not** stop the
model — you must "add a dedicated stop endpoint that persists the partial response, cancels the
active work, and clears the active stream". Without it, stop hides a generation that keeps running
and billing, and it returns on the next resume.

So the session row must know a stream is active (Pillar 2), the stop control must call that endpoint
rather than only aborting the fetch (Pillar 3), and reopening a session must reconcile "server still
generating" against "local history ended". Read the reconcile matrix and endpoint contracts in
`references/artifacts-resume-collaboration.md` before wiring any of it.

## Collaboration contract `[optional pattern]`

Async sharing is shipped, and the three live models differ in ways that move your data boundary. All
three verified 2026-07-29; for the full role names, quotes and revocation semantics
read `references/artifacts-resume-collaboration.md` before designing any share dialog. The shapes:

- **Container share, two tiers** — chat vs edit access; **editors may add members but not remove
  them**; container-scoped memory switches on automatically once shared; members branch each
  other's chats `[verified: help.openai.com "Projects in ChatGPT"]`.
- **Container share, view vs edit, plan-gated** — "Can view" / "Can edit", Team and Enterprise
  only, found through a "Shared with me" surface `[verified: support.claude.com "What are Projects"]`.
- **Public link the recipient continues as their own** — anyone with the link may read *and
  reshare* `[verified: support.google.com/gemini/answer/13743730]`.

Four rules fall out: **name the unit** (a chat and a container are different grants), **a public link
is a fork point, not a snapshot**, **revocation is not deletion**, and **show what travels** — files,
instructions and memory scope, listed in the dialog. That last one is the leak that actually happens.

## Framework menu

The anatomy is framework-neutral by construction and has to be: this portfolio's chat surfaces
include React/Next.js (majority), SvelteKit and plain JavaScript `[portfolio requirement]`.

- **Thread transport + resume** — AI SDK (`useChat` + `resumable-stream`), assistant-ui, or
  hand-rolled SSE with your own stream-ID buffer. Resume decides: hand-rolling means re-implementing
  the buffer, the GET resume route, *and* the stop endpoint.
- **Shell layout** — your own. No library owns this, or will give you the stack order.
- **URL state** for session and open panel — the framework router first; a state library shadowing
  the URL drifts from it.
- **Recents list** — plain until genuinely long; virtualize *before* unbounded growth, not at a
  number someone invented.

Version-pinned SDK details rot fastest: check `package.json` before applying any hook signature from
this skill or its references.

## Workflow

1. **Draw the seam.** Split the request into shell vs in-thread, and route the in-thread half to
   `frontend-ai-generative-ui` explicitly, in writing.
2. **Choose the org primitives** — two or three, named, decision recorded. Not six.
3. **Lay out the three zones**, then decide whether the third surface exists at all (Pillar 4).
4. **Build the composer first**: highest traffic, most invisible failure modes (IME, drafts,
   dictation vs voice).
5. **Wire session state to the URL**: session id, open artifact, active panel.
6. **Implement resume and the dedicated stop endpoint together** — resume without the stop endpoint
   produces a stop button that lies.
7. **Design the four shell states** — empty, loading history, offline/reconnecting, interrupted
   response — before styling anything.
8. **Walk the shell at 360px**, keyboard-only, then with a screen reader for the panel transition.

## Common pitfalls

- **One button for dictation and voice session** (Pillar 3) — the most common error here.
- **Enter sending mid-IME composition.** Ships broken for every CJK user; no English test catches it.
- **A stop button that only aborts the fetch** — the model keeps generating and billing, the partial
  is lost. **A truncated stream rendered as a finished answer** is the same class of lie.
- **Recents showing *optimistic* status** — a row reads "done" because the client assumed so.
- **Sidebar that only collapses via a media query**; **draft lost on navigation**; **titles that
  never regenerate** ("hi" forever); **search over titles only**, when users remember content.
- **Building synchronous multiplayer chat** because a vendor shipped it — it was withdrawn.

## Validation checklist

- [ ] Every in-thread concern routed to `frontend-ai-generative-ui`, not implemented here.
- [ ] Sidebar order matches Pillar 1; org primitives are two or three, on record; new-chat and chat
      search both reachable without opening a menu.
- [ ] Recents show live status for work outliving attention, `needs-input` above `running`, derived
      from server state — never optimistically.
- [ ] Dictation and voice session are distinct controls with distinct destinations.
- [ ] Model/effort visible before send wherever more than one exists.
- [ ] Enter/Shift+Enter correct during IME composition; drafts survive navigation.
- [ ] Send morphs to stop in place, and stop calls a dedicated endpoint that persists the partial,
      cancels the work, and clears the active stream.
- [ ] Resume wired for reload, tab close, connection loss and navigation away; device switch promised
      nowhere in the copy.
- [ ] Interrupted responses render as interrupted, with retry — never as a finished answer.
- [ ] Placement chosen from the three patterns with its cost accepted in writing; open artifact and
      active session both in the URL.
- [ ] Panel open/close transfers focus and is announced; Escape closes without trapping.
- [ ] Mobile shell is a designed fallback, verified at 360px.
- [ ] Branching creates a session with visible lineage, its own row, and its own URL.
- [ ] Share dialog names the unit, shows what travels, and does not imply revocation deletes.
- [ ] Both themes render from tokens; neither is hard-coded.

## Reference files

- Read `references/chat-shell-composer-sessions.md` when building the sidebar or composer: annotated
  wireframes, collapse order, keyboard/IME matrix, attachment state machine, sessions/search.
- Read `references/artifacts-resume-collaboration.md` before panel mechanics, resume or sharing:
  endpoint contracts, session-reopen reconcile matrix, verified vendor collaboration models.
- `assets/chat-shell-mockup.html` — open this self-contained, brand-free, theme-aware mockup and
  adapt it. A maintained exemplar, not the specification — the pillars are.

