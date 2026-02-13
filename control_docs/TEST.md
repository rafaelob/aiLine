# Test Strategy

## Frameworks
- **Backend:** pytest 8.x + pytest-asyncio 0.24.x + httpx (async client)
- **Frontend:** Vitest + React Testing Library + @testing-library/jest-dom
- **E2E:** Playwright (headless in CI)
- **A11y:** axe-core + pa11y + Lighthouse
- **Security:** trivy (container), pip-audit (Python), pnpm audit (Node)

## Coverage Targets
- Pre-MVP (current): 1330+ backend tests (1090+ runtime + 235 agents), all passing
- Frontend: 717 tests, all passing (84 test suites)
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
| Domain entities | Yes | - | - |
| Accessibility validator | Yes | - | - |
| Export renderer (10 variants) | Yes | - | - |
| Curriculum search | Yes | Yes | - |
| i18n translations | Yes | - | - |
| API endpoints | - | Yes | - |
| Database CRUD | - | Yes | - |
| RAG pipeline | - | Yes | - |
| LLM adapters | - | Yes (@pytest.mark.live_llm) | - |
| Pydantic AI agents (ailine_agents) | Yes (167) | Yes (10 live_llm) | - |
| Skill Registry (parse, scan, prompt) | Yes (18) | - | - |
| SSE replay store | Yes | - | - |
| RunContext terminal SSE | Yes | - | - |
| Full plan pipeline | - | - | Yes |
| Tutor chat flow | - | - | Yes |
| SSE streaming | - | Yes | Yes |
| Frontend components | Yes (Vitest) | - | - |
| WCAG AAA compliance | - | - | Yes (axe-core) |
| Keyboard navigation | - | - | Yes (Playwright) |
| Rate limiter middleware | Yes | - | - |
| Prometheus metrics | Yes | - | - |
| Input sanitization | Yes | - | - |
| Tenant context middleware | Yes | - | - |
| Observability spans | Yes | - | - |
| Circuit breaker + retry | Yes | - | - |
| Idempotency guard | Yes | - | - |
| Readiness probe | - | Yes | - |
