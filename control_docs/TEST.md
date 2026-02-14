# Test Strategy

## Frameworks
- **Backend:** pytest 8.x + pytest-asyncio 0.24.x + httpx (async client)
- **Frontend:** Vitest + React Testing Library + @testing-library/jest-dom
- **E2E:** Playwright (headless in CI)
- **A11y:** axe-core + pa11y + Lighthouse
- **Security:** trivy (container), pip-audit (Python), pnpm audit (Node)

## Coverage Targets
- Pre-MVP (current): 1,993+ backend tests (1,743 runtime + 250 agents), all passing
- Frontend: 770+ tests, all passing (90 test suites)
- E2E: 3 Playwright golden path specs + 8 visual regression + axe-core a11y audit
- Agent eval: 15 golden test sets (Planner/QualityGate/Tutor) + rubric scoring
- Post-MVP: >= 90% on touched code (hard gate)

## Test Layers

| Layer | Scope | Tool | Doubles |
|-------|-------|------|---------|
| Unit | Domain entities, validators, exports, i18n | pytest / Vitest | Ports mocked at boundary |
| Integration | Adapters vs real Postgres/Redis | pytest + Docker Compose | None (real services) |
| E2E | Full pipeline, tutor chat, SSE streaming | Playwright + API | None |
| A11y | WCAG AAA compliance, keyboard nav | axe-core + Lighthouse | N/A |

## Test Database
Integration tests use Postgres container from Docker Compose.
Each test run applies migrations via Alembic to fresh schema.
SQLite fallback for fast unit tests (vector ops skipped).

## How to Run
```bash
cd runtime && uv run pytest -v --cov                            # Backend tests
cd agents && uv run pytest -v                                    # Agents tests
cd runtime && uv run pytest -m live_llm -v --timeout=120         # Live API (65 tests, keys required)
cd frontend && pnpm test && pnpm test:coverage                   # Frontend tests
cd frontend && pnpm exec playwright test                         # E2E + a11y
cd runtime && uv run ruff check . && uv run mypy .               # Lint + typecheck
cd frontend && pnpm lint && pnpm exec tsc --noEmit               # Frontend lint
docker compose up -d --build && docker compose exec api uv run pytest -v  # Docker (source of truth)
```

## Test Matrix

| Area | Unit | Integration | E2E |
|------|------|-------------|-----|
| Domain entities, validators, exports, i18n | Yes | - | - |
| Middleware (rate limiter, sanitization, tenant, metrics) | Yes | - | - |
| Resilience (circuit breaker, retry, idempotency, SSE) | Yes | - | - |
| Pydantic AI agents + Skill Registry | Yes (250) | Yes (10 live_llm) | - |
| API endpoints, DB CRUD, RAG pipeline | - | Yes | - |
| LLM adapters (Anthropic/OpenAI/Gemini) | - | Yes (live_llm) | - |
| Frontend components (770+ Vitest) | Yes | - | - |
| Full plan pipeline, tutor chat, SSE streaming | - | - | Yes |
| WCAG AAA, keyboard nav, visual regression | - | - | Yes (axe + Playwright) |
