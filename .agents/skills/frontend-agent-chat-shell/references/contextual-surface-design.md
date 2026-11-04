# Adapt a shell to its work

This is project-level application guidance, not another resident design skill or a deploy
manifest. Use the project's existing components, tokens, routes and design record. The
generic `frontend-design` capability owns art direction; this file owns shell-specific choices.

## Three valid compositions

| Project task | Composition worth testing | Trade-off and fallback |
|---|---|---|
| Read and ask about a long answer | Reading-first thread; quiet session navigation; bounded prose | Do not squeeze text beside an unused panel. Open an occasional artifact inline or on a route. |
| Compare a generated artifact while revising it | Thread plus an independently useful work surface | Two readable minimum widths determine the split, not a universal breakpoint. At narrow widths use a named view/route with a way back. |
| Supervise several long-running tasks | Compact session/task list with explicit status and a selected detail | Do not turn every task into a large promotional card. Separate needs-input from activity without relying on color alone. |

These can share a brand without sharing a density. A conversational greeting does not
determine the styling of an error, approval request or results table. Name the actual user
task before choosing rail width, type scale or artifact placement. An existing sidebar order
may be correct; historical competitor screenshots are not permission to reorganize it.

## Bind visual choices to real state

- Map status tokens to **server-confirmed** states, not just attractive swatches. Give
  interrupted/blocked work text and recovery; avoid the same green treatment for completed,
  partial and merely disconnected. A local preview proves only the rendering.
- Keep composer focus, editable draft and attachment status independent of a view switch.
  Distinguish unsent, uploading, rejected and ready attachments before send. IME composition
  and rapid repeat actions still follow the existing composer contract.
- Stop/Cancel remains in a predictable position, but the visual control is not evidence that
  server work stopped. Wire and observe the responsible backend path separately.
- Reserve hierarchy for the work: a session title, a current task and the next action. Model
  metadata is visible when it affects the choice; decorative slogans must not compete with
  a blocked task. Preserve labels, constraints and safety/consent text.
- Side-by-side artifact views are **not modal**. A genuine modal uses modal focus behavior;
  an ordinary panel must not trap focus. On Close/Escape return focus coherently. Test
  reopen, browser Back/Forward and newer navigation so an old view cannot reappear.
- At narrow widths, keep navigation and Stop reachable without covering the composer. Test
  long titles, mobile viewport height and the on-screen keyboard in the actual target device
  when relevant. Desktop viewport emulation does not prove virtual-keyboard behavior.

## Project record and test slice

Use `assets/surface-contract.template.md` only when the existing record has no place for
these decisions. Choose the affected rows: empty, history-loading, ready, running,
needs-input, interrupted, error, and permissions. Each needs an owner, rendered content,
available action and announcement strategy. Do not live-announce every streaming token.

Validate the changed surface with real content shape, keyboard, focus restoration and its
narrow fallback. Reuse the existing browser runner. Label fixtures and unverified backend
behavior. A screenshot, static mockup or state reducer cannot establish end-to-end resume.

Guidance sources (consulted 2026-10-30): [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[WAI modal-dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/),
[responsive layout](https://web.dev/articles/responsive-web-design-basics).
Original application guidance; no vendor assets or screenshots included.
