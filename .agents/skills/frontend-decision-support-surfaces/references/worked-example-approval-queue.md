# Worked example: an approvals queue that gets the commit path right

An anonymized walkthrough of a mature approvals surface in a production regulated back-office console,
plus contrasting evidence from three other independently built products. All observations were read
directly from source on 2026-07-29 and are reported without naming products, teams or repositories.

Read this as a shape to adapt, not a specification. The specification is the main SKILL.md.

## 1. Route and layout

One route holds the whole job: **queue list + item detail + decision controls**. No modal-stacked
decision, no separate `/decide` page.

- **Wide viewports:** table list beside the detail pane.
- **Narrow viewports:** the list degrades to **cards**, not a horizontally scrolling table. This is the
  right call — a reviewer scrolling sideways to find the amount column is a reviewer who will mis-read
  it. (Compare the canonical narrowing rule: when a two-pane view narrows, keep the detail and hide the
  list; the reviewer's context is the item.)
- The list is a shared table component exposing an accessible label and an explicit "scrollable region"
  label for the horizontal-scroll case.

## 2. Actions: three, not two

| Action | Rationale required | Effect |
|---|---|---|
| Approve | no | The submitted payload takes effect |
| Approve with edits | yes | **The edited payload** is what takes effect |
| Reject | **yes** | Nothing takes effect; the reason is stored and displayed |

Decided items render **who decided, when, and the reason**, inline, in the same pane — so a reviewer
opening an already-decided item sees the answer and the reasoning rather than an empty action bar.

The middle action is the one most implementations omit. Without it, a reviewer who agrees with the intent
but not the detail must reject and ask for resubmission, which destroys the chain of custody for the
original request.

## 3. The guard round-trip

```text
GET  /items/{id}          -> { ..., lock_version: 7 }
PUT  /items/{id}/decide   <- { action, lock_version: 7, rationale?, payload? }

200  -> decided
409  -> { erro: <flavour>, mensagem: <ready-to-render text>,
          versao_atual?: 9, estado_atual?: "decided" }
```

Two details worth copying:

1. **`lock_version` is only sent when known.** The client does not invent a version; if it never read one,
   it omits the field and the server applies its own default policy. A fabricated guard is worse than an
   absent one.
2. **The server returns display-ready message text** alongside the machine-readable flavour code. This is
   a deliberate trade: it centralizes the wording of a legally-sensitive message rather than letting each
   client paraphrase it. Keep the flavour code too, so the client can still branch on behaviour.

### The three 409 flavours

| Flavour | Meaning | Extra field |
|---|---|---|
| version conflict | Someone changed the record since the GET | current version |
| already decided | A decision was already committed | current state |
| expired | The approval window closed | — |

The implementation's own source comments describe the guard as giving **"optimistic control plus
single-decision"** — that phrase is the requirement in five words: the record moved, or the decision has
already been made once and must not be made twice.

## 4. What the client does with a 409

In order:

1. Render the flavour-specific message in a banner that is `role="alert"` with `aria-live="assertive"`.
2. **Reload the item immediately**, so the evidence pane and history show real current state under that
   banner. The source annotates this explicitly: the item is reloaded right after the conflict message.
3. Recompute the legal actions from the reloaded state.

The reason this ordering matters: a conflict banner sitting over stale data is a screen that is now
*confidently wrong*, which is worse than the original failure. The reviewer's next action depends on
seeing the truth, not on being told there was a problem.

## 5. Authority handling

- The decision is gated on a confirmed elevated role for high-consequence item types.
- The gate is **fail-closed**: if the role cannot be confirmed, the action is disabled rather than
  optimistically enabled.
- The source labels this gate, in its own comments, as **"defence in depth, not the only barrier"** — the
  server is the authority; the UI merely avoids offering an action that would be refused.
- The role is resolved once per session at the shell level and reused, rather than re-fetched per screen.

That comment is the habit worth copying more than the code. A client-side check documented as the barrier
becomes, eventually, the only barrier.

## 6. Accessibility wiring actually present

- `role="status"` for informational banners (pending summary, success note).
- `role="alert"` for errors, with `aria-live="assertive"` on the conflict banner specifically.
- An accessible label on the queue table and a labelled scrollable region for horizontal overflow.
- Rejection reason rendered as text in the detail pane, not only as a tooltip.

## 7. Contrasting evidence from three other products

**Product B — same invariant, different vocabulary.** A moderation queue in a different product, built by
a different team, sends `{ target_state, expected_state, rationale }` and disables the commit control
until the rationale is non-empty **after trimming**, with a warning toast if a commit is attempted
without one. Different names, identical guard semantics. Two independent inventions of the same mechanism
is the strongest available argument that it belongs in shared guidance.

**Product C — the counter-example.** Six independently hand-rolled review/triage surfaces inside **one**
application. Measured across its admin surfaces: confirm-gating present on some and absent on others,
**zero** files referencing bulk actions despite row-selection state existing in eight, **zero**
referencing undo, and **zero** persisting queue state to the query string. Claim/assignee concepts appear
in six — so the teams each independently discovered that allocation matters, and each solved it
differently.

**Product D — the URL-state gap at scale.** In a large clinician-facing application, only a couple of
roughly a hundred and fifty screens read query parameters at all; the queue and inbox surfaces do not.
Every refresh loses the reviewer's place, and no view is shareable.

None of this is incompetence. It is the predictable outcome of the same surface being rebuilt by
different teams with no shared contract — which is exactly the gap this skill closes.

## 8. Adaptation checklist

- [ ] One route holds list + detail + decision; narrow viewports get cards, not sideways scroll.
- [ ] Three actions, with approve-with-edits authoritative over the original payload.
- [ ] Guard token read on GET, echoed on commit, omitted rather than fabricated when unknown.
- [ ] Three 409 flavours, each with its own copy and its own legal next actions.
- [ ] Conflict → assertive announcement **then immediate reload**, in that order.
- [ ] Authority gate fail-closed, documented as defence in depth, enforced server-side.
- [ ] Decided items show who, when and why, inline.
- [ ] Queue filters, sort and selected id in the URL.
