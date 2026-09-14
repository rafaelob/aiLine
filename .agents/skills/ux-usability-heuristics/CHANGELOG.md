# Changelog: ux-usability-heuristics

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.2.8] - 2026-09-12
### Changed
- The unconfirmed "ISO/IEC 40500:2025" identifier left the WCAG line; WCAG 2.2 AA is cited from the W3C page alone.
- 2026-09-10: Removed the ux-copy-patterns pairing from the routing description; that skill is not in the catalog. Version bump recorded in SKILL.md.
- 2026-09-05: Shortened the frontmatter routing description to make ux-usability-heuristics's task boundary and sibling routing explicit; version bump recorded in SKILL.md.
- Qualified research sample sizes as planning heuristics and separated web WCAG target size from
  Android and iOS platform guidance.

## [1.2.4] - 2026-08-06
### Changed
- Removed the standalone `- Last verified: 2026-07-28.` bullet from `## Dependency
  Currency` (bare-date sweep, Wave 4B). It carried no fact of its own; the source
  links and the `SYSTEM_DESIGN.md` recording instruction it sat under stayed.

## [1.2.3] - 2026-08-06
### Fixed
- The `## Freshness` journal's spatial-computing pointer named a sibling skill, `mobile-spatial-computing`, that does not exist anywhere in this catalog (confirmed: no such directory under `skills/`). It was hiding a real routing instruction that never made it into the body. Promoted into Step 7 (Mobile UX patterns), corrected to point at the skill that actually exists and actually matches (`webxr-immersive`, WebXR session/controller integration), with an honest note that native visionOS/RealityKit UX has no dedicated skill here yet -- rather than re-publishing the same broken name. Note for the catalog owner: `webxr-immersive`'s own description independently makes the identical broken reference ("native visionOS/RealityKit (mobile-spatial-computing)") -- out of scope here since that file is outside this pass's assigned skill list, flagging for a separate fix.

### Changed
- Moved the rest of `## Freshness` out of `SKILL.md`'s body (provenance-out-of-body pass, per `AGENTS.md` §"O que vai dentro de um SKILL.md"), collapsed the surviving verify-instructions-plus-sources into `## Dependency Currency`. The AI/conversational-UX and WCAG bullets restated content already in body Step 8 / Step 5 without adding an instruction, so only their source links were kept. Backfilled the procedural history here, dates preserved:
  - **2026-07-28 -- description trim.** Token-budget audit: 530 -> 338 chars; triggers and negative routing preserved, illustrative detail already in the body cut.
  - **2026-07-28 -- validation gap closed.** Added the explicit `## Validation` checklist (the skill had a scoring method and a Deliverables list but no falsifiable "did I actually check this" gate). Fixed the `references/UX_HEURISTICS_GUIDE.md` citation to carry a load trigger (was a bare link). Removed empty, never-referenced `assets/`, `scripts/`, and `references/.gitkeep`. No change to the heuristics content itself.

## [1.2.2] - 2026-07-31
### Fixed
- Description: virgula duplicada removida na lista de anti-triggers (rodada 2, 2026-07-31).
