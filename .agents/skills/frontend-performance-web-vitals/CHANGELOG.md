# Changelog — frontend-performance-web-vitals

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.7] - 2026-09-11
### Changed
- Tightened activation routing around the skill's produced artifact and removed redundant handoff wording.
- Rewrote the description trigger-first. It fires when Lighthouse, PageSpeed or CrUX shows LCP, INP or CLS out of budget, a page is slow to load or freezes after a click (PT "site lento", "a página trava ao clicar", "nota do Lighthouse caiu"), content jumps while it loads, or a JS bundle grows. The generic "page-speed regression" trigger is gone; a slowdown outside the browser routes to `diagnosing-bugs`.

## [1.0.6] - 2026-08-06
### Changed
- Removed the bare `- Last verified: 2026-06-29` line from `## Official sources` — pure audit-trail, not an instruction (per `AGENTS.md` §"O que vai dentro de um SKILL.md"). The dated source links beneath it are unchanged.

## [1.0.5] - 2026-08-06
### Changed
- Renamed the trailing `## Freshness` section to `## Official sources` (per `AGENTS.md` §"O que vai dentro de um SKILL.md") — the dated URL list under it backs specific claims made throughout the Execution playbook (several already cited inline via "Source: ..."), so it is a live fact catalog, not provenance. Moved out the one line that was pure provenance:
  - **2026-07-28** — renamed "Common pitfalls" to "Common Pitfalls / Gotchas" so the linter's checklist/gotcha heading pattern matched; gave both `references/` entries an explicit load-trigger and removed a doubled self-citation on `web-vitals-audit-checklist.md`; deleted the stray `references/.gitkeep` since the folder held two real files and no longer needed a placeholder. No procedural or metric content changed.

## [1.0.4] - 2026-07-28
### Changed
- Tightened description to <=400 chars (token-budget audit 2026-07-28); preserved negative routing to frontend-data-fetching-caching/frontend-web-platform-apis/frontend-responsive-design
