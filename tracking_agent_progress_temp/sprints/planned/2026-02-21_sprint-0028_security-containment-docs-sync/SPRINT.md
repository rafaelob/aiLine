# Sprint 28 — Security Containment + Docs Sync

**Date:** 2026-02-21
**Status:** planned
**Source:** Comprehensive 5-agent audit (backend review, security audit, docs audit) + Codex/Gemini expert debate

## Goal

Fix all CRITICAL and HIGH findings from the Sprint 27 final audit. Sync all documentation. Fix i18n diacritics. Ship with zero known security gaps.

## Acceptance Criteria

- [ ] Zero CRITICAL findings open
- [ ] Zero HIGH findings open
- [ ] All MEDIUM findings addressed or tracked with owner+date
- [ ] All docs in control_docs/ match codebase reality
- [ ] i18n diacritics correct (pt-BR, es)
- [ ] All tests green (backend + frontend + typecheck)
- [ ] Docker Compose builds and all 4 services healthy

---

## Phase 1 — Emergency Security Containment (CRITICAL + exploitable HIGHs)

### F-251: Demo login privilege escalation fix
- [ ] Enforce `_validate_role()` in `/auth/demo-login` (cap to teacher/student/parent)
- [ ] Remove `admin-super` and `admin-principal` from `DEMO_PROFILES` or block admin roles
- [ ] Remove admin profile keys from frontend `VALID_DEMO_PROFILES` (api.ts)
- [ ] Add exploit regression test: demo-login with admin key returns 403 or teacher role
- **Severity:** CRITICAL | **Source:** Backend C1, Security C-2

### F-252: TraceStore tenant integrity enforcement
- [ ] `append_node()` and `update_run()` must NOT auto-create RunTrace
- [ ] Require `get_or_create()` to be called first; append/update raise if run not found
- [ ] Add teacher_id ownership check in append_node/update_run
- [ ] Add cross-tenant trace write rejection test
- **Severity:** CRITICAL | **Source:** Backend C2

### F-253: Dev mode default to OFF
- [ ] Change docker-compose.yml `AILINE_DEV_MODE: "${AILINE_DEV_MODE:-true}"` → `"${AILINE_DEV_MODE:-false}"`
- [ ] Update .env.example to explicitly show `AILINE_DEV_MODE=true` for local dev
- [ ] Update RUN_DEPLOY.md with this change
- **Severity:** HIGH | **Source:** Security H-1

### F-254: Remove hardcoded JWT fallback secret
- [ ] Auth router: generate random secret at startup if dev mode, never use hardcoded
- [ ] Middleware: same — use runtime-generated dev secret
- [ ] docker-compose.yml: remove hardcoded default, require explicit AILINE_JWT_SECRET
- [ ] Startup validation: refuse to start without JWT key material in non-dev mode (already done)
- **Severity:** HIGH | **Source:** Security H-2, Backend H3 (partial)

### F-255: Demo login rate limiting
- [ ] Add `_check_login_rate()` call at start of `demo_login()`
- [ ] Add test for demo-login rate limit enforcement
- **Severity:** MEDIUM | **Source:** Security M-1

### F-256: Diagnostics admin-only access
- [ ] Change `/internal/diagnostics` from `Depends(require_authenticated)` to `Depends(require_admin)`
- [ ] Add test: student/parent gets 403 on /internal/diagnostics
- **Severity:** MEDIUM | **Source:** Backend M5

---

## Phase 2 — Reliability + Code Quality (remaining HIGHs + MEDIUMs)

### F-257: Rate limiter docs/code alignment
- [ ] Reconcile `_LOGIN_MAX_ATTEMPTS` constant (20) with docstrings (say "5")
- [ ] Decision: keep 20 for demo or reduce to 10; update ALL docstrings to match
- **Severity:** HIGH | **Source:** Backend H1

### F-258: Redis access encapsulation
- [ ] Add `get_redis_client()` public method to EventBus protocol
- [ ] Replace `event_bus._redis` access in auth.py and tenant_context.py
- [ ] Update container.py if needed
- **Severity:** HIGH | **Source:** Backend H3

### F-259: Runs API server-side filtering
- [ ] Add `status` filter param to `TraceStore.list_recent()`
- [ ] Remove load-all-500-then-filter pattern in runs.py
- [ ] Update tests
- **Severity:** HIGH | **Source:** Backend H4

### F-260: Seed module import unification
- [ ] Standardize all imports to use `demo_profiles.DEMO_PROFILES` directly
- [ ] Remove import from `demo.py` re-export module
- **Severity:** HIGH | **Source:** Backend H5

### F-261: Role validation returns 422
- [ ] `_validate_role()` returns 422 on invalid role instead of silent teacher default
- [ ] Update tests for explicit error on invalid role
- **Severity:** MEDIUM | **Source:** Backend M1

### F-262: plans_stream body immutability
- [ ] Use local variable instead of mutating `body.user_prompt` in-place
- **Severity:** MEDIUM | **Source:** Backend M4

### F-263: Frontend sessionStorage JWT removal
- [ ] Implement one-time migration: hydrate Zustand from sessionStorage → delete
- [ ] Remove sessionStorage fallback from api.ts
- [ ] Test across tabs
- **Severity:** MEDIUM | **Source:** Security M-2

### F-264: Docker port exposure hardening
- [ ] Bind DB/Redis ports to 127.0.0.1 only in docker-compose.yml
- [ ] Document override in RUN_DEPLOY.md
- **Severity:** MEDIUM | **Source:** Security M-5

---

## Phase 3 — Documentation Sync + I18N

### F-265: SYSTEM_DESIGN.md version sync
- [ ] Tailwind 4.1.18 → 4.2.0
- [ ] motion 12.34.0 → 12.34.2
- [ ] next-intl 4.8.2 → 4.8.3
- [ ] Pydantic AI 1.58.0 → >=1.62.0
- [ ] Remove phantom shadcn/ui 3.8.4 reference
- [ ] Fix embedding dimensions inconsistency note (config 3072 vs migration 1536)
- [ ] Remove stale deps (faster-whisper, pypdf, langgraph-checkpoint-postgres if not in pyproject.toml)

### F-266: FEATURES.md Sprint 27 addition
- [ ] Add Sprint 27 section (F-230 to F-250, 21 features)

### F-267: SECURITY.md roles + authz update
- [ ] Fix roles: "admin, educator, student" → "super_admin, school_admin, teacher, student, parent"
- [ ] Update authz function references to match actual code

### F-268: RUN_DEPLOY.md port defaults + env vars
- [ ] Fix port defaults: 8011/3011/5411/6311 (not 8000/3000)
- [ ] Document frontend env vars (API_INTERNAL_URL, NODE_OPTIONS)

### F-269: TEST.md counts + commands
- [ ] Update test counts to ~3,883 (2,445 backend + 1,438 frontend)
- [ ] Fix Docker pytest command: `python -m pytest` not `uv run pytest`

### F-270: frontend/CLAUDE.md version sync
- [ ] Tailwind 4.1.18 → 4.2.0
- [ ] motion 12.34.0 → 12.34.2

### F-271: I18N diacritics full sweep
- [ ] pt-BR: currículo, papéis, início, Segurança, padrões, vírgula (7 known + full sweep)
- [ ] es: Sección (1 known + full sweep)
- [ ] Run comprehensive regex audit for common missing diacritics

---

## Dependencies

- Phase 1 is release-blocking — must complete before any deployment
- Phase 2 depends on Phase 1 (security foundation must be solid first)
- Phase 3 can partially overlap with Phase 2 (docs are independent of code changes)

## Validation Gates

### Phase 1 Gate
- Exploit regression tests pass (demo-login admin escalation blocked)
- Cross-tenant trace write blocked
- JWT startup refuses without key material in non-dev
- `docker compose exec api python -m pytest tests/ -x -q --tb=short`

### Phase 2 Gate
- No private `_redis` attribute access anywhere
- Runs API filtering is server-side
- `docker compose exec api python -m pytest tests/ -x -q --tb=short`
- `docker compose exec api python -m ruff check . --no-cache`

### Phase 3 Gate
- All control_docs/ match codebase
- i18n: 0 missing diacritics
- `docker compose exec frontend pnpm test`
- `docker compose exec frontend pnpm typecheck`

## Risks

| Risk | Mitigation |
|------|------------|
| Breaking demo scripts expecting admin-super | Update fixtures + add admin-auth test via real credentials |
| TraceStore API change touches many callers | Single coordinated refactor PR |
| Dev mode OFF by default breaks local dev | Explicit AILINE_DEV_MODE=true in .env.example |
| Port binding changes break local workflows | Document override in RUN_DEPLOY.md |

## Decisions (confirmed by Codex + Gemini consensus)

1. **Demo login**: Defense-in-depth — role allowlist + remove admin profiles + rate limit
2. **TraceStore**: Enforce get_or_create-first; append/update never auto-create
3. **JWT secret**: Refuse startup without explicit key material in non-dev; random dev-only secret
4. **sessionStorage**: Migrate to Zustand then remove
5. **i18n**: Full sweep, not just known 8 instances
6. **SSE XSS**: Audit usage; React auto-escape is sufficient unless dangerouslySetInnerHTML
