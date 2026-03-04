# Sprint 29-A — Foundation & Hygiene ("Clean Slate")

**Goal:** Stabilize the dependency foundation, patch security vulnerabilities, and modernize tooling BEFORE the massive design system refactor (Sprint 29). Zero feature work — pure hygiene.

**Theme:** Dependency cleanup, security patches, tooling modernization. This sprint de-risks Sprint 29+ by ensuring a solid, up-to-date base.

**Duration:** 1 week | **Status:** planned

**Sources:** Dependency audit (Feb 27), Codex architecture review, Gemini sprint planning consultation.

---

## Acceptance Criteria
- [ ] Zero known CVEs in direct dependencies (PyJWT, langgraph-checkpoint)
- [ ] All CRITICAL security fixes applied (Parent IDOR, skill slug, composite FK, demo-login guard, CI scans)
- [ ] All linters/formatters at latest stable (Ruff 0.15, Mypy 1.19, ESLint 10)
- [ ] Test framework at latest major (pytest 9, pytest-asyncio 1.3)
- [ ] All SDKs at latest stable (Anthropic 0.84, OpenAI 2.24, Pydantic AI 1.63)
- [ ] pnpm at latest (10.30), tailwind-merge at 3.5, Tailwind at 4.2.1
- [ ] @microsoft/fetch-event-source replaced with maintained alternative
- [ ] All 3,889+ tests passing after upgrades
- [ ] Docker Compose builds and runs healthy

---

## Stories (F-380 → F-403) — 24 stories, 3 phases

### Phase 1 — Critical Security & Unmaintained (P0, Day 1) [IMMEDIATE]

**F-380: Pin PyJWT >=2.10.1 (CVE-2024-53861)**
- Update `runtime/pyproject.toml`: change `PyJWT[crypto]>=2.9,<3` to `>=2.10.1,<3`
- Verify `decode()` always specifies `algorithms` explicitly (already done per Sprint 22)
- Run full auth test suite
- AC: No CVE-2024-53861 exposure. All auth tests green.
- Effort: TRIVIAL | Risk: LOW

**F-381: Replace @microsoft/fetch-event-source (UNMAINTAINED 5 years)**
- Replace with native `fetch` + `ReadableStream` (POST SSE) or `@sentool/fetch-event-source` (API-compatible fork)
- Evaluate: if only GET SSE needed → native `EventSource`. If POST needed → maintained fork or custom thin wrapper.
- Update all SSE client code in `frontend/src/hooks/` and `frontend/src/components/`
- AC: Zero imports of `@microsoft/fetch-event-source`. SSE streaming works identically. All frontend tests pass.
- Effort: MODERATE | Risk: MEDIUM (SSE is critical path)

**F-382: Upgrade pgvector Docker image 0.8.0 → 0.8.2**
- Update `docker-compose.yml`: `pgvector/pgvector:0.8.2-pg16`
- AC: Docker Compose starts healthy. Vector search tests pass.
- Effort: TRIVIAL | Risk: LOW

**F-398: Upgrade langgraph-checkpoint >=3.0.0 (CRITICAL RCE deserialization fix)**
- CRITICAL SECURITY: RCE via deserialization in langgraph-checkpoint < 3.0.0
- Add `langgraph-checkpoint>=3.0.0` to `runtime/pyproject.toml`
- Verify LangGraph workflows still function correctly
- AC: No RCE exposure. Plan/tutor workflows pass.
- Effort: LOW | Risk: MEDIUM (may require checkpoint format migration)

**F-399: Fix Parent IDOR in /progress/student/{student_id} (CRITICAL FERPA breach)**
- Any authenticated parent can read any student's progress records
- Files: `progress.py:104-112`, `progress_store.py:144`
- Implement `check_student_access(student_id, session)` for PARENT role; deny by default
- AC: Parents can only access their linked students. 403 on unauthorized access. Tests cover cross-tenant attempt.
- Effort: 2h | Risk: LOW

**F-400: Fix cross-tenant skill slug ambiguity (CRITICAL)**
- `scalar_one_or_none()` raises `MultipleResultsFound` with duplicate slugs across teachers
- Files: `skill_repository.py:65, 129, 157, 291`
- Fix: Make tenant-aware repository API the default (`get_by_slug(slug, teacher_id)`)
- AC: Skill lookups always scoped to tenant. No `MultipleResultsFound`. Tests with duplicate slugs pass.
- Effort: 3h | Risk: LOW

**F-401: Fix composite FK schema error in PostgreSQL 16**
- `ERROR: no unique constraint matching given keys for referenced table "courses"`
- Files: `models.py:124, 192, 224, 296`
- Fix: Add `UniqueConstraint("teacher_id", "id")` on parent tables before creating composite FKs
- AC: Migration applies cleanly on fresh PG16. All DB tests pass.
- Effort: 2h | Risk: MEDIUM (migration required)

**F-402: Make CI security scans blocking (remove || true)**
- Files: `ci.yml:212-220`
- Remove `|| true` from security scan jobs; enforce severity threshold
- AC: CI fails on CRITICAL/HIGH vulnerabilities. Security job is required for merge.
- Effort: 30min | Risk: LOW

**F-403: Gate /auth/demo-login behind AILINE_DEMO_MODE**
- `/auth/demo-login` mints valid JWTs even in non-demo environments
- Files: `auth.py:540`, `tenant_context.py:93`
- Fix: Hard-block demo-login unless `AILINE_DEMO_MODE=1`; disable by default
- AC: 404 on /auth/demo-login without AILINE_DEMO_MODE. Tests verify both modes.
- Effort: 1h | Risk: LOW

### Phase 2 — Tooling Modernization (P0, Day 2-3)

**F-383: Upgrade pnpm 10.7.1 → 10.30.3**
- Update `frontend/package.json` `packageManager` field
- Run `pnpm install` to regenerate lockfile
- AC: All frontend commands work. Lockfile regenerated.
- Effort: TRIVIAL | Risk: LOW

**F-384: Migrate ESLint 9 → 10 (flat config only)**
- Remove `@eslint/eslintrc` compat dependency
- Convert to pure `eslint.config.js` with `defineConfig()`, `extends`, `globalIgnores()`
- Update `eslint-config-next` to 16.x compatible version
- AC: `pnpm lint` passes with ESLint 10. Zero eslintrc references.
- Effort: MODERATE | Risk: MEDIUM (config system completely changed)

**F-385: Upgrade Ruff 0.9 → 0.15.3**
- Update `runtime/pyproject.toml`: `ruff>=0.15,<1`
- Run `uv run ruff check . --fix` to apply 2026 style guide changes
- AC: `ruff check .` clean. All formatting consistent.
- Effort: LOW | Risk: LOW

**F-386: Upgrade Mypy 1.14 → 1.19.1**
- Update `runtime/pyproject.toml` dev deps: `mypy>=1.19,<2`
- Fix any new type errors surfaced by 1.19
- AC: `mypy .` clean (zero errors).
- Effort: LOW | Risk: LOW

**F-387: Upgrade pytest 8 → 9.0.2 + pytest-asyncio 0.24 → 1.3.0**
- Update dev deps: `pytest>=9,<10`, `pytest-asyncio>=1.3,<2`
- Check for strict parametrization ID changes
- Verify scoped event loop behavior with new pytest-asyncio
- AC: All 2,451 backend tests pass. No fixture/loop issues.
- Effort: MODERATE | Risk: MEDIUM (major version changes)

**F-388: Upgrade TypeScript 5.8 → 5.9.3**
- Update `frontend/package.json`: `typescript: "^5.9.0"`
- Fix any new type errors
- AC: `pnpm typecheck` clean.
- Effort: TRIVIAL | Risk: LOW

### Phase 3 — SDK & Library Updates (P1, Day 3-5)

**F-389: Upgrade Anthropic SDK 0.79 → 0.84.0**
- Update `runtime/pyproject.toml`: `anthropic>=0.84.0,<1`
- Verify Claude adapter compatibility
- AC: LLM adapter tests pass. No breaking API changes.
- Effort: TRIVIAL | Risk: LOW

**F-390: Upgrade OpenAI SDK 2.11 → 2.24.0**
- Update `runtime/pyproject.toml`: `openai>=2.20,<3`
- Verify Responses API usage (already mandated by CLAUDE.md)
- AC: OpenAI adapter tests pass.
- Effort: TRIVIAL | Risk: LOW

**F-391: Upgrade Pydantic AI 1.58 → 1.63.0**
- Update `runtime/pyproject.toml`: `pydantic-ai>=1.63.0,<2`
- Check for new features: Gemini 3.1 Pro Preview support, logprob, args_validator
- AC: All agent tests pass.
- Effort: TRIVIAL | Risk: LOW

**F-392: Upgrade FastAPI 0.129 → 0.133.1**
- Update `runtime/pyproject.toml`: `fastapi>=0.133.0,<1`
- Test strict Content-Type checking behavior (new default)
- AC: All API tests pass. SSE endpoints work with Content-Type validation.
- Effort: LOW | Risk: MEDIUM (strict Content-Type may affect clients)

**F-393: Upgrade pydantic-settings 2.7 → 2.13.1**
- Update constraint: `pydantic-settings>=2.13,<3`
- AC: Config loads correctly. All tests pass.
- Effort: TRIVIAL | Risk: LOW

**F-394: Upgrade tailwind-merge 3.0.2 → 3.5.0**
- Update `frontend/package.json`: `tailwind-merge: "3.5.0"`
- AC: Better Tailwind v4.2 support. No visual regressions.
- Effort: TRIVIAL | Risk: LOW

**F-395: Upgrade Tailwind CSS 4.2.0 → 4.2.1 + motion 12.34.2 → 12.34.3**
- Patch-level bumps in `frontend/package.json`
- AC: No visual regressions.
- Effort: TRIVIAL | Risk: NEGLIGIBLE

**F-396: Upgrade SQLAlchemy 2.0.36 → 2.0.47**
- Update `runtime/pyproject.toml`: `sqlalchemy[asyncio]>=2.0.47,<3`
- AC: All DB tests pass. No breaking changes (patch within 2.0.x).
- Effort: TRIVIAL | Risk: LOW

**F-397: Upgrade OpenTelemetry 1.29 → 1.39.1**
- Update all OTel deps in `runtime/pyproject.toml` to `>=1.39,<2`
- AC: Tracing works. All observability tests pass.
- Effort: TRIVIAL | Risk: LOW

---

## Dependencies
- Phase 1 has zero deps — start immediately
- Phase 2 depends on Phase 1 (especially ESLint migration after pnpm upgrade)
- Phase 3 can parallel with Phase 2

## Risks
- F-381 (fetch-event-source replacement): SSE is on the critical path. Needs thorough E2E testing.
- F-384 (ESLint 10): Complete config system change. Timebox to 2 days; if blocked, defer to Sprint 29.
- F-387 (pytest 9): Major version jump. Event loop fixture changes may need test refactoring.
- F-398 (langgraph-checkpoint): RCE fix may require checkpoint format migration if using persistence.
- F-399 (Parent IDOR): FERPA breach — must be fixed before any production deployment.
- F-401 (Composite FK): Migration required on live DB; test rollback path.

## Micro-tasks: ~55 (24 stories × ~2.3 tasks each)

## Estimated Effort: 7 working days (1 developer) or 4 days (2 developers)
