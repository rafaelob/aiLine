# Sprint 26 — Mega Review: Critical Fixes, Polish & Feature Completion

**Date:** 2026-02-19
**Goal:** Fix ALL critical/high issues found in exhaustive codebase review, complete Sprint 25 Phase 2 features, and polish for hackathon readiness.
**Status:** PLANNED

---

## Audit Findings Summary

### Test Results (Docker Compose)
- **Backend:** 2,403 passed, 3 skipped, 0 failures
- **Frontend:** 1,166 passed / 1,176 total (2 failures + 1 worker OOM)
- **TypeScript:** 2 errors (landing-page.tsx, learning-trajectory.tsx)
- **`uv run pytest` broken in Docker** — must use `python -m pytest`

### Critical Issues Found

| ID | Severity | Area | Description |
|----|----------|------|-------------|
| C1 | CRITICAL | Auth/Demo | Demo login COMPLETELY BROKEN — AILINE_DEV_MODE=false blocks X-Teacher-ID header, demo users have empty passwords (rejected in non-dev mode) |
| C1b | CRITICAL | Auth/JWT | **AILINE_JWT_SECRET not configured in Docker** — auth router has dev fallback secret, but middleware _get_jwt_config() returns empty algorithms → JWTs created by login are REJECTED by middleware. Design mismatch. |
| C1c | CRITICAL | Auth/Reg | POST /auth/register throws RuntimeError: "AILINE_JWT_SECRET must be set in non-dev mode" → 500 error |
| C2 | CRITICAL | Docker | Frontend container OOM at 512MB — 741 restarts, tests/typecheck/build fail (need 1.5-2GB) |
| C3 | HIGH | TypeScript | 2 type errors: landing-page.tsx:119 (FeatureItem.icon vs Feature.icon union), learning-trajectory.tsx:147 ({} not assignable to ReactNode) |
| C4 | HIGH | Tests | 2 test failures in plan-generation-flow.test.tsx ("shows pipeline viewer when running", "calls cancel when cancel button is clicked") |
| C5 | HIGH | Docker | `uv run pytest` fails in Docker (agents editable path ../agents doesn't exist in container). Documented test commands wrong. |
| C6 | HIGH | Auth | Admin demo profiles (school_admin, super_admin) have no demo profiles in frontend DEMO_PROFILES_BY_ROLE — empty arrays |
| C7 | HIGH | Auth | VALID_DEMO_PROFILES allowlist missing admin-principal and admin-super keys |
| C8 | HIGH | Demo | AILINE_DEMO_MODE=0 blocks demo seed/reset/run endpoints (403) |
| C9 | HIGH | Docker/TS | TypeScript compiler OOM — tsc --noEmit hits "JavaScript heap out of memory" even at 512MB |
| C10 | MEDIUM | Rate Limit | Login rate limiter (5/min per IP) blocks demo testing — all Docker requests come from same IP |
| C11 | MEDIUM | Docs | TODO.md out of sync — shows Phase 1 as `[ ]` but features are implemented |
| C12 | MEDIUM | Setup | Setup wizard shows has_env=false, completed=false — not fully wired |
| C13 | MEDIUM | Email | Demo user email format mismatch: auth seeds `{key}@ailine-demo.edu`, unclear to users |
| C14 | MEDIUM | Health | /health/diagnostics requires auth — should be public for monitoring |
| C15 | LOW | Docker | Frontend healthcheck wget --spider returns "Invalid seek" with Next.js dev server |
| C16 | LOW | Security | API keys visible in `docker compose config` output |

### Architecture Observations
- **Hexagonal architecture well-executed** — clean domain/ports/adapters separation
- **72 API endpoints** across 15 routers — comprehensive coverage
- **In-memory user store** (InMemoryUserRepository) — auth state lost on restart
- **Permissive middleware** — good pattern but some endpoints unprotected
- **SSE streaming** — mature implementation with 14 event types
- **Sign language** — 8 languages with rich metadata, works without auth
- **Skills system** — complex runtime with token budgeting, well-designed

---

## Sprint Plan (3 Phases, 45 Micro-Tasks)

### Phase 1: Critical Fixes (MUST do — demo broken)

#### F-217: Auth & Demo Login Fix (Priority: CRITICAL)
**Goal:** Fix JWT infrastructure AND make demo login work end-to-end

1. [ ] Add `AILINE_JWT_SECRET` to docker-compose.yml api environment (generate with `python -c 'import secrets; print(secrets.token_urlsafe(48))'`)
2. [ ] Add `AILINE_JWT_SECRET` to .env.example with placeholder
3. [ ] Fix JWT middleware/auth router mismatch: ensure _get_jwt_config() works with the dev fallback secret when AILINE_JWT_SECRET is not set BUT DEV_MODE is true
4. [ ] Set `AILINE_DEV_MODE=true` in docker-compose.yml for hackathon development
5. [ ] Set `AILINE_DEMO_MODE=1` in docker-compose.yml to enable demo scenarios
6. [ ] Create dedicated `/auth/demo-login` endpoint: accepts `demo_key`, maps to profile, returns JWT with correct role/org_id
7. [ ] Add `/auth/demo-login` to _EXCLUDED_EXACT in tenant middleware
8. [ ] Frontend: change handleDemoLogin to call /auth/demo-login instead of just setting X-Teacher-ID
9. [ ] Frontend: store JWT from demo-login in auth store (same flow as email login)
10. [ ] Add admin demo profiles to DEMO_PROFILES_BY_ROLE (school_admin, super_admin)
11. [ ] Add admin-principal and admin-super to VALID_DEMO_PROFILES allowlist
12. [ ] Seed demo users with hashed password ("demo123") so email login also works
13. [ ] Ensure seed_demo_users() runs even when AILINE_DEV_MODE=false
14. [ ] Tests: verify all 8 demo profiles can log in via demo-login and access their routes
15. [ ] Tests: verify RBAC enforcement after demo login (students can't access teacher endpoints)

#### F-218: TypeScript & Test Fixes (Priority: HIGH)
11. [ ] Fix landing-page.tsx:119 — change FeatureItem.icon from `string` to Feature icon union type
12. [ ] Fix learning-trajectory.tsx:147 — cast `(row as Record<string, unknown>)[k]` to `String()`
13. [ ] Fix plan-generation-flow.test.tsx — update "shows pipeline viewer" test to match current component structure
14. [ ] Fix plan-generation-flow.test.tsx — update "calls cancel" test to match current cancel button
15. [ ] Verify 0 TypeScript errors: `docker compose exec frontend pnpm typecheck`
16. [ ] Verify all tests pass: `docker compose run --rm frontend pnpm test`

#### F-219: Docker & CI Improvements (Priority: HIGH)
17. [ ] Increase frontend container memory limit from 512MB to 2GB in docker-compose.yml
18. [ ] Add `NODE_OPTIONS=--max-old-space-size=1536` to frontend container environment
19. [ ] Fix frontend healthcheck: replace `wget --spider` with `curl -f http://127.0.0.1:3000 || exit 1`
20. [ ] Fix test documentation: `python -m pytest` instead of `uv run pytest` for Docker
21. [ ] Update CLAUDE.md, frontend/CLAUDE.md, TEST.md with correct Docker test commands
22. [ ] Add one-off test runner: `docker compose run --rm --no-deps frontend pnpm test`
23. [ ] Ensure `docker compose exec api python -m pytest tests/ -q` is canonical backend test command
24. [ ] Make /health/diagnostics public (remove auth requirement for monitoring)

### Phase 2: Polish & UX (SHOULD do — quality improvements)

#### F-220: Auth & Demo Polish
22. [ ] Set AILINE_DEV_MODE=true in docker-compose.yml for hackathon demo ease
23. [ ] Set AILINE_DEMO_MODE=1 in docker-compose.yml to enable demo scenarios
24. [ ] Seed demo users at startup with hashed demo password ("demo123") so email login works too
25. [ ] Add demo password display on login page ("Demo password: demo123")
26. [ ] Sync TODO.md with actual implementation status
27. [ ] Add demo-login endpoint to /demo/ excluded prefix so it doesn't need tenant context

#### F-221: Frontend UX Polish
28. [ ] Add loading skeleton to login page during API call
29. [ ] Add role descriptions to login cards (not just icons)
30. [ ] Show "Demo" badge on demo profiles clearly
31. [ ] Add keyboard shortcut hints to command palette
32. [ ] Ensure all 9 themes work correctly after login with different profiles
33. [ ] Verify reduced-motion works across all animations

#### F-222: Backend Resilience
34. [ ] Login rate limiter: increase to 20/min for Docker/demo or exempt demo-login
35. [ ] Add /auth/demo-login to _EXCLUDED_EXACT in tenant middleware
36. [ ] Add healthcheck to verify demo users are seeded
37. [ ] Ensure seed_demo_users() is called even when AILINE_DEV_MODE=false

### Phase 3: Sprint 25 Phase 2 Completion

#### F-176: Skills API Endpoints (from Sprint 25)
38. [ ] Wire /v1/skills CRUD endpoints with SkillRepository
39. [ ] Fork endpoint: POST /v1/skills/{slug}/fork
40. [ ] Rate endpoint: POST /v1/skills/{slug}/rate
41. [ ] Suggest endpoint: POST /v1/skills/suggest (AI-powered)
42. [ ] Verify 9 endpoints work end-to-end

#### F-165: TTS Integration (from Sprint 25)
43. [ ] ElevenLabs adapter with 3-tier fallback
44. [ ] POST /v1/tts/synthesize endpoint
45. [ ] GET /v1/tts/voices and /voices/{id}

---

## Acceptance Criteria
- [ ] All 8 demo profiles login successfully in Docker
- [ ] 0 TypeScript errors
- [ ] All frontend tests pass (one-off container, no OOM)
- [ ] All backend tests pass (2,403+)
- [ ] Demo login works end-to-end: click profile → JWT → authenticated API calls
- [ ] Docker Compose builds and runs with health/readiness on all 4 services
- [ ] control_docs/ synced with delivered behavior
- [ ] RBAC enforcement verified: students can't access teacher endpoints

## Dependencies & Risks
- **Risk:** Demo login redesign may require frontend+backend changes in sync
- **Risk:** ElevenLabs API key needed for TTS testing
- **Dependency:** Frontend tests need 2GB+ memory container
- **Dependency:** Skills API needs SkillRepository (F-175 done)

## Decisions
- Demo login via dedicated endpoint (not dev mode bypass) — more secure and production-ready
- Keep AILINE_DEV_MODE as security toggle, don't rely on it for demo
- Frontend container 2GB is acceptable for dev/test; production build uses less
