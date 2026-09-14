# Queue mechanics, and the board variant

Depth for Step 2 and the board section. Load before building claim/lease, ordering, aging, bulk
selection, or a column board.

## 1. The item state machine

Model the *allocation* state separately from the *domain* state. Conflating them is why queues end up
unable to express "claimed but not yet decided".

```text
allocation:  unclaimed -> claimed(actor, until) -> released | committed
domain:      pending -> approved | rejected | escalated | expired
```

Rules that fall out of keeping them separate:

- A release must not change domain state. "I put it back" is not "I rejected it".
- Expiry is a *domain* transition and can happen while an item is claimed. That is the third 409
  flavour, and it is invisible if expiry is modelled as an allocation concern.
- Escalation changes who may claim, not who currently holds it. Escalate then release, in that order,
  or the item is briefly unreachable by anyone.

## 2. Claim as a lease

| Concern | Rule |
|---|---|
| Grant | Server assigns `claimed_by` + `claimed_until`; client never invents the holder |
| Renew | Heartbeat while the tab is visible; stop on `visibilitychange` to hidden |
| Expire | Server-side; a stale lease is reclaimable by anyone without an admin step |
| Display | Show holder identity and remaining time, not a bare "locked" badge |
| Release | Explicit button, plus best-effort on navigate-away (`pagehide`, not `unload`) |

Two failure modes to design against:

- **Silent lease loss.** If the heartbeat fails, tell the user *before* they spend ten minutes writing
  a rationale that will 409. A visible "your hold expires in 2:00 — renew" beats a surprise conflict.
- **Reclaim races.** Two reviewers reclaiming the same expired lease is the original bug in a new
  costume. The grant must be a conditional server-side write, not a read-then-write.

Do **not** implement leases with client-side timers as the authority. The clock that matters is the
server's; the client's copy is a display convenience.

## 3. Ordering and aging

- **Declare the default in the UI**, e.g. "Sorted by risk, highest first". A queue whose order is a
  mystery gets worked top-down on faith.
- **Stable sort keys.** Ties broken by a monotonic id, never by anything mutable, or the list shuffles
  on every refetch even when nothing changed.
- **Freeze order while an item is open.** Buffer incoming changes and apply them when the detail pane
  closes, or on an explicit "3 new items" action.
- **Age needs a target.** Render `elapsed / target` as three states: within, approaching (configurable
  fraction of the target), breached. Make breach a filter value, not just a red row — the whole point
  is to work breaches first, which requires selecting them.
- **Do not sort by age when the ordering is priority.** Two competing orders on one list is how items
  at the bottom of a priority queue silently age past their SLA forever. If both matter, sort by
  priority and *surface* the breached ones as a separate pinned group.

## 4. Bulk selection and undo

Bulk is where queues become dangerous, so gate it on evidence sufficiency:

- **Row-sufficient decisions only.** If deciding requires opening the detail pane, the decision is not
  bulk-eligible. Say so — disable bulk for those action types rather than allowing it silently.
- **Selection survives nothing.** Clear the selection on filter change, sort change and page change.
  A selection that persists across a filter change will commit decisions on rows the user never saw.
- **Show the count in the action, not just the bar**: "Reject 14 items", never "Reject".
- **Partial failure is the normal case.** A bulk commit over 14 items will return successes and
  conflicts together. Report per-item outcomes and leave the failures selected so the user can retry
  exactly those. A single "some items failed" toast is unusable.
- **Undo, where it is real.** An undo window is only honest if the downstream effect is genuinely
  deferred (queued, not yet sent/published/charged). If the effect fires immediately, do not offer
  undo — offer a reversing action with its own audit entry, and label it as such. A fake undo is worse
  than no undo.
- **Rationale on bulk** applies once to the batch, and the audit trail must record it against *each*
  item, with a batch id linking them.

## 5. Multi-actor freshness

- Prefer **event-driven invalidation** (server emits "item X changed", client refetches that key) over
  pushing whole payloads or polling the whole list. The mechanics belong to
  `frontend-data-fetching-caching`; the queue-specific rule is that arrival of new work is *polite*
  news and loss of your claim is *assertive* news.
- Pause polling on a hidden tab, and on return show the age of what is on screen before refetching, so
  the user knows whether they are looking at old data.
- **Never optimistically remove an item from the list on commit** before the server confirms. On a 409
  the item must still be there, reloaded, showing why the commit failed.

## 6. The board (kanban) variant

A board is a queue grouped by domain state, with the transition expressed as a move. Everything above
still applies: claim, ordering within a column, aging, guard token on the transition.

**Sourcing honesty:** there is no canonical design-system specification for board layout — Material and
the GOV.UK Design System do not define one. Treat the layout choices below as industry practice
collected from working implementations, and do not present them to a stakeholder as standard.

Practice that recurs across working boards:

- **Optimistic move with visible rollback.** Move the card immediately, send the transition with the
  guard token, and on failure animate it back to its origin column *and* surface the reason. A silent
  snap-back teaches users that the board is flaky.
- **Per-transition confirm policy, not per-board.** Most moves need no dialog; the one or two that are
  irreversible (publish, pay, close-won) do. A board that confirms every drag is unusable; one that
  confirms none is unsafe.
- **Column limits are a signal, not an enforcement**, unless the domain actually forbids the state.
- **Aggregates in the column header** (count, and weighted total where the domain has a value) are the
  one dashboard-like element that earns its place here, because they answer "is this column healthy?"
  without leaving the surface.
- **Virtualization and drag do not compose well.** A long column that virtualizes will drop the drag
  source when it scrolls out of range. Either cap column length with paging, or accept the DOM cost.

### Accessibility is not optional here

WCAG 2.2 SC 2.5.7 Dragging Movements (Level AA): "All functionality that uses a dragging movement for
operation can be achieved by a single pointer without dragging, unless dragging is essential or the
functionality is determined by the user agent and not modified by the author." The Understanding
document names this exact widget class, suggesting an "additional pop-up menu after tapping or clicking
on items for moving the selected element to another column", and for reordering "adjacent controls for
moving the element up or down in the list by simply tapping"
`[verified: w3.org/WAI/WCAG22/Understanding/dragging-movements.html, 2026-07-29]`.

So the minimum viable board ships **two** move paths:

1. Pointer drag (the affordance everyone builds).
2. A per-card "Move to…" menu listing the legal target columns — which doubles as the keyboard path and
   the touch path, and is usually less code than a keyboard drag emulation.

Additional a11y requirements for either path:

- Announce the result politely: "Moved *Item* to *Column*, position 3 of 9."
- Keep the card's accessible name stable across the move; a name derived from position changes under
  the user.
- Ensure focus lands on the moved card in its new column, not on `<body>`.
- Legal targets only: a menu that offers an illegal transition and then 409s is worse than a disabled
  entry with a reason.

**Do not** rely on a drag library's built-in keyboard sensor as your conformance story without testing
it: sensors vary in whether they announce, whether they respect reduced motion, and whether they work
inside a scroll container.
