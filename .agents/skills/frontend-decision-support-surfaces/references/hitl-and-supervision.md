# Human-in-the-loop and supervision

Depth for Step 5. Load when a model suggests, scores, or acts before the human — or when a human must
take control of something a model is already running.

Boundary: the *rendering* of confidence, explanation, model cards and contestability affordances belongs
to `ai-trust-transparency-ux`. This file covers how the suggestion changes the **queue and the commit
path**.

## 1. Response modes

Two modes (on/off) is not enough for any real deployment, because trust is not uniform across item types.
Three modes, settable per item class or per conversation:

| Mode | Model does | Human does | Audit implication |
|---|---|---|---|
| **auto** | acts and commits | audits *after the fact*, samples | Every auto action needs a review queue of its own |
| **assist** | proposes with a score | reviews and commits | The default for consequential decisions |
| **manual** | nothing, or is hidden | decides unaided | The control case; keep it reachable |

One production system ships exactly this `auto | assist | manual` selector, scoped per conversation and
switchable by an operator mid-flight `[observed]`. The value is that "how much do we trust the model
here?" becomes a runtime setting an operator owns, rather than a deploy an engineer owns.

Design consequences:

- **auto is not "no human".** It is "human later, on a sample". If you ship auto without building the
  post-hoc audit queue, you have shipped unsupervised automation with a UI that implies otherwise.
- **Mode changes are auditable events** with an actor and a reason. A queue that silently flipped to auto
  is the incident nobody can reconstruct.
- **Show the current mode in the action bar**, not in a settings page. The reviewer must know whether
  their inaction means "nothing happens" or "the model proceeds".

## 2. Where the suggestion goes on screen

- **Beside the action bar, never inside it.** The suggestion is evidence, not a pre-filled answer. A
  pre-selected radio or a pre-focused "Approve" button converts a review into a confirmation.
- **The score is an input, not a verdict.** If the product wants a threshold-driven shortcut, make it an
  explicit *filter* on the queue ("show me only low-confidence items"), not a nudge on the button.
- **Show the model's stated reasons next to the human's rationale field**, so the reviewer can disagree
  with a specific reason rather than the whole suggestion.
- **Never hide the evidence because the model was confident.** High confidence is exactly when
  automation bias does the damage.

## 3. Override economics

The rule: **overriding must cost no more clicks than accepting.**

| Path | Acceptable | Not acceptable |
|---|---|---|
| Accept suggestion | 1 action | — |
| Override | 1 action + rationale field already on screen | modal → dropdown → reason → confirm |

If overriding is more expensive, measured override rates will fall and you will read that as the model
improving. It is not; it is the interface taxing dissent.

Corollaries:

- **Rationale on override is right; extra ceremony is not.** Keep the field inline and pre-focused when
  the reviewer picks a different action.
- **Do not require the reviewer to categorize their disagreement** before they can commit. Offer the
  taxonomy as optional structured metadata beside the free text; a mandatory dropdown of override
  reasons produces whichever option is first in the list.
- **Never gate override behind an escalation.** If the human needs permission to disagree with the
  model, the model is the decider and the human is decoration.

## 4. Disagreement tracking

The single most useful signal this surface can emit. Record on every item: `suggested_action`,
`suggestion_score`, `committed_action`, `actor`, `model_version`, `policy_version`.

Derived measures worth surfacing to whoever owns the model:

- **Override rate by model version** — the regression detector.
- **Override rate by category** — where the model is weakest, which is where the humans should be routed.
- **Override rate by reviewer** — read carefully. A reviewer at ~0% may be rubber-stamping, or may be
  handling only easy items; compare against their item mix before concluding anything.
- **Agreement at high confidence vs low confidence.** If they are the same, the score carries no
  information and should not be displayed as if it did.

Interpretation guardrails:

- **Near-zero override is a red flag, not a win.** It usually means the humans stopped looking.
- **Near-total override means the model should not be suggesting** at all for that category; suppress
  the suggestion rather than training reviewers to ignore it.
- These are directional readings. Resist publishing a numeric "healthy override rate" target — there is
  no primary source for one, and a target immediately becomes something the interface is tuned to hit.

## 5. Supervision console: takeover and release

For systems where an agent is *already running* something (a conversation, a workflow, a batch), the
supervision surface is a queue whose items are live processes.

Required mechanics:

- **Takeover is a claim** — same lease semantics as any other item (§2 of the queue-mechanics reference):
  server-granted, TTL'd, visible holder, reclaimable.
- **Takeover must stop the agent, verifiably.** Show the agent's status as suspended, and handle the race
  where an in-flight agent action lands *after* the takeover: it must be rejected by the same guard
  token, not merged.
- **Release requires a reason.** One production console captures a free-text reason on release
  `[observed]`; without it the audit trail records that control moved and loses why, which is the only
  part a later reviewer needs.
- **Release must state what the human changed**, so the agent (or the next human) resumes from a known
  state rather than re-deriving it.
- **Approve/reject of individual agent instructions** is a nested decision surface: same rationale,
  guard and audit rules as any other commit. Do not treat "approve this tool call" as lighter-weight
  because it is small — it is often the most consequential action on the screen.

Failure modes seen in practice:

- **Takeover without suspend**: human and agent both acting, interleaved, with no guard.
- **Release without reason**: an audit trail of handoffs with no causes.
- **No visible agent state**, so the supervisor cannot tell whether their takeover actually took effect.
- **Supervision surfaced only in a log**, so intervention requires reading a stream rather than acting
  on an item — which is the exact monitoring-vs-executing confusion this skill exists to correct.
