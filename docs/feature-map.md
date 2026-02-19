# AiLine Feature Map

**190+ features** organized into 12 capability areas. Each feature links to its ID in `control_docs/FEATURES.md`.

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

Docker Compose stack, 3,300+ tests, CI pipeline, observability, health checks, and documentation.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-001 | Hexagonal Architecture | Domain/Ports/Adapters with DI container |
| F-007 | Observability Foundation | structlog JSON + OTEL trace context |
| F-014 | Frontend Dashboard | Next.js 16, Glass Box pipeline viewer |
| F-030 | Docker Compose Stack | One-command local dev (4 services) |
| F-032 | React Compiler 1.0 | Auto-memoization enabled |
| F-040 | Full Test Coverage | 2,125 backend + 962 frontend tests |
| F-041 | Docker Compose Full Stack | API + DB + Redis + Frontend, healthchecks |
| F-042 | GitHub Actions CI | lint, typecheck, test pipeline |
| F-052 | Live API Integration Tests | 65 live_llm tests (Anthropic/OpenAI/Gemini) |
| F-061 | Prometheus Metrics | /metrics endpoint, Counter, Histogram |
| F-070 | DI Container Lifecycle | health_check, close, validate |
| F-071 | Observability Spans | span_context, timed_operation, log_llm_call |
| F-072 | Dev-Mode Safety Guard | Startup fail if production + dev mode |
| F-073 | Readiness Probe | /health/ready (DB+Redis checks) |
| -- | 60 ADRs | Architecture Decision Records (ADR-001 through ADR-060) |

## G. Sprint 13 -- Final Polish & Wow Factor (26 features)

Pipeline transparency, observability, quality gate hardening, and frontend UX polish.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-074 | Agent Trace Viewer API | GET /traces/{run_id}, node execution timeline |
| F-075 | SmartRouter Route Rationale | "Why this model?" in SSE stage.started |
| F-076 | QualityGate Hard Constraints | 4 deterministic validators |
| F-077 | RAG-Grounded Quoting | 1-3 source quotes with confidence |
| F-078 | Observability Dashboard API | LLM latency p50/p95, CB state, token usage |
| F-079 | Standards Alignment Evidence | Teacher handout with BNCC/CCSS/NGSS/Bloom |
| F-080 | Theme Morphing Animation | CSS transition-colors 500ms |
| F-081 | Magic Layout Tabs | Motion layoutId sliding indicator |
| F-082 | Skeleton Shimmer Loading | animate-pulse with Suspense fallbacks |
| F-083 | Staggered Dashboard Entrance | Motion staggerChildren 0.12s |
| F-084 | Bento Grid Dashboard | CSS Grid responsive layout |
| F-085 | Streaming Typewriter Effect | Token-by-token SSE rendering |
| F-086 | Toast Notifications | sonner with undo capability |
| F-087 | Interactive Empty States | text-balance with CTA buttons |
| F-088 | Webcam Active Ring | Confidence-based border glow |
| F-089 | Export Paper Fold | motion.article rotateY animation |
| F-090 | Degradation Panel | Chaos simulation with status banner |
| F-091 | Privacy Data Panel | LGPD/FERPA compliance display |
| F-092 | Cognitive Load Meter | 3-factor heuristic with suggestions |
| F-093 | Agent Trace Viewer UI | Collapsible LangGraph timeline |
| F-094 | SmartRouter Rationale Card | 5-weight breakdown badge |
| F-095 | Observability Dashboard UI | Recharts sparkline + charts |
| F-096 | Enhanced Error Boundary | Branded error.tsx, SSE reconnect |
| F-097 | Full i18n Coverage | All components in 3 locales |
| F-098 | Playwright E2E Golden Paths | 3 specs + axe-core a11y |
| F-099 | Judge Artifacts | 4 docs: arch, features, demo, packet |

## H. Sprint 14 -- State-of-the-Art Hardening (21 features)

Security, observability, agent evaluation, and production readiness.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-100 | JWT RS256/ES256 Verification | Asymmetric JWT, JWKS, algorithm pinning |
| F-101 | JWT Security Test Suite | 57 tests: forged, expired, replay |
| F-102 | Prompt Injection Defenses | Trust scoring, retrieval sanitization |
| F-103 | Structured Audit Logging | Admin/content/auth event logging |
| F-104 | OpenTelemetry Tracing | Spans for FastAPI/SQLAlchemy/LLM/pipeline |
| F-105 | RFC 7807 Problem Details | application/problem+json errors |
| F-106 | DB Pool Tuning | pool_size=10, HNSW m=16/ef=128 |
| F-107 | Cache Headers | Curriculum API 1h cache |
| F-108 | Container Refactoring | 476->278 LOC split |
| F-109 | Agent Eval Harness | 15 golden sets with rubric scoring |
| F-110 | Eval Rubric System | Multi-dimension scoring, regression |
| F-111 | RAG Provenance Diagnostics | Confidence classification |
| F-112 | RAG Diagnostics API | GET /rag/diagnostics/{run_id} |
| F-113 | Sign Language Worker Fix | MediaPipe feature-gated loading |
| F-114 | Playwright webServer Config | Self-contained E2E |
| F-115 | Visual Regression Tests | 8 screenshot comparisons |
| F-116 | View Transitions API | CSS route morphing |
| F-117 | Dynamic OG Images | next/og ImageResponse |
| F-118 | PWA Manifest | Install prompt, icons, shortcuts |
| F-119 | Recharts Keyboard Accessibility | Tab through data, aria-live |
| F-120 | Optimistic UI | useOptimistic hook |

## I. Sprint 16 -- Hackathon Victory Sprint (5 features)

Transformation scorecard, teacher review workflow, student progress tracking, UX micro-polish, and conversation review.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-121 | Transformation Scorecard | 9-metric trust card computed as LangGraph terminal node |
| F-122 | HITL Teacher Review Panel | Approve/reject/revision workflow + pending reviews badge |
| F-123 | Student Progress Dashboard | Mastery tracking, standards heatmap, class overview |
| F-124 | UX Micro-Polish | 8 nav items, "Powered by Claude Opus 4.6" badge, empty state + skeleton components |
| F-125 | Conversation Review | Scrollable tutor transcript with per-turn flagging |

## J. Sprint 17 -- Hackathon Final Push (10 features)

Settings page, guided demo mode, trust panel, materials upload, live dashboard, tutor persistence, system status, lint cleanup, and dead code removal.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-126 | Settings Page | AI model, language, accessibility, about with glass morphism |
| F-127 | Guided Demo Mode | ?demo=true, auto-fill wizard, tooltip overlay, 3 guided steps |
| F-128 | Trust & Transparency Panel | Quality report, scorecard, model provenance, decision badge |
| F-129 | Materials Upload Page | File upload, material listing with tags, glass card grid |
| F-130 | Live Dashboard Stats | API-wired stats, plan history, loading skeleton |
| F-131 | Tutor Persistence & Review | Zustand persist, ConversationReview tab |
| F-132 | System Status Indicator | TopBar health check badge with dropdown |
| F-133 | Ruff Lint Zero | Fixed 11 lint errors (RUF009 + UP038) |
| F-134 | Orphan Component Integration | Wired 4 orphaned components into pages |
| F-135 | Dead Code Cleanup | Removed 5 duplicate/unused components |

## K. Sprint 18 -- Impact Sweep & State-of-the-Art Polish (5 features)

View Transitions, loading skeletons, mobile navigation, and HITL API test coverage.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-136 | View Transition Theme Morphing | Circular clip-path reveal from click origin on persona/theme switch |
| F-137 | Loading Skeletons for All Pages | 8 loading.tsx files with page-specific skeleton layouts |
| F-138 | Mobile Nav Overflow Menu | "More" popover with 4 overflow items, AnimatePresence animation |
| F-139 | HITL API Test Coverage | 51 new tests: Progress (16), Plan Review (18), Tutor Transcript/Flag (17) |
| F-140 | PreferencesPanel View Transition | Theme switch uses View Transitions API for circular reveal |

## L. Sprint 19 — State-of-the-Art Final Sweep (5 features)

Command palette, code refactoring, motion dedup, and type safety improvements.

| ID | Feature | Key Details |
|----|---------|-------------|
| F-141 | Command Palette (Cmd+K) | Fuzzy search, 9 navigation pages, quick actions, theme/language switching, ARIA combobox |
| F-142 | Plan Nodes Refactor | 764 LOC split into 5 focused modules with barrel re-export |
| F-143 | Plan Flow Refactor | 757 LOC split into orchestrator + wizard-steps + result-display |
| F-144 | Shared Motion Variants | Extracted stagger animations from 9 components into shared lib |
| F-145 | SSE Type Safety | Replaced `as never` casts with proper domain type assertions |

---

## Summary

| Capability Area | Feature Count | Highlights |
|----------------|---------------|------------|
| A. AI-Powered Learning | 16 | 4 Pydantic AI agents, SmartRouter, RAG, 4 curriculum standards |
| B. Universal Accessibility | 13 | WCAG AAA, 9 themes, Libras sign language, STT/TTS |
| C. Real-Time Pipeline | 10 | 14 SSE event types, replay, terminal guarantee |
| D. Data and Security | 14 | Tenant isolation, circuit breaker, rate limiting, LGPD/FERPA |
| E. Multi-Language | 5 | 3 languages, BNCC/CCSS/NGSS/ELA standards |
| F. Developer Experience | 15 | 3,300+ tests, Docker, CI, observability, 60 ADRs |
| G. Sprint 13 Polish | 26 | Pipeline transparency, observability UI, UX animations |
| H. Sprint 14 Hardening | 21 | JWT security, OTel tracing, agent eval, visual regression |
| I. Sprint 16 Victory | 5 | Scorecard, teacher review, progress dashboard, UX polish |
| J. Sprint 17 Final Push | 10 | Settings, demo mode, trust panel, materials, live stats |
| K. Sprint 18 Impact Sweep | 5 | View Transitions, loading skeletons, mobile nav, HITL tests |
| L. Sprint 19 Final Sweep | 5 | Command Palette, code refactoring, motion dedup, type safety |
| **Total** | **145** | |
