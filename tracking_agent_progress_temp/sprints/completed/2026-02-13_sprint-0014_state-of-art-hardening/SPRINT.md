# Sprint 0014 — State-of-the-Art Hardening

**Status:** completed
**Date:** 2026-02-13
**Goal:** Comprehensive pass across ALL sprints: implement missing pieces, harden security, improve tests, fix gaps, elevate to production-grade.

## Expert Input Sources
- **GPT-5.2**: 20 gaps identified (JWT, tracing, eval harness, RAG provenance, type safety, CI/CD, privacy)
- **Gemini-3-Pro**: 15 frontend improvements (PPR, View Transitions, PWA, visual regression, OG images)
- **Web Research**: FastAPI hardening 2026, Playwright a11y patterns, async best practices

## Streams & Tasks

### STREAM A: Security Hardening (backend-engineer)
- A1: JWT verification — full RS256/ES256 verification (iss/aud/exp/nbf), JWKS support, algorithm pinning
- A2: Security tests — forged token, expired, wrong aud, wrong kid, replay attack, tenant impersonation
- A3: Prompt injection defenses — document trust scoring, retrieval sanitization, instruction hierarchy in RAG
- A4: Audit logging — admin actions, content access, authentication events to structured log
- A5: Environment validation — strict Pydantic settings with typed constraints, fail-fast on missing critical vars

### STREAM B: Backend Quality & Architecture (backend-engineer)
- B1: Type safety cleanup — eliminate `Any` in routing_types.py provider fields, annotate `**kwargs` with TypedDict/Protocol, fix 16 `type:ignore` with proper types or narrowed ignores with reasons
- B2: Remove `pass` stubs — container.py (2), session.py (1), plans_stream.py (1) — implement proper logic or explicit no-ops with comments
- B3: Large file refactoring — container.py (476 LOC), validator.py (462), hard_constraints.py (432), smart_router.py (426) — split by responsibility
- B4: OpenTelemetry tracing — spans across request -> agent run -> LLM call -> tool -> DB, correlation IDs propagated everywhere
- B5: Agent eval harness — golden sets with rubric scoring, regression detection across model changes, reproducibility controls
- B6: RAG provenance UX — citations with chunk IDs/doc titles/timestamps/confidence, retrieval diagnostics (top-k scores, filters)
- B7: API error model — RFC 7807 problem details, unified error schema, versioned contract, explicit retry semantics
- B8: Performance — connection pool validation under SSE load, N+1 query check, HNSW tuning, caching strategy

### STREAM C: Frontend Excellence (frontend-engineer)
- C1: Sign language worker completion — implement real MediaPipe loading (remove TODO stubs), feature flag + graceful fallback
- C2: Playwright webServer config — self-contained E2E (build + start + test), no manual dev server needed
- C3: Visual regression tests — 5-10 screenshot comparisons for key layouts (dashboard, pipeline viewer, exports)
- C4: View Transitions API — morph animations between route navigations
- C5: Dynamic OG images — next/og ImageResponse for shared lesson links
- C6: PWA manifest + install prompt — proper manifest.json, beforeinstallprompt, icons, shortcuts
- C7: Recharts keyboard accessibility — tab through data points, aria-live announcements
- C8: Optimistic UI — useOptimistic for quick interactions (mark complete, toggle settings)

### STREAM D: Testing & Quality Gates (quality-tester)
- D1: Run full Docker Compose test suite — backend + agents + frontend all green in containers
- D2: Backend coverage report — identify files below 75% line coverage
- D3: Frontend coverage report — identify components below 75% coverage
- D4: Axe-core a11y in CI — every page navigation must pass with zero violations (wcag2a + wcag2aa + wcag21aa)
- D5: Security scanning — pip-audit, pnpm audit, Trivy container scan
- D6: Mypy strict mode audit — count errors, create plan to reach zero
- D7: Load test (basic) — k6 or locust: 50 concurrent SSE connections, measure p95 latency
- D8: Integration test for full plan pipeline — real DB, real Redis, FakeLLM, end-to-end in Docker

## Acceptance Criteria
- [ ] JWT verification complete with security tests
- [ ] Zero `Any` types in critical paths (routing, agents)
- [ ] All `pass` stubs replaced with implementations
- [ ] No file over 500 LOC (or documented exception)
- [ ] OpenTelemetry spans on all LLM/tool/DB calls
- [ ] Sign language worker TODOs resolved
- [ ] E2E tests self-contained (webServer config)
- [ ] Visual regression baseline captured
- [ ] Security scans clean (no critical/high)
- [ ] Docker Compose full suite green
- [ ] Coverage >= 75% on all touched code
