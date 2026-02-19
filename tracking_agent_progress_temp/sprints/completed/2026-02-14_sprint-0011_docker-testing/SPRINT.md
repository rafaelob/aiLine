# Sprint 0011 — Docker + Testing

**Status:** completed | **Date:** 2026-02-14
**Goal:** Full Docker Compose stack (API + Frontend + Postgres/pgvector + Redis),
comprehensive test suite (unit + integration + E2E), CI/CD with GitHub Actions.

---

## Hackathon Priority

> Based on expert consultation (Gemini-3-Pro-Preview), Sprint 11 is **OPTIONAL**
> for the hackathon. Docker+Testing just needs to run on localhost for demo.
> However, having Docker Compose working is still valuable for consistent setup
> and for judges who want to run the project.

**Priority levels within this sprint:**

| Priority | Scope | Rationale |
|----------|-------|-----------|
| **P0 (must-have)** | Docker Compose with Postgres+pgvector (already partially done in Sprint 2) | Judges need one command to bring up infra |
| **P1 (should-have)** | Unit tests for domain layer, API integration tests | Proves correctness of core logic |
| **P2 (nice-to-have)** | Full CI pipeline, frontend tests, E2E tests | Polish for the repo; judges unlikely to check CI |
| **P3 (optional)** | Full Docker stack with frontend container | Frontend runs fine via `pnpm dev` for demo |

---

## Scope & Acceptance Criteria

A single `docker compose up --build` must bring up all four services (Postgres with
pgvector, Redis, Python API, Next.js frontend) with health checks, private
networking, and volume persistence. The backend must have unit tests (>=85% on
touched code), integration tests against real Postgres/Redis in Docker, and an E2E
pipeline test. The frontend must have Vitest component/hook/store tests (>=75%).
A GitHub Actions CI workflow must run lint, typecheck, unit tests, integration tests
(via Docker Compose), and image builds on every push/PR to main.

---

## Architecture

- **Docker Compose**: Single `docker-compose.yml` at repository root with four
  services, one bridge network, and one named volume.
- **Multi-stage builds**: Builder stage (install dependencies + compile) followed by
  a minimal runtime stage (non-root user, no dev dependencies, explicit healthcheck).
- **Test in Docker**: `docker compose run --rm api uv run pytest` is the source of
  truth for backend tests. Host-executed tests are acceptable for development but
  Docker is the final gate.
- **CI**: GitHub Actions with five sequential stages -- lint, typecheck, unit test,
  integration test (Docker Compose), and Docker image build. Caching for uv, pnpm,
  and Docker layers.

**Network topology:**
```
                     +---------+
                     | frontend|:3000
                     +----+----+
                          |
                     +----+----+
          +----------+   api   |:8000
          |          +----+----+
          |               |
     +----+-----+    +----+-----+
     |    db     |    |  redis   |
     | (pgvector)|    |  (7-alp) |
     | :5432     |    |  :6379   |
     +-----------+    +----------+
         [ailine-internal network]
```

---

## Stories

### S11-001: Docker Compose Full Stack

> **Hackathon note:** For the hackathon, the API + Postgres + Redis stack from
> Sprint 2 is sufficient. Frontend runs directly via `pnpm dev` (faster iteration
> than Docker build). Full frontend Docker build is **P3** -- nice for presentation
> but not needed for demo.

**Description:** Complete Docker Compose configuration with all services, health
checks, private bridge network, volume persistence, dependency ordering, and
non-root runtime users. Includes multi-stage Dockerfiles for both API and frontend.

**Files:**
- `docker-compose.yml` (new: full stack definition)
- `runtime/Dockerfile` (new: multi-stage Python build)
- `frontend/Dockerfile` (new: multi-stage Node.js build)
- `.dockerignore` (new: exclude build artifacts, venvs, .git)
- `.env.example` (update: add `COMPOSE_PROJECT_NAME`, `AILINE_DB_PASSWORD`)

**Docker Compose definition:**
```yaml
services:
  db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: ailine
      POSTGRES_USER: ailine
      POSTGRES_PASSWORD: ${AILINE_DB_PASSWORD:-ailine_dev}
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ailine"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks: [ailine-internal]

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks: [ailine-internal]

  api:
    build:
      context: ./runtime
      dockerfile: Dockerfile
      target: runtime
    ports: ["8000:8000"]
    env_file: .env
    environment:
      AILINE_DB__URL: postgresql+asyncpg://ailine:${AILINE_DB_PASSWORD:-ailine_dev}@db:5432/ailine
      AILINE_REDIS__URL: redis://redis:6379/0
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks: [ailine-internal]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: runtime
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
    depends_on:
      api: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3000').then(r => process.exit(r.ok ? 0 : 1))"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks: [ailine-internal]

volumes:
  pgdata:

networks:
  ailine-internal:
    driver: bridge
```

**API Dockerfile (multi-stage):**
```dockerfile
# --- Builder ---
FROM python:3.13-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY . .

# --- Runtime ---
FROM python:3.13-slim AS runtime
RUN groupadd -r ailine && useradd -r -g ailine -d /app ailine
WORKDIR /app
COPY --from=builder /app /app
USER ailine
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
CMD ["uv", "run", "uvicorn", "ailine_runtime.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile (multi-stage):**
```dockerfile
# --- Builder ---
FROM node:24-alpine AS builder
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# --- Runtime ---
FROM node:24-alpine AS runtime
RUN addgroup -S ailine && adduser -S -G ailine -h /app ailine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
USER ailine
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD node -e "fetch('http://localhost:3000').then(r => process.exit(r.ok ? 0 : 1))"
CMD ["node", "server.js"]
```

**Acceptance Criteria:**
- [ ] Services: `db` (pgvector/pgvector:pg17), `redis` (redis:7-alpine),
      `api` (Python 3.13 slim), `frontend` (Node 24 alpine)
- [ ] All four services have explicit healthchecks
- [ ] Private bridge network `ailine-internal` for all inter-service communication
- [ ] Named volume `pgdata` for Postgres data persistence
- [ ] API waits for healthy Postgres + Redis via `depends_on` conditions
- [ ] Frontend waits for healthy API via `depends_on` condition
- [ ] Non-root runtime user (`ailine`) in both API and frontend containers
- [ ] `.dockerignore` excludes: `node_modules`, `__pycache__`, `.venv`, `.git`,
      `.env`, `*.pyc`, `.next` (in runtime context)
- [ ] `docker compose up --build` brings all services to healthy state in < 60s
- [ ] `COMPOSE_PROJECT_NAME=ailine` pinned in `.env.example`
- [ ] Host port collision check documented in `.env.example` comments
- [ ] No `container_name` directives (allows Compose scaling)
- [ ] No `:latest` image tags

---

### S11-002: Backend Unit Tests (>=85% on touched code)

> **Hackathon note (P1):** Focus on domain layer tests that prove correctness:
> - Accessibility validator scoring (all categories)
> - Export renderer (verify HTML structure, ARIA landmarks for all 10 variants)
> - Curriculum search (BNCC + CCSS + grade mapping)
> - i18n (all locales, missing keys fallback, interpolation)
>
> Coverage target: >= 75% on domain + accessibility modules.

**Description:** Unit tests for domain entities, shared layer (config, errors,
i18n, observability), and service logic. These tests run without any external
dependencies -- all ports are test doubles (fakes or mocks) at I/O boundaries.

**Files:**
- `runtime/tests/__init__.py` (new)
- `runtime/tests/conftest.py` (new: shared fixtures)
- `runtime/tests/unit/__init__.py` (new)
- `runtime/tests/unit/test_entities.py` (new: domain entity tests)
- `runtime/tests/unit/test_config.py` (new: Settings loading tests)
- `runtime/tests/unit/test_errors.py` (new: error hierarchy tests)
- `runtime/tests/unit/test_i18n.py` (new: translation lookup tests)
- `runtime/tests/unit/test_observability.py` (new: logging setup tests)
- `runtime/tests/unit/test_container.py` (new: DI container tests)
- `runtime/tests/unit/test_sse.py` (new: SSE format/heartbeat tests)
- `runtime/tests/unit/test_event_bus.py` (new: InMemoryEventBus tests)

**Test coverage targets by module:**
| Module | Target | Key scenarios |
|--------|--------|---------------|
| `domain/entities/*.py` | >=90% | Construction with valid/invalid data, serialization round-trip, enum completeness, field defaults |
| `shared/config.py` | >=85% | Load from env vars, nested sub-configs, alias choices, missing required keys, defaults |
| `shared/errors.py` | >=90% | Hierarchy isinstance checks, code propagation, details dict, string repr |
| `shared/i18n.py` | >=85% | Key lookup, locale fallback chain (pt-BR -> pt -> en), missing key behavior, interpolation |
| `shared/observability.py` | >=80% | Logger creation, JSON mode toggle, event logging with bound context |
| `shared/container.py` | >=85% | Build with valid settings, port resolution, frozen immutability |
| `api/streaming/sse.py` | >=90% | Event format correctness, heartbeat interval, merge generators |
| `adapters/events/inmemory_bus.py` | >=90% | Publish/subscribe, multiple handlers, handler exception isolation |

**Acceptance Criteria:**
- [ ] Domain entities: construction with valid data, rejection of invalid data
      (e.g., negative minutes), serialization via `.model_dump()` /
      `.model_dump_json()`, all enum values covered
- [ ] Config: `Settings()` loads from environment, `LLMConfig`, `EmbeddingConfig`,
      `DatabaseConfig`, `RedisConfig` sub-configs resolve correctly, alias choices
      for API keys work, missing required keys raise `ValidationError`
- [ ] Errors: `AiLineError` base class, subclass hierarchy (`PlanGenerationError`,
      `ValidationError`, `ProviderError`, `RateLimitError`, `NotFoundError`), code
      and details propagation
- [ ] i18n: `t("key", "pt-BR")` returns Portuguese string, `t("key", "de")`
      falls back to English, missing key returns key itself or placeholder
- [ ] Observability: `configure_logging(json_output=True)` configures structlog,
      `get_logger("test")` returns a bound logger, `log_event("test", k="v")`
      emits structured output
- [ ] >=85% line coverage on tested modules (measured via `pytest-cov`)
- [ ] All tests pass in Docker: `docker compose run --rm api uv run pytest tests/unit -v --cov`
- [ ] Tests complete in < 30s (no I/O, no network)

---

### S11-003: Backend Integration Tests

**Description:** Integration tests against real Postgres (with pgvector) and Redis
using Docker Compose services. These tests validate the database layer (ORM models,
UnitOfWork, repositories), API endpoints (via `httpx.AsyncClient`), and RAG
operations (embed + store + search against pgvector).

**Files:**
- `runtime/tests/integration/__init__.py` (new)
- `runtime/tests/integration/conftest.py` (new: async DB session, test client,
  Redis client fixtures with transaction rollback)
- `runtime/tests/integration/test_db.py` (new: ORM model CRUD, UoW
  commit/rollback, repository queries)
- `runtime/tests/integration/test_api.py` (new: health check, plan generation
  with mocked LLM, materials CRUD)
- `runtime/tests/integration/test_rag.py` (new: embed + store + similarity search
  against pgvector)

**Fixtures design:**
```python
# conftest.py (simplified)
@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide a transactional DB session that rolls back after each test."""
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn)
        yield session
        await trans.rollback()

@pytest_asyncio.fixture
async def test_client(db_session, test_settings):
    """FastAPI test client with injected test DB session."""
    app = create_app(settings=test_settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def redis_client():
    """Real Redis client, flushed between tests."""
    client = redis.asyncio.from_url("redis://localhost:6379/1")
    yield client
    await client.flushdb()
    await client.aclose()
```

**Acceptance Criteria:**
- [ ] Database tests: create ORM models (Plan, Material, TutorSession), verify
      UnitOfWork commit persists and rollback discards, repository query methods
      return correct results, foreign key constraints enforced
- [ ] API tests: `GET /health` returns 200, `POST /plans/generate` returns plan
      (LLM mocked at port boundary, real DB), `POST /materials` CRUD cycle,
      error envelope on invalid input (422)
- [ ] RAG tests: embed a test document (3072-dim vector), store in pgvector,
      search by cosine similarity, verify top-k results and scores
- [ ] Tests use real Postgres via Docker (not SQLite, not in-memory)
- [ ] Test database cleaned between tests via transaction rollback
- [ ] `conftest.py` with async fixtures: `db_session`, `test_client`,
      `redis_client`
- [ ] Alembic migrations applied before test suite runs
      (`alembic upgrade head` in fixture or conftest)
- [ ] Tests pass in Docker: `docker compose run --rm api uv run pytest tests/integration -v`
- [ ] Integration tests complete in < 60s

---

### S11-004: Pipeline E2E Test

**Description:** End-to-end test of the full plan generation pipeline, from API
request through all LangGraph workflow stages to final export generation. Uses real
LLM calls (not mocked) to validate the complete flow. This test is the ultimate
confidence gate for the pipeline.

**Files:**
- `runtime/tests/e2e/__init__.py` (new)
- `runtime/tests/e2e/conftest.py` (new: E2E fixtures with real LLM config)
- `runtime/tests/e2e/test_pipeline.py` (new: full pipeline test)

**Test scenario:**
```python
async def test_full_pipeline_generates_all_exports():
    """Submit plan request -> Planner -> Validate -> Execute -> Export.

    Validates:
    - All pipeline stages execute in order
    - Accessibility score >= 60
    - All 9 export variants generated
    - Total time < 120s
    """
    request = PlanGenerateIn(
        run_id=ulid.new().str,
        user_prompt="Plano de aula de fracoes para 6o ano com aluno TEA na turma",
        subject="Matematica",
        class_accessibility_profile={"autism": True},
        learner_profiles=[{"name": "Aluno TEA", "needs": ["autism"]}],
    )
    # POST to /plans/generate
    response = await client.post("/plans/generate", json=request.model_dump())
    assert response.status_code == 200
    result = response.json()

    # Verify pipeline stages executed
    assert result["stage"] == "done"

    # Verify accessibility score
    assert result.get("accessibility_score", 0) >= 60

    # Verify all 9 export variants
    exports = result.get("exports", {})
    expected_variants = [
        "standard_html", "low_distraction_html", "large_print_html",
        "high_contrast_html", "dyslexia_friendly_html", "screen_reader_html",
        "visual_schedule_html", "student_plain_text", "audio_script",
    ]
    for variant in expected_variants:
        assert variant in exports, f"Missing export variant: {variant}"
```

**Acceptance Criteria:**
- [ ] Submit plan request via `POST /plans/generate`
- [ ] Pipeline executes all stages: Planner -> Validate -> (Refine if needed) ->
      Execute -> Export -> Done
- [ ] Uses real LLM calls (requires API key in CI secrets: `ANTHROPIC_API_KEY`)
- [ ] Accessibility score >= 60 on generated plan
- [ ] All 9 export variants generated and non-empty
- [ ] Total pipeline execution completes in < 120s
- [ ] Retry logic for transient LLM failures (max 2 retries with 5s delay)
- [ ] Test marked with `@pytest.mark.e2e` and skipped if
      `ANTHROPIC_API_KEY` not set (graceful degradation in CI without secrets)
- [ ] Test result includes timing metrics logged to stdout

---

### S11-005: Lint + Typecheck + CI (GitHub Actions)

> **Hackathon note (P2):** For the hackathon, local lint/typecheck is sufficient.
> GitHub Actions CI is nice for the repo but judges will not check CI status.
> ```bash
> # Local quality checks (sufficient for hackathon)
> cd runtime && uv run ruff check . && uv run mypy .
> cd frontend && pnpm lint && pnpm exec tsc --noEmit
> ```

**Description:** GitHub Actions CI pipeline with lint, typecheck, test, and build
stages. Runs on push to main and pull requests targeting main. Uses caching for
dependencies and Docker layers.

**Files:**
- `.github/workflows/ci.yml` (new: CI pipeline)
- `runtime/pyproject.toml` (update: ensure ruff, mypy, pytest configs)
- `.github/dependabot.yml` (new: automated dependency updates, optional)

**CI pipeline stages:**
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .

  typecheck:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run mypy .

  unit-tests:
    runs-on: ubuntu-latest
    needs: typecheck
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run pytest tests/unit -v --cov --cov-report=xml
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-unit
          path: coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d db redis
      - run: docker compose run --rm api uv run pytest tests/integration -v --cov --cov-report=xml
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-integration
          path: coverage.xml
      - run: docker compose down -v

  build:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

**Acceptance Criteria:**
- [ ] Triggers: push to `main`, pull request to `main`
- [ ] Stage 1 (lint): `ruff check .` + `ruff format --check .` (fail-fast)
- [ ] Stage 2 (typecheck): `mypy .` (depends on lint passing)
- [ ] Stage 3 (unit tests): `pytest tests/unit -v --cov` (depends on typecheck)
- [ ] Stage 4 (integration tests): `docker compose up -d db redis` then
      `docker compose run --rm api uv run pytest tests/integration -v`
      (depends on unit tests)
- [ ] Stage 5 (build): `docker compose build` all images (depends on integration)
- [ ] Caching: uv cache via `astral-sh/setup-uv@v4`, Docker layer cache via
      `docker/build-push-action` or BuildKit cache mounts
- [ ] Fail-fast: pipeline stops on first stage failure
- [ ] Coverage reports uploaded as artifacts (XML format for potential integration
      with coverage services)
- [ ] E2E tests (S11-004) run only if `ANTHROPIC_API_KEY` secret is set
      (conditional step)
- [ ] Total CI time target: < 5 minutes for lint+typecheck+unit, < 10 minutes
      including integration

---

### S11-006: Frontend Tests (Vitest, >=75%)

**Description:** Frontend unit and component tests using Vitest and React Testing
Library. Covers key components, hooks, and stores from Sprint 5 and Sprint 10.

**Files:**
- `frontend/vitest.config.ts` (new: Vitest configuration)
- `frontend/tests/setup.ts` (new: test setup with jsdom, Testing Library matchers)
- `frontend/tests/components/score-gauge.test.tsx` (new)
- `frontend/tests/components/pipeline-viewer.test.tsx` (new)
- `frontend/tests/components/persona-toggle.test.tsx` (new)
- `frontend/tests/components/plan-tabs.test.tsx` (new)
- `frontend/tests/hooks/use-pipeline-sse.test.ts` (new)
- `frontend/tests/hooks/use-tutor-ws.test.ts` (new)
- `frontend/tests/hooks/use-theme.test.ts` (new)
- `frontend/tests/stores/pipeline-store.test.ts` (new)
- `frontend/tests/stores/theme-store.test.ts` (new)

**Test coverage targets by area:**
| Area | Target | Key scenarios |
|------|--------|---------------|
| ScoreGauge | >=80% | Renders score arc, color thresholds (red/yellow/green), aria-label with score value |
| PipelineViewer | >=75% | Stage progression, active stage highlight, completed stage checkmark, error state |
| PersonaToggle | >=80% | Renders all persona buttons, toggle activates/deactivates, keyboard navigation, aria-pressed |
| PlanTabs | >=75% | Tab switching, content rendering per tab, keyboard arrow navigation, ARIA tab roles |
| usePipelineSSE | >=80% | Connection open, event parsing, reconnect on error, cleanup on unmount |
| useTutorWS | >=80% | WS connect, message send/receive, token accumulation, reconnect |
| useTheme | >=85% | Theme toggle, system preference detection, localStorage persistence |
| pipeline-store | >=90% | State transitions, event push, stage update, reset, FIFO cap |
| theme-store | >=90% | Toggle, persistence, initial load from localStorage |

**Acceptance Criteria:**
- [ ] Vitest configured with jsdom environment, React Testing Library, path aliases
- [ ] Component tests: ScoreGauge, PipelineViewer, PersonaToggle, PlanTabs render
      correctly and handle user interaction
- [ ] Hook tests: `usePipelineSSE`, `useTutorWS`, `useTheme` lifecycle, state
      transitions, cleanup
- [ ] Store tests: `pipeline-store` and `theme-store` state mutations, selectors,
      persistence
- [ ] >=75% coverage on frontend component and hook code
- [ ] Accessibility assertions with `@testing-library/jest-dom` matchers
      (`toHaveAttribute("aria-label", ...)`, `toBeVisible()`, role queries)
- [ ] Mock SSE/WS via `vitest.fn()` and custom EventSource/WebSocket stubs
- [ ] `pnpm test` runs all tests; `pnpm test:coverage` reports coverage
- [ ] Tests complete in < 30s

---

## Dependencies

- **Sprint 2** (Database Layer): ORM models, Alembic migrations, UnitOfWork for
  integration tests.
- **Sprint 5** (Frontend MVP): Components (ScoreGauge, PipelineViewer, PlanTabs)
  and Zustand stores for frontend tests.
- **Sprint 10** (SSE Streaming): SSE hook, WS hook, pipeline-store for frontend
  hook/store tests.
- **All prior sprints**: Integration and E2E tests exercise the full stack.

---

## Decisions

- **Docker Compose at root**: Single file for the entire stack. No per-service
  overrides for hackathon scope. Production would split into
  `docker-compose.prod.yml` overlay.
- **Transaction rollback for test isolation**: Integration tests wrap each test in
  a transaction that rolls back at teardown. Faster than truncate, avoids
  cross-test contamination.
- **Real LLM in E2E**: The pipeline E2E test uses real LLM calls because the
  pipeline's correctness depends on LLM output quality. Marked with
  `@pytest.mark.e2e` and skipped without API keys.
- **Vitest over Jest**: Vitest is faster, native ESM support, compatible with
  Vite-based Next.js 16 builds.
- **Coverage as artifact, not gate**: Coverage reports are uploaded as CI artifacts
  but do not block the pipeline (coverage gate enforced by code review for
  hackathon).
- **Sprint is optional for hackathon** (expert consensus, Gemini-3-Pro-Preview):
  Docker+Testing adds repo quality but is not demo-critical. Localhost is
  sufficient for the hackathon demo.
- **Focus testing effort on domain layer**: Highest value, lowest effort. Domain
  entities, accessibility validator, export renderer, and curriculum search are
  pure functions that can be tested without infrastructure.
- **CI pipeline is "nice to show"**: Judges will evaluate the demo, not the CI
  badge. Local lint/typecheck is the pragmatic minimum.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| CI time too long with Docker integration tests | Parallel jobs where possible, Docker layer caching, limit integration tests to critical paths |
| Port collisions with host services | Documented in `.env.example`; CI runs on clean Ubuntu runner (no collisions) |
| Flaky E2E tests due to LLM non-determinism | Retry logic (max 2 retries), relaxed score threshold (>=60 not >=80), skip without API key |
| pgvector extension not available | `pgvector/pgvector:pg17` image includes extension pre-installed; `CREATE EXTENSION IF NOT EXISTS vector` in migration |
| Frontend test flakiness with async hooks | Use `waitFor()` and `act()` from Testing Library; deterministic timers via `vi.useFakeTimers()` |

---

## Technical Notes

**Existing code to leverage:**
- `runtime/ailine_runtime/api/app.py` has `create_app()` factory that accepts
  `Settings` -- integration tests inject test settings with test DB URL.
- `runtime/ailine_runtime/shared/config.py` has `Settings` with
  `env_nested_delimiter="__"` -- Docker Compose sets `AILINE_DB__URL` and
  `AILINE_REDIS__URL` via environment.
- `runtime/ailine_runtime/shared/container.py` has `Container.build(settings)` --
  tests can build a container with test-specific settings.
- `runtime/ailine_runtime/domain/entities/*.py` has 22 Pydantic entities --
  unit tests validate construction and serialization.

**Test tooling to install:**
- Backend: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (async test client),
  `redis[hiredis]` (async Redis for fixtures)
- Frontend: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`, `jsdom`
