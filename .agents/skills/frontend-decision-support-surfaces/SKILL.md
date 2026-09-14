---
name: frontend-decision-support-surfaces
description: >-
  Build a one-item review, approval, moderation, or triage surface with claim/lease, evidence,
  rationale, expected-state conflict handling, audit history, and human override of AI
  suggestions. Trigger when a person commits a decision on a queue item; monitoring dashboards
  use frontend-dashboards.
context: fork
agent: frontend
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.0.3
  category: content-production
  subcategory: technical-writing
  vendor: universal
  lifecycle: active
  coding_agent: true
  user_level: true
  project_level: false
  audience: developer
  output_format: markdown
  modality: text
  short-description: Build queue-and-decide surfaces — approval, review, moderation and triage queues
    with rationale, guards and audit
  tags:
  - frontend
  - approval-queue
  - review-queue
  - moderation
  - triage
  - human-in-the-loop
  - audit-trail
  - optimistic-concurrency
  - rbac
  - work-queue
  - user_level
---

# Frontend Decision-Support Surfaces

> A dashboard tells you that something needs attention. This surface is where one person takes **one
> item**, reads the evidence, and commits a decision that carries their name. The second job is almost
> always hand-rolled from scratch — repeatedly, inside the same product, with the safety mechanics
> reinvented differently each time.

## Scope

The unit of work is **one item, one human, one committed decision**. Neighbours own the adjacent
problems; the first two are the ones people actually confuse:

| Request | Owner |
|---|---|
| A board that *monitors* — KPIs, trends, "is anything wrong?" | `frontend-dashboards` |
| Pane behaviour per window width, generic list-detail, empty-state families | `frontend-screen-archetypes` |
| The confidence display, model card or contestability widget itself | `ai-trust-transparency-ux` |
| Accept/reject of AI suggestions **inside a document editor** | `frontend-canvas-doc-editor` |
| Bot persona, dialogue repair, turn design | `conversational-ai-ux` |

**The seam with dashboards, stated once:** a dashboard's job ends when it has made a problem *visible*;
this skill's starts when a human must *act on one instance of it*. "14 items pending" is a dashboard
widget; opening item 7 and pressing Reject is this skill. Fusing them yields a surface bad at both —
sparklines the reviewer never reads, and no rationale field for the auditor.

## Step 1 — name the decision before drawing anything

One sentence per action: **who** decides, **what** they commit, **on what evidence**, and **whether it
can be undone**. If all four will not fill in, the surface is not designable yet — and that gap is where
the reinvention comes from.

| Family | The decision | Signature risk |
|---|---|---|
| **Approve / reject** | authorize an effect (spend, publish, grant) | irreversible; needs authority checks and four-eyes |
| **Triage / route** | choose *who handles this*, not the outcome | cheap to undo, so over-confirming wastes the reviewer |
| **Moderate** | classify content against a policy | policy drift; store the policy version with the decision |
| **Investigate** | reconstruct what happened; often decides nothing | read-only; confirm dialogs here are pure friction |

**Reversibility sets the ceremony**: a reversible routing decision gets one click, an irreversible
authorization a confirm plus a rationale. And the record must capture **what the decider saw**, not just
what they chose — a moderation verdict with no policy version cannot be defended six months later.

## Step 2 — queue mechanics

Not a list with a filter: a work-allocation mechanism. Its parts:

- **Mine vs pool.** Every item is unclaimed, mine, or someone else's — show all three, and never let the
  pool view hide that an item is taken. Handing one item to two reviewers is this surface's defining bug.
- **Claim as a lease, not a flag.** A claim with no expiry becomes a permanent orphan the first time a
  browser closes. TTL, renew while the tab is active, release on navigate-away, and surface *who* holds
  it *until when*.
- **Ordering is a declared product decision.** Priority, FIFO or risk-score — pick a default and name it
  on screen. **Never silently reorder under the cursor**: an item that moves between click and mouse-up
  produces a decision on the wrong record.
- **Aging only means something against a target.** Elapsed time plus the breach threshold (approaching /
  breached), with breach *filterable*, not merely coloured.
- **Four escape hatches, all of them:** *skip* (back to pool), *defer* (mine, with a wake-up time),
  *escalate* (more authority), *reassign* (someone specific). Accept/reject alone forces the reviewer to
  guess, and guesses are the worst output this surface has. NN/g names rigid flows with "no escape
  hatches or flexibility in sequence" as the anti-pattern, and says users need "a clearly marked
  'emergency exit' to leave the unwanted action" `[verified: NN/g "8 Design Guidelines for Complex
  Applications", Kaplan 2020-11-08]`.
- **Count honesty.** "14 pending" must mean fourteen items *this user can act on*. A badge counting items
  behind a permission wall teaches people to distrust the number.

**Precedent worth knowing:** the GOV.UK Task list is for services whose users "do not want to, or cannot,
complete all the tasks in one sitting" and who "need to be able to choose the order", with a per-item
status that "indicates whether they can start it" — and explicitly **not** for a fixed-order flow
`[verified: GOV.UK Design System, Task list]`. Borrow that contract, not the visual.

Read `references/queue-mechanics-and-board-variant.md` before building claim, ordering, aging, bulk
selection, or a column board.

## Step 3 — the decision surface

Compose it as **list + detail + action bar**. Pane-width rules belong to `frontend-screen-archetypes`,
but one canonical behaviour is worth quoting because hand-rolled queues get it backwards: when an
expanded two-pane view narrows, "the detail pane remains visible and the list pane is hidden"
`[verified: Android Developers, Canonical layouts (list-detail)]`. The reviewer's context is
the item, not the list.

What this skill adds inside that layout:

- **An evidence pane, snapshotted at decision time.** Payload, diff, attachments, computed risk signals —
  without leaving the surface. If deciding needs another tab, the surface is incomplete. Re-deriving the
  evidence later from live data produces an audit trail that lies.
- **A history timeline**: transitions, actors, timestamps, prior rationales. What makes a queue
  defensible, and the most commonly omitted part.
- **An action bar that is stable and last.** Fixed position so it does not shift as evidence loads;
  destructive separated from safe; everything keyboard-reachable. Never disable an action without saying
  why — a greyed Reject with no explanation reads as a broken screen.
- **Remember the third action.** Real approval flows are rarely binary: approve / **approve with edits** /
  reject. Omitting the middle one forces reject-and-recreate, destroying the audit chain.

## Step 4 — commit safely: rationale, guard, audit

Where independent implementations diverge most, and where divergence costs most. Four mechanics.

**1. Rationale, required where it matters.** Free text on reject, on override of a recommendation, and on
any irreversible action — but *not* on the happy path, or reviewers type "ok" forever and the column
becomes noise. Enforce by **disabling the commit** until the field is non-empty after trimming, not by
rejecting the request afterwards.

**2. An optimistic-concurrency guard, always.** The client sends, with the action, a token proving *which
state it was looking at*; the server refuses if it moved. Two flavours work: a **version token**
(`lock_version` read on GET) or an **expected-state token** (`expected_state: "pending"`). Prefer the
version token when the record has many mutable fields; expected-state reads better when the guard is
really about a state machine.

The refusal is `409 Conflict` — "a request conflict with the current state of the target resource"
`[verified: MDN, 409 Conflict, citing RFC 9110 §status.409]`. What matters is the client
behaviour, and most implementations get two of these three:

- **Distinguish the flavours.** "Someone else edited it", "already decided" and "expired" are different
  sentences to a reviewer. One generic "conflict" is a support ticket.
- **Reload the item immediately.** A 409 banner over stale data is worse than the original error: the
  screen is now confidently wrong.
- **Announce it assertively.** The action failed — exactly what MDN reserves `aria-live="assertive"` for,
  updates of "the highest priority" that "should be presented to the user immediately", under the
  standing warning not to use it "unless the interruption is imperative"
  `[verified: MDN, aria-live]`. Queue-count changes get `polite`.

**3. Ceremony sized to consequence.** WCAG 2.2 SC 3.3.4 (Level AA) requires **at least one** of three
properties for legal, financial or data-changing submissions: reversible, checked for input errors with a
chance to correct, or a "mechanism… for reviewing, confirming, and correcting information before
finalizing" `[verified: W3C WAI, Understanding SC 3.3.4]`. Read it as permission to *stop
confirming everything*: make the decision reversible and the criterion is met with no dialog at all.
Confirm-everything queues are why reviewers develop click-through reflexes.

**4. Four-eyes where authority demands it.** The preparer cannot be the authorizer — NIST's
separation-of-duty definition: "the person authorizing a paycheck should not also be the one who can
prepare them" `[verified: NIST CSRC Glossary, separation of duty, per NIST SP 800-192]`. Show
the first approver and their rationale, disable the second approval for that same actor, and say *why*.
Treat every client-side authority check as **defence in depth, never the barrier** — the server decides;
the UI only avoids offering an action that will fail.

Read `references/decision-commit-integrity.md` before wiring rationale enforcement, the guard, the 409
taxonomy, bulk commits, undo, or the audit-record shape.

## Step 5 — the AI suggestion in the loop

Once a model pre-computes a recommendation this becomes a human-in-the-loop control. The widget that
*renders* confidence and explanation belongs to `ai-trust-transparency-ux`; the **decision economics**
belong here.

- **Three response modes, not two.** Auto (model acts, humans audit after), assist (model proposes, human
  commits), manual (model stays out). One product ships exactly this `auto | assist | manual` triad per
  item `[observed]` — worth copying, because it turns "how much do we trust it here?" into a per-item
  setting instead of a deploy.
- **Override must cost the same as accept.** One click to accept versus a modal plus dropdown plus reason
  to override is not oversight; it is a rubber stamp with paperwork. And **never pre-fill the committed
  decision** — a pre-selected radio button is an automation-bias generator.
- **Track disagreement as a first-class metric**: override rate per model version, category and reviewer.
  Near zero means the humans stopped looking; near one means the model should not suggest. Invisible
  unless you record *suggested vs committed* on every item.
- **Supervision console.** Agent systems need takeover and release: a supervisor claims a running
  interaction, acts, hands it back — **with a reason on release** `[observed]`. Release-without-reason
  logs the handoff and loses the cause.

Read `references/hitl-and-supervision.md` when a model suggests, scores or acts before the human.

## Step 6 — anti-fatigue

Fatigue is not a comfort concern; it is the mechanism by which bad decisions get committed.
**Keyboard-first**: next/prev item, approve, reject, defer, focus-rationale — all mouse-free, all in a
visible shortcut panel — and **return focus deliberately** after each commit, to the next item,
announced; focus dumped to `<body>` forces a full re-orient every cycle. **Bulk only where the row
genuinely summarizes the evidence.** **Reduce clutter without reducing capability** (NN/g's sixth
guideline) by progressively disclosing secondary evidence rather than deleting it, and do not make the
human the retry loop — if an automated step failed, offer retry-with-fix, not manual re-entry. **An empty
queue is a success state**: "nothing waiting", last-checked time, visually distinct from "your filter
matched nothing".

## Step 7 — multi-actor freshness, and queue state in the URL

Queues are the one surface where *other humans* change your data while you look at it. Subscribe to
changes or show a visible age plus manual refresh — silent staleness here is what produces the 409 you
then have to explain. Announce arrivals politely and never re-sort under the cursor: a "3 new items"
button the user presses beats a list that reshuffles itself.

**Persist the queue view in the URL** — filters, sort, status, assignee, page, selected item id. Two
reviewers cannot discuss "the third one down"; they can paste a URL. Across four independently built
products surveyed, queue and inbox views that persisted state to the query string were the rare
exception, and the rest lost the reviewer's place on every refresh `[observed]`. Mechanics and library
menu live in `frontend-dashboards` Step 3 — do not re-derive them.

## Worked example `[observed]`

A mature approvals queue in a regulated back-office console, anonymized. Its commit path is right end to
end: list + detail + decision in one route with a card fallback instead of a scrolling table; three
actions (approve, approve-with-edits where the edited payload is what ships, reject with a **mandatory**
reason); `lock_version` read on GET and echoed on the decision PUT, with 409 raised in **three distinct
flavours** — version diverged, already decided, request expired; on 409 the specific message plus an
**immediate reload** so banner and data agree, announced via `role="alert"` and `aria-live="assertive"`;
and a fail-closed role gate labelled *in its own source* as defence in depth rather than the barrier.

A second product, different team, reached the same guard as `{ target_state, expected_state, rationale }`
with commit disabled until the rationale is non-empty after trimming `[observed]` — two vocabularies, one
invariant. The counter-example, from a fourth codebase: six hand-rolled review and triage queues in **one**
application, confirm-gating on some and not others, **no** bulk action bar despite row selection existing,
**no** undo after commit, **no** queue state in the URL anywhere `[observed]`.

## Board (kanban) variant — practice, not canon

A column board is a *presentation* of a queue whose decision is "which state next", not a separate
surface: inherit everything above. Layout guidance here is industry practice, not canon — but the
accessibility requirement is **not** optional. WCAG 2.2 SC 2.5.7 Dragging Movements (Level AA) requires
that "all functionality that uses a dragging movement for operation can be achieved by a single pointer
without dragging", and names task-board columns directly, suggesting an "additional pop-up menu after
tapping or clicking on items for moving the selected element to another column"
`[verified: W3C WAI, Understanding SC 2.5.7]`. A drag-only board fails AA: ship the
move-to-column path plus an optimistic move that rolls back visibly.

## Workflow

1. **Inventory the decisions**, then **fix the queue contract** before any layout work.
2. **Compose list + detail + action bar**; build the evidence pane and history timeline before styling.
3. **Wire the commit path** — guard token, rationale, the three 409 flavours with reload, audit record.
   Do not defer: retrofitting a guard means re-testing every action.
4. **Add the HITL layer** if a model suggests, put queue state in the URL, pass the anti-fatigue checks.
5. **Verify with two sessions open at once** — the only way to test claim collisions and 409 handling —
   then at 360px and keyboard-only.

## Common pitfalls

- **The same item served to two people**, because claim is a boolean with no lease. **Silent reordering**
  of a live queue while the user is clicking is the same class of bug.
- **A generic "conflict" error**, or a 409 banner left sitting over stale data.
- **Confirm dialogs on everything**, producing the click-through reflex that defeats the one confirm that
  mattered — reversibility is the cheaper WCAG 3.3.4 path. And **client-side permission checks treated as
  the barrier**, with no server authority behind them.
- **Only accept and reject**, so reviewers guess; or **rationale required everywhere**, yielding a column
  full of "ok".
- **An AI suggestion pre-selected in the action bar**, and **override rate never measured**.
- **An audit trail recording the choice but not the evidence and policy version shown.**
- **A drag-only board** with no keyboard or menu move path — a WCAG 2.2 AA failure, not a nicety.

## Validation checklist

- [ ] Every action has a written actor, commitment, evidence set and reversibility class.
- [ ] Claim is a lease with a TTL and a visible holder; two sessions cannot both hold one item.
- [ ] Ordering default is declared on screen and the list never re-sorts under an open item; age shows
      against an SLA target with breach filterable; skip/defer/escalate/reassign exist or their absence
      was recorded.
- [ ] Evidence pane suffices to decide without leaving the surface and is snapshotted with the decision;
      the history timeline shows transitions, actors, timestamps and prior rationales.
- [ ] Every commit sends a guard token; the three 409 flavours have distinct copy and the item reloads;
      failed commits announce `assertive`, queue-count changes `polite`.
- [ ] Ceremony matches consequence per WCAG 3.3.4 — reversible, checked *or* confirmed, not all three;
      four-eyes enforced server-side where required, first approver's rationale visible; the audit record
      stores who, when, why, what was shown and the policy/model version.
- [ ] AI suggestion never pre-selected; override costs no more than accept; disagreement logged.
- [ ] Keyboard cycle covers next/prev/approve/reject/defer/rationale and focus returns to the next item;
      the empty queue is a distinct success state, separate from "no results for this filter".
- [ ] Filters, sort, assignee, page and selected id are all in the URL.
- [ ] If a board: every drag has a single-pointer alternative; optimistic moves roll back visibly.

## Reference files

- Read `references/queue-mechanics-and-board-variant.md` before building claim/lease, ordering, aging,
  bulk selection or a column board.
- Read `references/decision-commit-integrity.md` before wiring the commit path: guard-token flavours, the
  409 taxonomy, rationale enforcement, bulk-commit and undo semantics, the audit-record shape.
- Read `references/hitl-and-supervision.md` when a model suggests, scores or acts before the human.
- Read `references/audit-log-investigation.md` when the surface *investigates* instead of deciding.
- Read `references/worked-example-approval-queue.md` for the anonymized end-to-end example.

## Source Verification

Primary sources behind the inline `[verified: ...]` tags: `design-system.service.gov.uk/components/task-list/`;
`developer.android.com/develop/adaptive-apps/guides/canonical-layouts`; W3C WAI Understanding SC 3.3.4
and SC 2.5.7; MDN "409 Conflict" (citing RFC 9110 §status.409) and MDN `aria-live`; NIST CSRC Glossary
"separation of duty" (per NIST SP 800-192); NN/g Kaplan 2020-11-08 "8 Design Guidelines for Complex
Applications" and Kaplan 2021-08-15 "10 Usability Heuristics Applied to Complex Applications".
