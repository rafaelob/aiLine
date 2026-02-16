# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints

All 22 sprints (S0-S21) + agents package COMPLETED. 3,217+ tests (1,876 runtime + 287 agents + 1,054 frontend), 35+ E2E Playwright specs, 65 live API tests.

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

## Sprint 20 — Maturity & Polish (Feb 15) — COMPLETED

- [x] Public landing page with hero, features, stats, footer (F-146)
- [x] Route group `(app)` — split layout: landing vs authenticated shell (F-147)
- [x] Fix all 327 ESLint warnings → 0 warnings (F-148)
- [x] Dashboard refactor: extract icons, AnimatedCounter, PlanHistoryCard (541→362 LOC) (F-149)
- [x] Shared AnimatedCounter component deduplicating dashboard + landing logic (F-150)
- [x] Landing page a11y audit + fixes: focus rings, aria-live counters, Link components (F-151)
- [x] Landing page UX polish: gradient text, scroll animations, hover effects (F-152)
- [x] 86 new tests for landing, shared, dashboard-extracted components (F-153)
- [x] Security review: 0 critical/high findings (F-154)
- [x] File cleanup: .gitignore updates, screenshot removal, nul artifact deleted (F-155)
- [x] Full verification: 0 TS/ESLint/ruff/mypy errors, 3,173 tests, build clean

## Sprint 21 — Skills Runtime System (Feb 15-16) — COMPLETED

- [x] Skills Spec Validator — agentskills.io-compliant validation (slug, metadata string-only, token limits) (F-167)
- [x] Accessibility Skill Policy — 7 profiles mapped to 17 skills with must/should/nice tiers (F-168)
- [x] Skill Prompt Composer — token-budgeted composition with priority sort + proportional truncation (F-169)
- [x] SkillCrafter Agent — multi-turn conversational skill creation for teachers (F-170)
- [x] Dynamic Skill Loading — SkillRequestContext in AgentDeps for per-request skill selection (F-171)
- [x] Skills Runtime State — RunState/TutorGraphState extended with skill fields (F-172)
- [x] All 17 Skills Spec-Compliant — metadata string-only, synced skills/ and .claude/skills/ (F-173)
- [x] Docker CORS Localhost — both localhost and 127.0.0.1 for all dev ports (F-174)
- [x] Verification: 1,876 runtime + 287 agents pass, 0 ruff/mypy errors, Docker 4 services healthy

## Sprint 22 — Security Hardening & Expert Review (Feb 16) — COMPLETED

- [x] Fix CRITICAL cross-tenant IDOR in plan review POST/GET endpoints (F-179)
- [x] Remove misleading teacher_id from MaterialIn/TutorCreateIn schemas (F-180)
- [x] Scorecard node: emit STAGE_FAILED + structured fallback instead of silent None (F-181)
- [x] SSE stream_writer: handle QueueFull gracefully (F-182)
- [x] CORS: add PUT/PATCH/DELETE/OPTIONS methods (F-183)
- [x] Skills registry: functools.lru_cache for thread safety (F-184)
- [x] Settings singleton: double-checked locking (F-185)
- [x] CircuitBreaker test timing fix for Windows (F-186)
- [x] Skills Discovery API with 4 endpoints (F-187)
- [x] AI Receipt SSE event for trust transparency (F-188)
- [x] Streaming Thought UI component (F-189)
- [x] Confetti celebration hook (F-190)
- [x] Expert review: GPT-5.2 (architecture/backend) + Gemini-3-Pro (frontend/UX)
- [x] Verification: 1,915 runtime + 287 agents + 1,064 frontend = 3,266 tests, 0 lint/type errors

---

## Post-Hackathon
- [ ] Postgres RLS, Redis rate limiter, disable OpenAPI in prod, SW multi-locale caching
- [ ] Skills DB Persistence — SQLAlchemy models + pgvector embeddings (F-175)
- [ ] Skills API Endpoints — CRUD, fork, rate, suggest, craft under /v1/skills (F-176)
- [ ] Skills Workflow Integration — skills_node in plan_workflow + tutor_workflow (F-177)
- [ ] Teacher Skill Sets — per-teacher presets (F-178)
