# Decision commit integrity

Depth for Step 4. Load before wiring the commit path: guard tokens, the 409 taxonomy, rationale
enforcement, bulk commits, undo, and the audit record.

## 1. The commit request shape

Every decision commit carries four things. Missing any one of them is a defect, not a simplification.

```text
POST/PUT  /items/{id}/decide
{
  action:        "approve" | "approve_with_edits" | "reject" | "escalate",
  guard:         <version token> | <expected state>,
  rationale:     string | null,          // required per policy, see §3
  payload:       {...} | null            // only for approve_with_edits
}
```

- **`action` is a verb the domain recognizes**, not a target state. "approve" and "set state to
  approved" look equivalent until a second effect (notification, ledger entry) hangs off the verb.
- **`guard` is mandatory on every mutating call**, including bulk and including escalate.
- **`payload` on approve-with-edits is what ships.** If the edited payload is not what takes effect, the
  action is a lie; either make it authoritative or remove the action.

## 2. Guard tokens: two flavours, one invariant

| Flavour | Shape | Best when |
|---|---|---|
| **Version token** | `lock_version: 7`, read on GET, echoed on commit | Record has many mutable fields; any change should invalidate the decision |
| **Expected-state token** | `expected_state: "pending"` | The guard is really "has anyone decided yet?"; state machine has few states |

Both were arrived at independently in production codebases `[observed]`. Pick one per resource and be
consistent — a surface where some actions guard by version and others by state is a surface where
somebody will forget the guard entirely.

**The invariant, restated:** the client asserts what it believed; the server refuses if reality moved.
This is not a nicety. Without it, two reviewers who opened the same item both succeed, and the second
decision silently overwrites the first — with the first reviewer's name still in the audit trail as the
decider of a state that no longer exists.

**Anti-pattern: guarding with `updated_at`.** Timestamp resolution and clock skew make it unreliable,
and it changes on writes that are irrelevant to the decision. Use a monotonic version or the state.

**Also insufficient:** disabling the button when the client *thinks* the item was decided. The client's
belief is what is stale. The guard exists precisely because the UI cannot know.

## 3. Rationale policy

Write the policy as a table, per action, and implement it from that table rather than ad hoc per screen:

| Action | Rationale | Why |
|---|---|---|
| Approve (matches recommendation) | optional | Requiring it produces "ok" rows |
| Approve (overrides recommendation) | **required** | The override *is* the information |
| Approve with edits | **required** | Explain what changed and why |
| Reject | **required** | The subject will ask |
| Escalate | **required** | The next actor needs the handoff reason |
| Defer / skip | optional | Cheap, reversible, high frequency |

Enforcement rules:

- **Trim before validating.** A field containing three spaces is empty.
- **Disable the commit control** while invalid, and pair it with a message saying what is missing —
  a disabled button with no explanation reads as a broken screen.
- **Validate server-side too.** The client check is convenience; the policy lives on the server.
- **Do not impose a minimum character count.** It produces "asdfgh" instead of "ok" and teaches
  reviewers that the field is an obstacle rather than a record.
- **Persist the draft rationale locally** keyed by item id. Losing a paragraph of reasoning to a
  navigation is the single most enraging bug on this surface.

## 4. The 409 taxonomy

At minimum three distinct outcomes, each with its own copy and its own next action:

| Flavour | Meaning | Reviewer's next step |
|---|---|---|
| `version_conflict` | Someone changed the record since you loaded it | Re-read the (reloaded) evidence, decide again |
| `already_decided` | A decision was already committed | Read who decided and what; nothing to do |
| `expired` | The window for this decision closed | Escalate or request a new submission |

Response body should carry enough to render the right sentence *and* the truth: the flavour code, a
human-readable message, and the current version/state. RFC 9110 defines 409 as indicating "a request
conflict with the current state of the target resource"
`[verified: MDN, HTTP 409 Conflict, citing RFC 9110 §status.409, 2026-07-29]`; the flavour code is your
own contract layered on top, so document it.

Client handling, in order:

1. Do **not** clear the form. The reviewer may still need their rationale text.
2. **Refetch the item** and re-render the evidence pane and history from the new state.
3. Render the flavour-specific message in an alert region with `aria-live="assertive"` — the case MDN
   reserves for updates that "should be presented to the user immediately", under the warning not to use
   assertive "unless the interruption is imperative"
   `[verified: MDN, aria-live, 2026-07-29]`.
4. Recompute which actions are still legal. After `already_decided`, the action bar should offer nothing
   but navigation.

**Distinguish 409 from 403 and 412.** A 403 means *you* may not do this (authority); 409 means *nobody*
can do this right now (state). If your API returns 409 for an authority failure, reviewers get told to
retry something that will never succeed.

## 5. Four-eyes / separation of duty

NIST's separation-of-duty definition is the plain-language version: "the person authorizing a paycheck
should not also be the one who can prepare them"
`[verified: NIST CSRC Glossary, separation of duty, sourced to NIST SP 800-192, 2026-07-29]`.

Implementation notes:

- The rule lives **server-side**. The UI's job is to (a) not offer an action that will be refused, and
  (b) explain why it is unavailable.
- **Show the first approval inline**: who, when, and their rationale. A second approver deciding without
  seeing the first one's reasoning is two independent decisions, not four eyes.
- **Two approvals of the same *action***, not just two touches of the record. Approving after someone
  else escalated is not a second approval.
- **Delegation breaks it.** If actor A can act as actor B, the server must compare effective identities,
  not session identities.
- Treat client-side authority checks as **defence in depth**. One production implementation labels its
  role gate in its own source comments as exactly that, and fails closed when the role cannot be
  confirmed `[observed]` — copy both halves of that habit.

## 6. The audit record

Store what makes the decision defensible later, not what is convenient now:

```text
{
  item_id, decision_id,
  actor_id, actor_role_at_decision,     // roles change; snapshot it
  action, rationale,
  committed_at,
  guard_value_sent,                     // what the reviewer believed
  evidence_snapshot_ref,                // or a content hash of what was rendered
  policy_version | model_version,       // what rules/suggestions applied
  suggested_action, suggestion_score,    // for disagreement analysis
  batch_id | null                        // bulk provenance
}
```

- **`actor_role_at_decision` is not derivable later.** Roles get revoked; the audit must say what
  authority existed at the moment.
- **`evidence_snapshot_ref` is the difference between an audit trail and a guess.** Re-deriving the
  evidence from live data six months later shows the reviewer something they never saw.
- **Never mutate an audit row.** A reversal is a new row referencing the old one.
- **Surface the trail in the UI**, not only in a log store. If reviewers cannot see the history, they
  cannot notice that the same item has been through the queue four times.
