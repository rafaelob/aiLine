# Changelog: frontend-decision-support-surfaces

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.3] - 2026-09-12
### Changed
- Verification dates left the inline `[verified: ...]` tags and the source list (2026-07-29 for all of them; the sources themselves stay named).
- Tightened activation routing around the skill's produced artifact and removed redundant handoff wording.

## [1.0.2] - 2026-08-06
### Changed
- Moved procedência out of the `## Freshness` section (body-cleanup pass, per
  `AGENTS.md` §"O que vai dentro de um SKILL.md"); renamed the remaining live-fact
  bibliography to `## Source Verification` since it backs the inline `[verified: ...]`
  citations already spread through the body. Backfilled here as it was not previously
  logged:
  - **Created 2026-07-29.** No library versions were pinned in the body on purpose:
    this surface composes list-detail, URL-state and table primitives whose version
    menus already live in `frontend-screen-archetypes` and `frontend-dashboards`, and
    duplicating them would create a second place to go stale. (The routing itself is
    still in the body's Scope table; only this rationale moved.)
  - **Sourcing-contract cuts (2026-07-29):** no canonical citation exists for
    kanban/board *layout* — the board is labelled practice and only its accessibility
    requirement (WCAG 2.2 SC 2.5.7) is sourced. Numeric thresholds for reviewer fatigue
    and batch sizes were cut for the same reason. RFC 9110's body text could not be
    retrieved unpaginated, so the 409 status is cited via MDN naming the RFC section
    rather than quoted directly from the RFC.
  - **`[observed]` provenance (2026-07-29):** evidence tagged `[observed]` in the body
    (both guard-token flavours, the three-flavour 409 taxonomy, the
    `auto | assist | manual` triad, takeover/release-with-reason, and the
    counter-example queue lacking bulk actions/undo/URL state) was confirmed directly
    in four independently built production codebases, reported anonymized.

## [1.0.1] - 2026-07-31
### Changed
- Description reescrita para roteamento: triggers e anti-triggers explicitos (rodada 2, 2026-07-31).
