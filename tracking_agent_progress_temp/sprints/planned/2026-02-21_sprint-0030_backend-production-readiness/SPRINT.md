# Sprint 30 — Backend Production Readiness, Observability & Compliance

**Goal:** Address critical production gaps: GEMINI_API_KEY fix, PII protection (in DB + logs), Google paid-service guard, full observability stack, distributed resilience, graceful shutdown, and large-file refactoring. Prepare for real-world deployment with student data safety.

**Theme:** Security, Compliance & Observability. Architecture direction: GPT-5.3-codex (3 consultations). GDPR/LGPD compliance verified against ANPD Resolucao 15/2024.

**Duration:** 2-3 weeks | **Status:** planned

**Prerequisites:** Sprint 29-A (Foundation & Hygiene) for dependency upgrades.

**Updated Feb 27, 2026:** Enriched with Codex (gpt-5.3-codex) architecture review findings. Key additions:
- Replace `@microsoft/fetch-event-source` (moved to Sprint 29-A as critical)
- Evaluate `arq` replacement (maintenance-only mode) → SAQ, Taskiq, or custom
- Upgrade `sentence-transformers` 3.x → 5.x (if used)
- **Codex-identified gaps (new stories):**
  - F-331: Durable LangGraph checkpointer (PostgresSaver) — replace in-memory for production
  - F-332: Database-level RLS enforcement — not just app-layer tenant filtering
  - F-333: JWKS/kid lifecycle + key rotation pipeline — beyond env var JWT secrets
  - F-334: Integration test confidence — ensure critical paths test against real Postgres/Redis, not SQLite/in-memory
  - F-335: Replace in-memory observability stores with persistent alternatives for production
  - F-336: API versioning stabilization — `/api/v1/` prefix with deprecation policy
- **Codex challenged assumptions:**
  - App-layer tenant filtering alone is insufficient → need DB-level RLS
  - High test count ≠ production confidence when fixtures default to SQLite/in-memory
  - JWT env var secrets without kid/JWKS = no zero-downtime key rotation

---

## Acceptance Criteria
- [ ] GEMINI_API_KEY accepted as primary env var (backward-compat with GOOGLE_API_KEY)
- [ ] Zero student PII in log output (structlog redaction processor)
- [ ] Google paid-service guard prevents free-tier processing of student data
- [ ] Persistent audit log for all authorization decisions (FERPA/LGPD ready)
- [ ] Student PII encrypted at rest (Fernet/AES-256)
- [ ] OTEL traces cover Redis, LLM calls, and DB queries with trace-ID correlation in logs
- [ ] Graceful shutdown drains SSE connections and flushes telemetry
- [ ] K8s-style health probes (live/ready/startup) with migration version check
- [ ] SmartRouter cascades on failure; IdempotencyGuard distributed via Redis
- [ ] app.py, auth.py, models.py all <500 LOC
- [ ] Docker Compose integration tests + Playwright E2E in CI
- [ ] All 2,451+ backend tests pass

---

## Stories (F-311 → F-330) — 20 stories, 6 phases

### Phase 1 — Critical Fixes (P0, Day 1) [IMMEDIATE]

**F-311: GEMINI_API_KEY env var fix**
- config.py: Add "GEMINI_API_KEY" as FIRST alias in AliasChoices (before GOOGLE_API_KEY)
- Update 8 files: config.py, RUN_DEPLOY.md, README.md, judge-packet.md, demo-script.md, setup_service.py, gemini_embeddings.py docstring, gemini_image_gen.py docstring
- AC: `GEMINI_API_KEY` in .env works. `GOOGLE_API_KEY` still accepted. Docs consistent.

**F-312: PII Redaction in Logs (CRITICAL)**
- structlog processor: regex + configured key list redacting emails, names, accessibility_needs, accommodations, passwords
- Key patterns: email (@), names (student_name, teacher_name), health data (accessibility_needs, accommodations, strengths)
- AC: Zero student PII in Docker Compose log output. Tested with real log samples. Dev mode preserves full logs optionally.

**F-313: Google Paid-Service Guard (COMPLIANCE)**
- Startup check: if `GEMINI_API_KEY` set without `AILINE_GEMINI_PAID_SERVICE=true`, log WARNING
- On student data processing paths (plan generation, tutor chat): block Gemini calls if paid flag false
- AC: Free-tier Gemini cannot process student PII per Google ToS. Warning logged. Config documented.

### Phase 2 — Compliance & Security (P0)

**F-314: Persistent Audit Log (FERPA/LGPD)**
- `AuditLogRow`: user_id, action, resource_type, resource_id, outcome (allow/deny), timestamp, ip_address, metadata (JSONB)
- Log at: require_role(), require_tenant_access(), check_student_access(), login, logout, demo-login
- Migration 0005. Admin endpoint: GET /admin/audit-log (paginated, filterable).
- AC: All auth decisions persisted. Retention configurable. Queryable by admin.

**F-315: PII Encryption at Rest**
- SQLAlchemy TypeDecorator (Fernet/AES-256) for: accessibility_needs, accommodations, strengths, learning_preferences
- Key from `AILINE_PII_ENCRYPTION_KEY` (fail-fast in prod if missing)
- Key rotation command. Migration safe (encrypt existing rows).
- AC: PII encrypted in DB. Decryption transparent. Key rotation works.

### Phase 3 — Observability Stack (P0-P1)

**F-316: OTEL Redis Instrumentation**
- Add `opentelemetry-instrumentation-redis` to deps
- Wire RedisInstrumentor in container_adapters with request/response hooks
- Custom span attributes: command, key_pattern (not full keys with PII)
- AC: Redis commands visible in traces. No PII in span attributes.

**F-317: Trace-ID Log Correlation**
- structlog processor injecting trace_id, span_id from active OTel span
- Dev mode: pretty console with trace_id prefix. Prod: JSON with trace_id field.
- AC: Every log line correlates with distributed trace. Searchable in aggregator.

**F-318: LLM Call Baggage Propagation**
- OTel baggage: student_id, plan_id, skill_name, agent_name propagated across agent calls
- Custom span attributes on every Pydantic AI and SmartRouter call
- AC: Can trace a plan generation from API request through all agent calls with full context.

### Phase 4 — Resilience & Reliability (P1)

**F-319: Redis-backed Distributed Idempotency Guard**
- Redis `SET NX` with TTL. Same API: try_acquire, complete, fail, get_result.
- Fallback to in-memory with structured log warning.
- AC: Works across Gunicorn/Cloud Run replicas. All tests pass.

**F-320: SmartRouter Cross-Tier Fallback**
- On failure: cascade primary → middle → cheap. Track fallback count in RouteMetrics.
- Config: AILINE_ROUTER_MAX_FALLBACKS=2, AILINE_ROUTER_FALLBACK_ENABLED=true.
- AC: Provider failure cascades. Metrics track rate. Config-driven.

**F-321: SSE Backpressure**
- Bounded asyncio.Queue per client (max 100). Overflow: drop oldest, emit stream.gap.
- AC: Slow clients don't block. Gap notification sent. Replay via Last-Event-ID works.

**F-322: Lifecycle State + Graceful Shutdown**
- LifecycleState enum: STARTING → READY → DRAINING → STOPPED
- SIGTERM handler: transition to DRAINING, stop accepting new SSE, drain active with timeout
- Container.close(): flush telemetry, close DB pools, shutdown arq workers
- AC: Zero dropped SSE on deploy. Tracer force_flush called. Clean Docker stop.

**F-323: K8s-Style Health Probes**
- /health/live (process alive), /health/ready (DB + Redis + migration version), /health/startup (init complete)
- Cached async LLM provider health with TTL (30s)
- AC: Readiness fails if DB unreachable or migration stale. Startup probe prevents premature traffic.

### Phase 5 — Refactoring (P1)

**F-324: Split app.py (709 → ~4 modules)**
- Extract: api/health.py, api/capabilities.py, api/metrics.py, api/factory.py (core wiring)
- AC: app.py <300 LOC. All modules <500 LOC. All tests pass.

**F-325: Split auth.py (654 → service + router)**
- Extract: app/services/auth_service.py (password hashing, JWT, user lookup, rate limit)
- Router: thin HTTP only.
- AC: Router <300 LOC. Service testable in isolation.

**F-326: Split models.py (646 → per-domain)**
- models/core.py, models/materials.py, models/pipeline.py, models/rbac.py, models/skills.py, models/__init__.py (re-exports)
- AC: Each <200 LOC. All imports work. All tests pass.

**F-327: Remove deprecated AiLineConfig**
- Delete legacy config.py. Migrate tutoring/builder.py reference.
- AC: Single config system. No DeprecationWarning.

### Phase 6 — CI/CD (P2)

**F-328: Docker Compose Integration Test CI Job**
- GitHub Actions: docker compose up + exec api uv run pytest + exec frontend pnpm test
- AC: Tests against real Postgres + Redis. Pipeline green.

**F-329: E2E Playwright CI Job**
- 8 Playwright specs in Docker. Screenshots archived as artifacts.
- AC: All E2E pass in CI. Visual regression screenshots saved.

**F-330: Consolidate /skills vs /v1/skills**
- /skills returns 301 → /v1/skills. Deprecation in CHANGELOG.
- AC: No breaking change. Redirect works.

---

## Dependencies
- Phase 1 (critical fixes) has zero deps — start immediately
- Phase 2 (PII encryption) requires AILINE_PII_ENCRYPTION_KEY in Docker Compose
- Phase 3 (OTEL) requires opentelemetry-instrumentation-redis dep
- Phase 5 (refactoring) can parallel with Phase 3-4

## Risks
- F-315: Data migration for existing encrypted columns needs rollback plan
- F-320: Async retry + streaming fallback is complex
- F-322: Graceful shutdown needs thorough integration testing with Docker stop

## Micro-tasks: ~65 (20 stories × ~3.25 tasks each)
