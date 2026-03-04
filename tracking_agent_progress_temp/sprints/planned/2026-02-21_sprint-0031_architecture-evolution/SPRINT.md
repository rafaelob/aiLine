# Sprint 31 — Architecture Evolution & Agent Maturity

**Goal:** Application service layer, domain events, background jobs, API versioning, prompt management, cost tracking, content safety guardrails, and persistent data stores. Evolve from working app to well-architected, AI-production-ready platform.

**Theme:** Structural patterns that enable scaling + AI agent production maturity. Architecture direction: GPT-5.3-codex consultations.

**Duration:** 2-3 weeks | **Status:** planned

---

## Acceptance Criteria
- [ ] Application service layer with typed Commands for top-3 use cases
- [ ] Domain events on Redis EventBus with 3+ async handlers
- [ ] arq background worker as separate Docker service with 2+ job types
- [ ] All API endpoints under /v1/ with X-API-Version header
- [ ] Cursor-based pagination on all list endpoints
- [ ] Prompt version registry in DB (version, activate, rollback)
- [ ] Per-tenant cost tracking with budget alerts
- [ ] Content safety guardrails on all student-facing AI output
- [ ] In-memory stores replaced with PostgreSQL-backed implementations
- [ ] All tests pass, backward compatibility maintained

---

## Stories (F-331 → F-345) — 15 stories, 4 phases

### Phase 1 — Application Layer (P1)

**F-331: Application Service Layer (Commands/Queries)**
- `app/commands/`: PlanGenerateCommand, TutorChatCommand, MaterialIngestCommand
- Each: validation, authorization, business logic, event emission
- Routers become thin HTTP layer delegating to handlers
- AC: 3 handlers operational. Business logic testable in isolation.

**F-332: Domain Events Infrastructure**
- DomainEvent base: event_id (uuid7), timestamp, aggregate_id, aggregate_type, payload
- Extend EventBus (Redis pub/sub) for domain events. DomainEventDispatcher with error isolation.
- Events: PlanGenerated, PlanApproved, SkillRated, TutorSessionStarted, MaterialIngested
- Handlers: audit log enrichment, analytics counter, cache invalidation
- AC: Events emitted on key actions. 3+ handlers. Events in logs. No sync blocking.

**F-333: Background Job Processing (arq)**
- Docker Compose service: `worker` (same image, different entrypoint)
- Jobs: batch embedding recomputation, report PDF generation, plan export
- Status: GET /jobs/{id} endpoint. Health check on worker.
- AC: Worker container runs. 2+ job types operational. Health check present.

### Phase 2 — API Maturity (P1)

**F-334: API Versioning (/v1/ prefix)**
- All endpoints under /v1/. X-API-Version: v1 response header.
- 301 redirects for old unversioned paths. Versioning policy in SYSTEM_DESIGN.md.
- AC: All endpoints versioned. Header present. Old paths redirect.

**F-335: Cursor-Based Pagination**
- CursorPage[T] generic: items, next_cursor, prev_cursor, has_more, total_count
- Base64-encoded cursor. Link headers (RFC 8288).
- Apply to: /runs, /v1/skills, /admin/audit-log, /plans
- AC: All list endpoints support cursor. Link header present. Backward compat with offset.

**F-336: Consolidate skills routers**
- /skills → 301 to /v1/skills. Deprecation in CHANGELOG with timeline.
- AC: Redirect works. No breaking change.

### Phase 3 — Agent Production Maturity (P1-P2)

**F-337: Prompt Version Registry**
- DB table: prompt_templates(id, name, version, content, variables, active, created_at)
- prompt_experiments(id, template_a_id, template_b_id, traffic_split, metrics_json)
- API: GET/POST /v1/prompts, POST /v1/prompts/{id}/activate, POST /v1/prompts/{id}/rollback
- Agents load active prompt from registry (fallback to hardcoded _prompts.py)
- AC: Prompts versioned in DB. Activation/rollback works. A/B split configurable.

**F-338: Per-Tenant Cost Tracking**
- DB table: usage_events(id, tenant_id, agent_name, model, tokens_in, tokens_out, cost_usd, created_at)
- tenant_budgets(tenant_id, monthly_limit_usd, alert_threshold_pct)
- SmartRouter records usage after each LLM call. API: GET /v1/usage?tenant_id=&period=
- Budget alerts: when threshold reached, log warning + optional SSE notification
- AC: All LLM calls tracked. Usage queryable. Budget alerts work.

**F-339: Content Safety Guardrails**
- Pydantic AI result validator pipeline: age-appropriate check, bias-free, PII output scrubbing, toxicity detection
- Configurable safety policy per agent role (tutor stricter than planner)
- Blocked outputs: logged with reason, fallback to safe generic response
- AC: Student-facing AI output passes safety checks. Blocked responses logged. Policy configurable.

**F-340: Semantic AI Caching**
- Redis cache for deterministic queries (curriculum alignment, skill lookups)
- Cache key: hash of (prompt_template_version + input_hash + model)
- Invalidation on prompt version change or model change
- Cache hit rate metric in diagnostics
- AC: Repeated curriculum queries cached. Hit rate visible. Invalidation works.

### Phase 4 — Data Layer & Cleanup (P2)

**F-341: PostgreSQL-Backed Persistent Stores**
- Replace: TraceStore → PgTraceStore, ReviewStore → PgReviewStore, ProgressStore → PgProgressStore, ObservabilityStore → PgObservabilityStore
- New tables with indexes and auto-cleanup (TTL via arq job)
- In-memory implementations kept for unit tests.
- AC: Stores survive restarts. APIs unchanged. Auto-cleanup configured.

**F-342: Embedding Dimension Consistency**
- Align config default to 1536 (MRL-reduced). Startup validation: config vs DB column.
- Document MRL strategy in SYSTEM_DESIGN.md.
- AC: Single dimension config. Startup check. No 3072/1536 confusion.

**F-343: Unified InMemoryStore[K,V] Base**
- Generic with TTL, max_size, LRU eviction. Refactor remaining in-memory stores.
- AC: No unbounded memory growth. Eviction tested.

**F-344: Expose session_factory on PgVectorStore**
- Public @property replacing getattr(vs, "_session_factory") pattern (3 occurrences).
- AC: No private attribute access. Property documented.

**F-345: Document global mutable state**
- Audit all 14 `global _*` patterns. Document as intentional (single-process ASGI) or refactor to DI.
- AC: All global state documented or refactored.

---

## Dependencies
- Sprint 30 should complete first (refactored app.py/auth.py make this cleaner)
- F-333 (arq worker) needs Redis (already in Compose)
- F-341 (persistent stores) needs new migration
- F-337 (prompt registry) needs migration

## Risks
- F-331: Service layer touches high-traffic code; careful integration testing
- F-337: Prompt registry migration from hardcoded to DB needs graceful fallback
- F-339: Content safety false positives could block legitimate educational content

## Micro-tasks: ~50 (15 stories × ~3.3 tasks each)
