# Artifact placement, stream resume, and collaboration — implementation contract

Load this when deciding where artifacts live, when wiring resume/stop, or when adding sharing.
Provenance classes as in SKILL.md: `[observed N/4]`, `[verified: source, date]`,
`[portfolio requirement]`, `[optional pattern]`.

Artifact **content** rendering (code highlighting, tables, charts inside a message) is
`frontend-ai-generative-ui` territory. This file is about the surface it lives on.

---

## 1. Artifact placement: three verified patterns

The "reserve a right panel" rule is wrong as a universal. The market split, verified 2026-07-29:

| Pattern | Live examples | Verification |
|---|---|---|
| Persistent side panel | Claude Artifacts, Gemini Canvas | `[observed 4/4 teardown: dedicated library/artifact entries in the sidebar]` |
| Inline block + fullscreen | ChatGPT, post-canvas | `[verified: OpenAI ChatGPT release notes, help.openai.com, 2026-07-29 — canvas unavailable in current GPT-5.5 Instant/Thinking; writing and coding now in inline writing blocks and code blocks in the chat response; legacy models keep canvas until sunset]` |
| Dedicated session route | Onyx v4.4.0 Craft | `[verified: Onyx v4.4.0 source tree, 2026-07-29 — web/src/app/craft/ with its own page.tsx and layout.tsx; agent loop left, live preview right]` |

### 1.1 Selection criteria

| Question | Side panel | Inline + fullscreen | Dedicated route |
|---|---|---|---|
| Is the artifact iterated over many turns? | yes | no | yes |
| Must the user see thread and artifact together? | yes | no | yes (its own split) |
| More than one artifact live per session? | awkward | natural | one per route |
| Is one layout across web/mobile/desktop a goal? | costly | cheapest | costly |
| Is the artifact the *point* of the session? | no | no | yes |
| Width budget on the primary breakpoint | ≥ 1280px comfortable | any | its own layout |

Costs to accept explicitly, in writing, before building:

- **Side panel** — steals thread width; two focus contexts; needs a real mobile fallback; the
  composer must stay under the narrowed thread, never under the panel.
- **Inline + fullscreen** — no side-by-side comparison; a long artifact pushes the conversation out
  of view; users doing sustained editing will ask for the panel back (documented publicly when a
  major vendor made this exact move).
- **Dedicated route** — a second shell to design, build and maintain; leaving the thread is a
  navigation, so the route needs its own way back and its own session identity.

### 1.2 Panel mechanics `[portfolio requirement]`

```text
URL is the source of truth:
  /c/<session>                          panel closed
  /c/<session>?panel=artifact&a=<id>    panel open on a specific artifact
  /c/<session>/artifact/<id>            dedicated-route variant

open(id):
  1. push URL state (replace, not push, when toggling the same artifact)
  2. render panel
  3. move focus to the panel heading; announce via a polite live region
  4. persist {sessionId -> lastOpenArtifactId, panelOpen} for session reopen

close():
  1. pop URL state
  2. return focus to the control that opened it
  3. keep the persisted last-open artifact (reopening the session restores it)
```

- Escape closes a non-modal panel without trapping focus; a modal sheet (mobile) traps until closed.
- The panel is resizable with a persisted width `[optional pattern]`; clamp so the thread never
  drops below a readable measure.
- Panel open/close state is **per-session**, not a global preference.
- On mobile, the panel is a full-screen sheet or a route with an explicit "back to chat" — not a
  narrow column.

---

## 2. Stream resume contract

`[verified: ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams, fetched 2026-07-29]`

Resumable streaming is **not** bare SSE `Last-Event-ID`. It is an application-level stream id plus a
server-side buffer the client replays.

### 2.1 The pieces

| Piece | What it does |
|---|---|
| `useChat({ resume: true })` | "automatically reconnects to active streams" |
| GET `/api/chat/[id]/stream` | a handler **you create**; "resumes the existing stream if one is found". The `resume` option "triggers a GET request" to it |
| `resumable-stream` package | manages the buffer storage (Redis) |
| `activeStreamId` per session | server-side record of the stream in flight |
| assistant-ui equivalent | `createResumableAssistantStreamResponse` `[verified: assistant-ui docs, 2026-07-29]` |

### 2.2 What resume actually covers

Covered, per the official doc: **page reload, tab close, connection loss, navigating away**.

**Device switch is not addressed.** Do not promise cross-device continuation in UI copy, release
notes, or a design doc. If the product needs it, treat it as unbuilt work, not a library feature.

### 2.3 The stop() correction — read this twice

Quoting the same source:

- "client-side aborts are treated as disconnects"
- "that abort is a disconnect signal, not a request to stop generation"
- "Closing a tab, refreshing the page, or calling `stop()` only closes the current HTTP connection"
- the fix: "add a dedicated stop endpoint that persists the partial response, cancels the active
  work, and clears the active stream"

So a naive stop button **lies**. The user sees generation end; the model keeps generating, keeps
billing, and the abandoned stream reappears on the next resume.

```text
POST /api/chat/<session>/stop
  1. persist the partial response as a message (marked interrupted)
  2. cancel the upstream generation
  3. clear activeStreamId for the session
  4. return the persisted message so the client reconciles instead of guessing
```

The composer's stop control calls this endpoint **and then** aborts locally — in that order. Abort
first and you race the persistence.

### 2.4 Session-reopen reconcile matrix

On opening a session, local history and server state can disagree. Decide all four cases:

| Server `activeStreamId` | Local last message | Action |
|---|---|---|
| present | ends with a user turn | attach to the stream (resume); show the assistant turn as in-flight |
| present | ends with a partial assistant turn | resume and replay the buffer; de-duplicate against the local partial by stream id, never by text prefix |
| absent | ends with a partial assistant turn | the stream died without a stop call: render **interrupted response + retry**, never a finished-looking answer |
| absent | ends with a complete assistant turn | nothing to do |

De-duplicate on stream id and message id. Prefix matching looks like it works until the model emits
a token that differs from the buffered replay, and then the message silently doubles.

### 2.5 Interrupted-response honesty `[portfolio requirement]`

A cut stream renders with a visible marker and a retry, and never as a short-but-complete answer. A
truncated answer presented as finished is indistinguishable, to the reader, from a real answer —
which is the same failure class as an empty result that actually meant "we could not look".

- Distinct visual treatment plus text; not colour alone.
- Retry re-sends from the last user turn and preserves the partial as history `[optional pattern]`,
  or discards it — pick one and be consistent, because a user who sees the partial vanish assumes
  data loss.
- Under degradation ("model unavailable", "rate limited"), say which, and do not present an empty
  assistant turn as an answer.

---

## 3. Collaboration models — verified vendor behaviour

All three verified 2026-07-29. `[optional pattern]` as a whole: async sharing is real and shipped,
but which model you copy is a product decision, not a default.

### 3.1 ChatGPT shared projects
`[verified: help.openai.com "Projects in ChatGPT", 2026-07-29]`

- Two access levels: **chat access** — see and interact with the project's chats, files and
  instructions; **edit access** — adds updating instructions, uploading/removing files, and
  inviting others.
- Visibility: "Only those invited" or "Anyone with a link"; only the owner controls whether the link
  is open. Workspace-link joiners arrive with chat access by default, upgradeable individually.
- Only project owners invite or remove collaborators.
- Members can create chats, **branch another member's chat**, and move existing chats in.
- The shared project has its own **project-only memory** scope.
- Removing all collaborators does not close an open workspace link — visibility must be set back to
  invite-only. This is the revocation trap worth copying as a warning, not as a behaviour.
- Sharing a single chat is a different, narrower grant: viewers see only that chat, not the
  project's other chats, files, instructions or history.

### 3.2 Claude Projects
`[verified: support.claude.com "What are Projects", 2026-07-29]`

- Two permission names: **"Can view"** — "Members can see project contents, knowledge, and
  instructions, and chat within the project, but cannot edit it"; **"Can edit"** — "Members can
  modify project instructions and knowledge, add/remove members, update member settings, and
  actively contribute to the project."
- Team and Enterprise plans only.
- Creators can share to specific members rather than making a project fully private or
  organization-wide, and can later make a private project org-visible.
- Recipients find shared projects through a "Shared with me" surface, with email notification.
- **Correction on record:** an earlier draft of our own spec called these roles "Can use"/"Can
  edit". The verified names are **"Can view"/"Can edit"**. Ship the verified names.

### 3.3 Gemini public chat link
`[verified: support.google.com/gemini/answer/13743730, 2026-07-29]`

- Share → "Share conversation" creates a public link (`g.co/gemini/share/...`).
- "anyone with the link can read the chat, reshare it with others" — access is not limited to the
  people you sent it to.
- The recipient can **"Continue this chat"** on their own. A share is therefore a **fork point**,
  not a read-only snapshot. Exceptions: not available to under-18 users; Gem-based chats cannot be
  continued.
- Revoke via Settings & help → "Your public links" → "Delete public link" (or delete all).
- After deletion, old links report that the chat no longer exists — but copies already posted
  elsewhere are not recalled, and the chat is not erased from activity history.

### 3.4 Design rules that fall out of all three

- **Name the unit.** "Share" alone is ambiguous between a chat and a container of chats, and users
  read it as the narrower one — then leak the wider one.
- **A public link is a fork point.** If recipients can continue, the session has descendants outside
  your control. Disclose that at share time.
- **Revocation ≠ deletion.** Killing a link stops future access only. Copy must not imply recall.
- **Show what travels:** files, instructions, and memory scope crossing the boundary, listed in the
  share dialog. This is the leak that actually happens in practice.
- **Separate content rights from membership rights.** In two of three models, "can edit" also means
  "can invite". Decide deliberately whether yours does.
- **Branch ownership:** when a member branches another member's chat, decide who owns the branch,
  whether the original author sees it, and whether it inherits the container's visibility. Silence
  here is how a private exploration becomes visible to a team.

### 3.5 The anti-invariant
`[verified: ChatGPT group chats shipped 2025-11, retired 2026-07-09]`

Synchronous multiplayer in one thread was shipped by a major vendor and withdrawn. Treat
co-presence in a single thread as tested-and-withdrawn, not as a gap to fill. This is **not**
evidence against asynchronous collaboration, which the three models above show is alive.

---

## 4. Implementation checklist

- [ ] Placement pattern chosen from the three, with its cost written down.
- [ ] Open artifact and active session are both in the URL; back-button behaves.
- [ ] Focus moves in on open and returns to the invoker on close; Escape closes without trapping.
- [ ] Mobile fallback is a designed sheet or route, verified at 360px.
- [ ] Panel state persists per session, not globally.
- [ ] `resume` wired with a real GET resume handler and a buffer store.
- [ ] A dedicated stop endpoint exists and persists the partial, cancels the work, clears the
      active stream; the client calls it **before** aborting locally.
- [ ] No UI copy promises cross-device continuation.
- [ ] All four reconcile cases handled; de-duplication is by id, never by text prefix.
- [ ] Interrupted responses are visually and textually distinct from complete ones, with retry.
- [ ] Share dialog names the unit, lists what travels, and does not imply recall.
- [ ] Branch ownership and visibility inheritance are decided and documented.
- [ ] No synchronous multiplayer thread was built on the strength of a withdrawn feature.
