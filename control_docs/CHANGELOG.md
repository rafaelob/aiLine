# Changelog
All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.1.1] - 2026-02-14 (Excellence Sweep)

### Fixed
- All 114 mypy type errors resolved (0 errors in 155 source files)
- Raw LangGraph state no longer leaked to client in POST /plans/generate
- Tool bridge now catches and returns errors instead of propagating raw exceptions
- useTranslations→getTranslations in server components (plans, tutors pages)
- Nested `<main>` removed from sign-language page (prevents WCAG landmark violation)
- Sidebar/MobileNav: `<a href>`→`<Link>` for client-side navigation
- Cognitive curtain: hover/focus restores interactivity (was blocking all nav)
- Preferences panel animations respect user's reducedMotion preference
- Ruff: F401, I001, UP017, E501 all fixed (0 lint errors across runtime + agents)

### Improved
- All 4 agent model IDs configurable via env vars with `provider:model` format (Pydantic AI 1.58 compliant)
- Default executor model changed to `google-gla:gemini-3-flash-preview` (cost-efficient)
- Pydantic AI DeprecationWarning eliminated (model names now use required provider prefix)
- Vitest 4 config migrated: deprecated `poolOptions` → top-level `maxWorkers`/`execArgv`
- Gemini adapter default updated to `gemini-3-flash-preview` (was `gemini-2.5-flash`)
- LLM adapters defensively strip provider prefix (e.g. `anthropic:claude-opus-4-6` → `claude-opus-4-6`)
- Cost tracking includes Gemini 3 Pro/Flash pricing
- README.md rewritten for hackathon judges (badges, Mermaid diagrams, metrics)
- Accessibility persona themes enhanced with meaningful UX adaptations
- Quality decision persisted in LangGraph workflow state for auditability
- Test setup: getTranslations mock added for async server component testing

## [0.1.0] - 2026-02-13 (Hackathon Release)

### Added
- Hexagonal architecture (Ports-and-Adapters) with domain, ports, adapters, application layers
- 4 Pydantic AI 1.58 typed agents (Planner, Executor, QualityGate, Tutor) via ailine_agents package (ADR-059)
- LangGraph workflows: plan pipeline (parallel fan-out, quality gate, refine loop) + tutor chat
- SmartRouter multi-LLM routing: weighted scoring, hard overrides, escalation ladder (ADR-049)
- 3 LLM adapters (Anthropic, OpenAI, Gemini) + FakeLLM/FakeSTT/FakeTTS for CI (ADR-051)
- FastAPI 0.129 with 8 routers, SSE 14 typed events, RFC 7807 error model
- SQLAlchemy 2.x async (11 tables, UUID v7), pgvector HNSW, composite FK tenant safety (ADR-053)
- RAG pipeline: material ingestion, embeddings (Gemini 1536d MRL), query with provenance diagnostics
- Curriculum alignment: BNCC, CCSS Math, CCSS ELA, NGSS with Bloom's Taxonomy filtering
- Next.js 16 frontend: React 19, Tailwind 4, React Compiler, 9 WCAG AAA themes, 3 locales
- Accessibility: VLibras, MediaPipe sign language, Whisper STT, ElevenLabs TTS, OCR
- Wow features: Cognitive Curtain, Bionic Reading, TTS Karaoke, Glass Box Pipeline Viewer
- Security: JWT RS256/ES256 + JWKS (57 tests), prompt injection defenses, audit logging, CSP/HSTS
- Structural tenant isolation in all vector stores (ADR-060), centralized authz policy
- OpenTelemetry tracing, Prometheus metrics, circuit breaker, retry with backoff
- SSE replay (Redis ZSET), RunContext terminal guarantee, asyncio.Lock thread safety
- Docker Compose (PostgreSQL 16 + pgvector, Redis, API, Frontend) with healthchecks
- 1,993+ backend tests, 770+ frontend tests, 35+ E2E Playwright, 65 live API tests
- 60 ADRs, 120 features, 11 skills, demo mode with 3 cached scenarios
