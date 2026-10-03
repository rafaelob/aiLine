# Chat shell, composer, and sessions — implementation contract

Load this when building the sidebar, the composer, or the sessions/search layer. Provenance classes
are the same as SKILL.md: `[observed N/4]` from the 2026-07-29 four-product teardown,
`[verified: source, date]`, `[portfolio requirement]`, `[optional pattern]`.

Nothing in this file describes what a message bubble renders. That is `frontend-ai-generative-ui`.

---

## 1. Shell wireframes (neutral, text-only)

Vendor screenshots are deliberately not shipped: they redistribute branded product shots, they cost
~1-1.5k context tokens per read, and they freeze one day's UI while looking permanent. Text
wireframes rot visibly instead.

### 1.1 Desktop, artifact panel closed

```text
┌────────────────────────┬──────────────────────────────────────────────────────┐
│ ✦ New chat        [⌘K] │  ┌─ session title ─────────────────┐   [share] [⋯]  │
│ 🔍 Search chats        │                                                      │
│                        │                                                      │
│ ── Library ──────────  │              (thread — NOT this skill)               │
│  Artifacts             │                                                      │
│  Images                │                                                      │
│                        │                                                      │
│ ── Projects ─────────  │                                                      │
│  ▸ Acme migration      │                                                      │
│  ▸ Support triage      │                                                      │
│                        │                                                      │
│ ── Pinned ───────────  │                                                      │
│  ★ Runbook draft       │                                                      │
│                        ├──────────────────────────────────────────────────────┤
│ ── Recents ──────────  │  ┌──────────────────────────────────────────────┐    │
│  ⏳ Needs input   ·1   │  │ Message…                                     │    │
│  ⟳ Indexing corpus     │  │                                              │    │
│    Q3 retro            │  ├──────────────────────────────────────────────┤    │
│    Invoice parser      │  │ [+] [Model ⌄] [effort ⌄]      [🎤] [◍] [↑]   │    │
│    (paginate…)         │  └──────────────────────────────────────────────┘    │
│                        │   [+]=attach  🎤=dictation  ◍=voice session  ↑=send  │
│ ── Admin panel ──────  │                                                      │
│ ⌂ avatar  Plan ▾       │                                                      │
└────────────────────────┴──────────────────────────────────────────────────────┘
```

### 1.2 Desktop, artifact panel open (one of three patterns — see the artifacts reference)

```text
┌──────────────┬───────────────────────────┬─────────────────────────────────┐
│  sidebar     │  thread (narrowed)        │  ARTIFACT  [⤢ fullscreen] [✕]   │
│  (or rail)   │                           │  ┌───────────────────────────┐  │
│              │                           │  │ tab: Preview | Code       │  │
│              │  composer stays anchored  │  │                           │  │
│              │  under the NARROWED       │  │  (content render is       │  │
│              │  thread, never under the  │  │   in-thread territory)    │  │
│              │  panel                    │  └───────────────────────────┘  │
└──────────────┴───────────────────────────┴─────────────────────────────────┘
   URL: /c/<session>?panel=artifact&a=<artifact-id>     ← addressable, restorable
```

### 1.3 Mobile (≤ 640px)

```text
┌──────────────────────────┐   sidebar → off-canvas drawer, focus-trapped
│ ☰   Session title    ⋯   │   while open, Escape closes, restores focus
├──────────────────────────┤
│                          │   artifact panel → full-screen sheet or its own
│        thread            │   route with an explicit "back to chat"
│                          │
├──────────────────────────┤   composer pinned; use dvh units, not vh, or the
│ [+] [Model ⌄]  [🎤] [↑]  │   mobile keyboard covers it
└──────────────────────────┘   effort chip and voice control collapse into [⋯]
```

### 1.4 Empty state `[observed 4/4]`

```text
              (no cards, no feature tour, no grid)

                  Localized greeting, one line
            ┌──────────────────────────────────────┐
            │ Message…                             │
            │ [+] [Model ⌄]        [🎤] [◍] [↑]    │
            └──────────────────────────────────────┘
             optional: ONE onboarding banner [observed 1/4]
```

---

## 2. Sidebar responsive collapse order

Declare the order once; do not let it emerge from CSS accident. Collapse from the bottom of the
value stack upward `[portfolio requirement]`:

| Width | Sidebar | What is shed |
|---|---|---|
| ≥ 1280px | full, ~260-300px | nothing |
| 1024-1280px | full, narrower; labels truncate with tooltips | recents page size reduced |
| 768-1024px | icon rail (~56-64px); labels on hover/focus | section headers, plan badge text |
| ≤ 768px | off-canvas drawer behind `☰` | nothing shed — the drawer holds the full stack |

Rail rules: every rail icon keeps an accessible name; the new-chat control stays visually distinct
in the rail (it is the one action users hit blind); collapsed/expanded is a **persisted user
preference**, not only a breakpoint outcome.

---

## 3. Composer: keyboard and IME matrix

The IME row is the one that ships broken `[portfolio requirement]`.

| Input | Expected | Implementation note |
|---|---|---|
| Enter | send | only when not composing and no popover has focus |
| Shift+Enter | newline | never sends |
| Enter **during IME composition** | commit the candidate, **do not send** | gate on the composition flag: set true on `compositionstart`, false on `compositionend`; check it inside the keydown handler. `keyCode 229`/`isComposing` are the two signals; test with a real IME, not a US layout |
| Escape | close popover; if none, blur | must not clear the draft |
| Up-arrow on empty draft | recall previous message into draft | `[optional pattern]`; power-user affordance |
| `/` at position 0 | open command/skills popover | Arrow keys navigate it; Enter selects, does not send |
| `@` | open mention popover | only where the product has multiple agents |
| Ctrl/Cmd+Enter | force send | `[optional pattern]` for products where Enter inserts a newline |
| Tab | leave the field | do NOT hijack for indentation in a chat composer |

Autosize: grow to a ceiling (~8 lines) then scroll internally. Measure with a hidden mirror element
or `field-sizing: content` where supported; never set height from a character count.

Focus after send: keep focus in the composer. Moving focus to the streaming response steals the
keyboard from a user who is already typing the next message.

---

## 4. Attachment state machine

```text
        idle
         │ user picks / drops / pastes
         ▼
    validating ──unsupported type/size──► rejected (inline, keep the draft)
         │ ok
         ▼
    uploading ── progress % ──┐
         │                    │ user cancels ──► removed
         │ transport error ───┴──────────────► failed  ──retry──► uploading
         ▼
      attached  (chip: name, size, type icon, remove ✕)
         │ send
         ▼
      committed (chip becomes read-only in the sent message)
```

Rules `[portfolio requirement]`:

- Validate type and size **before** upload; a rejection after a 40MB upload is a design failure.
- Multiple attachments upload in parallel with per-chip progress; one failure must not discard the others.
- Never block send on an unrelated failed attachment — let the user remove it and send.
- Paste and drag-drop enter the same machine as the picker. Three code paths for one lifecycle is
  how one of them ends up missing the validation step.
- A chip is removable until commit; after commit it is history.
- Never relay files to a model provider from client code. Upload to your own endpoint. (Provider
  MIME/size limits and the proxy pattern belong to `frontend-ai-generative-ui`.)

---

## 5. Sessions, projects, and search contract

### 5.1 Session lifecycle

| Stage | Behaviour |
|---|---|
| create | optimistic local session, replaced by the server id on ack; the URL updates without a history entry the user has to back through |
| title | autogenerated after the first exchange; always user-overridable; regenerate on demand |
| rename | inline, optimistic, revert on failure |
| pin | reorders into a `Pinned` section, not a badge on a recents row |
| move to project | inherits that project's instructions/files context |
| delete | soft, with undo for at least one interaction; hard-delete only after the undo window |
| branch | creates a NEW session with a `parent_id`; both remain listed; lineage visible in both directions |

### 5.2 Recents query contract

- Cursor pagination (`updated_at` descending, stable tiebreak on id). Offset pagination
  double-shows rows as new sessions arrive.
- The row payload carries status, not just a title: `{ id, title, updated_at, status,
  status_detail?, unread? }` with `status ∈ {idle, running, needs_input, failed}`.
- Sort: `needs_input` first, then `running`, then by `updated_at`. A blocked job outranks a busy one.
- Status is server-derived. Client-side optimism on a row that represents server work is how a
  finished-looking job turns out to be dead.
- Poll or subscribe only while the sidebar is visible; pause on `document.hidden`.

### 5.3 Search over chats `[observed 4/4]`

- Search **content**, not only titles. Users search for the phrase they remember.
- Server-side, debounced (~200-300ms), cancel the in-flight request on a new keystroke.
- Result rows show a matched snippet with the term highlighted, plus the session title and date.
- Query lives in the URL so a search view is shareable and back-button-restorable.
- Empty results must distinguish **no match for this query** from **search unavailable**. The same
  blank state for both teaches users the archive is empty when the index is merely down.
- Scope selector (all / this project) where projects exist.

### 5.4 Org primitives — pick two or three `[observed 4/4]`

| Primitive | What it is | Pick when |
|---|---|---|
| Pinned/favorites | user-flagged sessions | sessions are revisited |
| Projects | container with own instructions/files/memory scope | work is grouped and long-running |
| Agent gallery | preconfigured personas/agents | multiple distinct agent behaviours |
| Notebooks | document-grounded surface | source documents drive the work |
| Media library | generated images/video/files | the product generates media |
| Scheduled | recurring or future runs `[observed 1/4]` | the product runs work on a timer |

Role-gated entries (admin console, workspace settings) sit immediately above the account block
`[observed 1/4]`, never mixed into the recents list.

---

## 6. Shell states

| State | Requirement |
|---|---|
| Empty (new user) | greeting + composer only; at most one onboarding banner |
| Empty (returning, no recents) | say the archive is empty; do not show a skeleton forever |
| Loading history | skeleton rows in the sidebar, composer already usable — never block input on history |
| Offline / reconnecting | persistent, non-modal banner; composer accepts input and queues it; never silently drop a send |
| Interrupted response | explicit "response interrupted" affordance with retry, distinct from a completed answer |
| Session not found / no access | explicit; never an empty thread that looks like a new chat |
| Degraded search | say search is unavailable; do not render "no results" |

---

## 7. Accessibility for the shell

The thread's `aria-live`/`role=log` wiring belongs to `frontend-ai-generative-ui`. The shell owns:

- **Landmarks:** the sidebar is `<nav>` with an accessible name; the thread region and composer are
  distinguishable landmarks.
- **Drawer/panel:** correct role, labelled by its heading, focus moved in on open and returned to
  the invoking control on close, Escape closes. A modal drawer traps focus; a non-modal panel must
  not.
- **Rail icons:** every collapsed item keeps a name (visible label, `aria-label`, or tooltip that is
  also the accessible name).
- **Recents status:** never colour-only. A status dot needs text or an icon shape beside it.
- **Composer:** the field has a real label (visually hidden is fine); the send/stop control's
  accessible name changes with its function; the popovers are keyboard-navigable and announce their
  option count.
- **Reduced motion:** `prefers-reduced-motion` disables drawer slide, panel transitions, and status
  pulsing.
- **Focus visible** on every control in the rail and drawer — icon-only controls are where focus
  rings get removed for aesthetics.

---

## 8. Sidebar performance

- Do not virtualize a short list. Virtualize **before unbounded growth**, at the point the list is
  paginated from a server that can return thousands. There is no citable universal row threshold;
  measure your own.
- The only vendor numbers worth quoting anywhere near this subject are product limits, not UI
  guidance, and they concern data grids rather than chat lists — do not launder them into a rule.
- Recents rows must be cheap: no per-row subscription, no per-row timer. One subscription for the
  list, fanned out by id.
- Stop all row animation when the tab is hidden.
