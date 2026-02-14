# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints

All 15 sprints (S0-S14) + agents package COMPLETED. 1,993+ backend tests (1,743 runtime + 250 agents), 770+ frontend tests (90 suites), 35+ E2E Playwright specs, 65 live API tests.

---

## Sprint 15 — Excellence Sweep (Feb 14) — IN PROGRESS

- [x] Fix 114 mypy errors, add wall_time_iso to RouteMetrics, persist quality_decision
- [x] Polish README, judge-packet, a11y themes
- [x] Fix all CRITICAL audit findings (state leak, tool bridge, server components, nested main)
- [x] Fix all HIGH audit findings (Link, model IDs, cognitive curtain, reducedMotion)
- [x] Fix all lint errors (ruff F401, I001, UP017, E501; ESLint 0 errors)
- [x] Docker Compose verification
- [ ] Demo video (3 min)

---

## Post-Hackathon

- [ ] Postgres RLS, Redis rate limiter, disable OpenAPI in prod
- [ ] Squash migrations, IdempotencyGuard TTL, QualityGate SmartRouter
- [ ] Service worker multi-locale caching
