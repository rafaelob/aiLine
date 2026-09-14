# The investigation variant: audit and event log surfaces

Load when the surface's job is to **reconstruct what happened** rather than to commit a decision. It is
the fourth family from Step 1, and it inverts several of this skill's defaults.

## 1. What inverts

| Default elsewhere | Here |
|---|---|
| Claim/lease an item | No claim — reading is not exclusive |
| Confirm before acting | No confirm; there is usually nothing to commit |
| Required rationale | None, unless the investigation ends in an action |
| Queue ordering by priority | Ordering by **time**, always, and usually descending |
| Evidence pane per item | Evidence *is* the list; the detail is the record's full shape |

The design goal changes too: not throughput, but **answering a question about the past without being able
to reproduce it**. The investigator cannot re-run the event; the log is all there is.

## 2. The query surface

Investigations are driven by four filter axes. Build all four or the surface will not answer real
questions:

1. **Time range** — absolute *and* relative ("last 15 minutes"). Store the resolved absolute range in the
   URL, not the relative expression, or a shared link means something different tomorrow.
2. **Actor** — who did it, including service/automated actors. An audit log that cannot filter to "actions
   by the integration user" cannot answer the most common security question.
3. **Entity** — which record, and its type. Support "everything touching entity X" across event types.
4. **Event type / outcome** — including failures. A log that only records successes cannot answer "did
   someone try?", which is usually the question.

Query-surface rules:

- **Every axis in the URL.** Investigations are collaborative by nature; the artifact of an investigation
  is a link plus a sentence.
- **Show the resolved query in words** above the results: "142 events, 2026-07-20 09:00–09:15 UTC, actor
  any, entity order/8831". Investigators mis-set filters constantly; echoing the query catches it.
- **Empty results need the query restated**, plus the widened-search offer. "No events" without the query
  is indistinguishable from a broken screen — and here the two-empties rule matters even more than on a
  dashboard, because "nothing happened" is a *finding*.
- **Timezone must be explicit and switchable** (UTC vs local), and stated on every timestamp. Cross-region
  incident reconstruction fails silently on implied local time.

## 3. Correlation

The single highest-value feature, and the most commonly missing:

- **Carry a correlation id** end to end and make it a first-class filter. One click from any event to
  "all events in this request/trace/session".
- **Group by correlation in the list** with an expand affordance, so a request that produced 30 events
  reads as one line, not 30.
- **Link out to the trace** where the system has distributed tracing, rather than reimplementing a
  waterfall view. The seam with `observability-core` is: it owns traces and spans; this surface owns the
  business-event log a non-engineer can read.
- **Causation vs correlation.** If the event model records a `caused_by` edge, render it as a tree. If it
  does not, do not imply causality by adjacency — chronological proximity is not cause, and an
  investigation UI that suggests otherwise produces wrong conclusions with confidence.

## 4. Rendering a change

A change event needs to show **before, after, and who**:

- **Field-level diff**, not a JSON blob. Highlight changed keys; collapse unchanged ones by default.
- **Redact by policy, and say that you did.** A hidden field must render as "redacted" with the reason,
  never as blank or absent — an investigator who cannot tell "empty" from "hidden from you" will draw the
  wrong conclusion. That distinction is the whole point.
- **Show the schema/policy version** alongside, so a field that no longer exists is explicable.
- **Never pretty-print away the original.** Offer a raw view for the record actually stored; the
  human-readable rendering is an interpretation.

## 5. Volume

Audit logs are the largest data set on this list of surfaces:

- **Server-side pagination, always.** Cursor-based, not offset — an offset page 40 over an append-heavy
  log returns overlapping and skipped rows.
- **Cap the default range** rather than defaulting to "all time", and say what the cap is.
- **Virtualize the list**, and keep DOM order equal to visual order for screen readers.
- **Honest export.** Label whether the file is the visible page, the current query, or everything — and
  refuse silently-truncated exports. An investigator reconciling an export against the UI and finding
  different row counts loses trust in both.
- **Export is itself an auditable event.** Exporting an audit log is a data-egress action; log it.

## 6. When the investigation ends in an action

The moment the surface offers "revoke this session", "reverse this transaction" or "suspend this actor",
it stops being an investigation surface for that action and inherits the full commit path from
`references/decision-commit-integrity.md`: guard token, required rationale, audit record, and a
correlation back to the investigation that motivated it. Record **which query the investigator was looking
at** when they acted — that link is the difference between a defensible intervention and an unexplained
one.
