# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints

All 20 sprints (S0-S19) + agents package COMPLETED. 3,087 tests (1,875 runtime + 250 agents + 962 frontend), 35+ E2E Playwright specs, 65 live API tests.

---

Sprints 15-18: Excellence sweep, Hackathon Victory, Final Push, Impact Polish — see FEATURES.md for details (F-121 through F-140).

## Sprint 19 — State-of-the-Art Final Sweep (Feb 15) — COMPLETED

- [x] Fix all documentation numbers (140 features, 3,087 tests, 20 sprints) across 6 files
- [x] Add Sprint 18 section to feature-map.md (F-136–F-140)
- [x] Refactor `_plan_nodes.py` (764→15 LOC barrel + 5 focused modules) (F-142)
- [x] Refactor `plan-generation-flow.tsx` (757→379 LOC + wizard-steps + plan-result-display) (F-143)
- [x] Extract shared motion variants to `lib/motion-variants.ts` — deduplicated 9 components (F-144)
- [x] Fix `as never` type casts in SSE hooks with proper `StudyPlan`/`ScorecardData`/`QualityReport` (F-145)
- [x] Command Palette (Cmd+K) — fuzzy search, navigation, themes, languages, ARIA combobox (F-141)
- [x] Full verification: 0 TS/ESLint/ruff/mypy errors, 3,087 tests, build clean

---

## Post-Hackathon
- [ ] Postgres RLS, Redis rate limiter, disable OpenAPI in prod, SW multi-locale caching
