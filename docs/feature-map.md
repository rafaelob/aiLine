# AiLine Feature Map

**73 features** organized into 6 capability areas. Each feature links to its ID in `control_docs/FEATURES.md`.

---

## A. AI-Powered Learning (16 features)

Intelligent lesson planning, adaptive tutoring, curriculum alignment, and content personalization powered by multi-LLM orchestration.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-004 | LangGraph Workflow Orchestration | Parallel fan-out topology, plan pipeline |
| F-009 | Multi-Embedding Service | Gemini/OpenAI 1536d MRL + FakeEmbeddings |
| F-010 | Vector Store (pluggable) | pgvector HNSW, ChromaDB, InMemory |
| F-011 | Material Ingestion | 512t chunks, 64 overlap, embed, index |
| F-012 | RAG Query | Retrieve relevant chunks for plans + tutoring |
| F-013 | Curriculum Standards | BNCC (Brazil) + CCSS/NGSS (USA) + grade mapping |
| F-017 | Tutor Agents | LangGraph workflow, session mgmt, Socratic playbooks |
| F-029 | SmartRouterAdapter | Weighted routing (0.25/0.25/0.25/0.15/0.10) |
| F-036 | Direct Anthropic Tool Calling | Executor via direct API, no SDK wrapper |
| F-038 | Tiered Quality Gate | Structural checks + heuristic scoring (0-100) |
| F-050 | SmartRouter Pure Decision | `compute_route()` with RouteFeatures/RouteDecision |
| F-053 | ailine_agents Package | 4 Pydantic AI 1.58 typed agents + tool/model bridges |
| F-054 | Model Selection Bridge | SmartRouter tier -> Pydantic AI Model mapping |
| F-055 | Custom Skill Registry | 11 SKILL.md files, YAML frontmatter, prompt fragments |
| F-056 | CCSS ELA Curriculum | 46 Common Core ELA K-8 standards |
| F-057 | Bloom's Taxonomy Filtering | bloom_level on all 4 curriculum systems |

## B. Universal Accessibility (13 features)

WCAG AAA compliance, 9 persona-based themes, sign language (Libras), speech interfaces, and inclusive design patterns.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-015 | WCAG AAA Design System | 9 persona themes via CSS custom properties |
| F-019 | Sign Language Input | MediaPipe hand landmarks for Libras (4 gestures) |
| F-020 | Sign Language Output | VLibras 3D avatar widget (government CDN) |
| F-021 | Speech-to-Text | Whisper V3 Turbo + OpenAI cloud STT |
| F-022 | Text-to-Speech | ElevenLabs primary + FakeTTS for CI |
| F-023 | OCR + Image Description | Opus 4.6 vision for alt-text + OCR |
| F-024 | Persona Toggle | Live content morphing with CSS var swap |
| F-025 | Simulate Disability | Empathy Bridge (dyslexia, tunnel vision, color blindness) |
| F-046 | Web Worker Sign Language | MediaPipe/MLP off main thread |
| F-047 | VLibras Accessibility | aria-hidden, skip-link for keyboard users |
| F-048 | Reduced Motion | OS sync + localStorage override |
| F-049 | Low-Distraction Mode | React 19 Activity for animation suppression |
| F-058 | Libras STT ML Pipeline | Training scaffold, TF.js MLP, gloss->LLM |

## C. Real-Time Pipeline (10 features)

Server-Sent Events streaming with replay, typed event contracts, terminal guarantees, and LangGraph-based orchestration.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-002 | Multi-LLM Port Protocols | ChatLLM with Anthropic, OpenAI, Gemini adapters |
| F-005 | FastAPI API Layer | 8 routers, CORS, streaming support |
| F-016 | SSE Pipeline Streaming | 14 typed events, {run_id, seq, ts, type, stage, payload} |
| F-027 | Accessibility Twin | Tabbed View with diff highlights |
| F-028 | Score Gauge | Radial chart 0-100, color interpolation, spring animation |
| F-031 | Demo Mode | 3 scenarios, cached golden path, DemoModeMiddleware |
| F-043 | SSE Event Replay | InMemory + Redis ZSET (score=seq, TTL 30min) |
| F-044 | Terminal SSE Guarantee | RunContext async context manager, exactly-once terminal |
| F-045 | ThemeContext MutationObserver | Recharts/Canvas theme reactivity |
| F-051 | SSE Emitter Thread Safety | asyncio.Lock for parallel LangGraph branches |

## D. Data and Security (14 features)

Tenant isolation, encryption, rate limiting, circuit breaker, input sanitization, and compliance (LGPD/FERPA).

| ID | Feature | Key Details |
|----|---------|-------------|
| F-003 | Pydantic Settings Config | Multi-provider env-driven configuration |
| F-008 | Database Layer | SQLAlchemy 2.x async, Alembic, UUID v7, 11 tables |
| F-033 | HTML Sanitization | DOMPurify 3.3.1 for safe export rendering |
| F-037 | FakeLLM Test Adapter | Deterministic CI outputs, zero external calls |
| F-039 | Composite FK Tenant Safety | DB-level cross-tenant prevention |
| F-060 | Rate Limiter Middleware | Sliding window, 429+Retry-After, X-RateLimit-* |
| F-062 | Security Headers | CSP, X-Frame-Options, Referrer-Policy |
| F-063 | Request ID Middleware | X-Request-ID + structlog correlation |
| F-064 | Tenant Context Middleware | JWT sub + X-Teacher-ID dev mode |
| F-065 | Input Sanitization | sanitize_prompt, validate_teacher_id |
| F-066 | Circuit Breaker | 5 fail -> 60s open -> half-open -> reset |
| F-067 | Retry with Exponential Backoff | 3 attempts, factor 2.0, transient-only |
| F-068 | Workflow Timeout | 300s max with graceful degradation |
| F-069 | Idempotency Guard | Duplicate plan generation prevention |

## E. Multi-Language and Curriculum (5 features)

Full-stack internationalization (3 languages), curriculum standard alignment (4 frameworks), and export variants.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-018 | i18n (Full Stack) | English, Portuguese (BR), Spanish via next-intl |
| F-006 | Domain Entities | StudyPlan, Material, Tutor, Curriculum, Accessibility |
| F-026 | Export Viewer | Side-by-side original vs adapted comparison |
| F-034 | Tutor ChatBlock | Structured message components |
| F-059 | SKILL.md Frontmatter Migration | 11 skills with metadata + compatibility |

## F. Developer Experience and Operations (15 features)

Docker Compose stack, 1800+ tests, CI pipeline, observability, health checks, and documentation.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-001 | Hexagonal Architecture | Domain/Ports/Adapters with DI container |
| F-007 | Observability Foundation | structlog JSON + OTEL trace context |
| F-014 | Frontend Dashboard | Next.js 16, Glass Box pipeline viewer |
| F-030 | Docker Compose Stack | One-command local dev (4 services) |
| F-032 | React Compiler 1.0 | Auto-memoization enabled |
| F-040 | Full Test Coverage | 1527+ backend + 331 frontend tests |
| F-041 | Docker Compose Full Stack | API + DB + Redis + Frontend, healthchecks |
| F-042 | GitHub Actions CI | lint, typecheck, test pipeline |
| F-052 | Live API Integration Tests | 65 live_llm tests (Anthropic/OpenAI/Gemini) |
| F-061 | Prometheus Metrics | /metrics endpoint, Counter, Histogram |
| F-070 | DI Container Lifecycle | health_check, close, validate |
| F-071 | Observability Spans | span_context, timed_operation, log_llm_call |
| F-072 | Dev-Mode Safety Guard | Startup fail if production + dev mode |
| F-073 | Readiness Probe | /health/ready (DB+Redis checks) |
| -- | 59 ADRs | Architecture Decision Records (ADR-001 through ADR-059) |

---

## Summary

| Capability Area | Feature Count | Highlights |
|----------------|---------------|------------|
| A. AI-Powered Learning | 16 | 4 Pydantic AI agents, SmartRouter, RAG, 4 curriculum standards |
| B. Universal Accessibility | 13 | WCAG AAA, 9 themes, Libras sign language, STT/TTS |
| C. Real-Time Pipeline | 10 | 14 SSE event types, replay, terminal guarantee |
| D. Data and Security | 14 | Tenant isolation, circuit breaker, rate limiting, LGPD/FERPA |
| E. Multi-Language | 5 | 3 languages, BNCC/CCSS/NGSS/ELA standards |
| F. Developer Experience | 15 | 1800+ tests, Docker, CI, observability, 59 ADRs |
| **Total** | **73** | |
