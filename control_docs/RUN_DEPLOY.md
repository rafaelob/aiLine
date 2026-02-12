# Run & Deploy

## Prerequisites
- Python 3.13 (managed by uv, pinned in .python-version)
- Node.js 24 (pnpm via Corepack)
- Docker 27+ / Docker Compose v2
- GCloud CLI (for deploy)

## Environment Variables
```
cp .env.example .env
# Required:
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...          # for Gemini embeddings
# Optional:
OPENAI_API_KEY=...          # fallback LLM
ELEVENLABS_API_KEY=...      # TTS
# Docker port overrides (if collisions):
API_HOST_PORT=8000
FRONTEND_HOST_PORT=3000
```

## Docker Compose (recommended)
```bash
# Full stack: api (8000), frontend (3000), db (5432 internal), redis (6379 internal)
docker compose up -d --build

# Check health
docker compose ps

# View logs
docker compose logs -f api

# Tear down (preserves volumes)
docker compose down

# Tear down + delete data
docker compose down -v
```

**Services:**
| Service | Image | Port (host) | Network |
|---------|-------|-------------|---------|
| db | pgvector/pgvector:0.8.0-pg16 | none (internal) | backend |
| redis | redis:7.4-alpine | none (internal) | backend |
| api | runtime/Dockerfile | 8000 | backend + frontend |
| frontend | frontend/Dockerfile | 3000 | frontend |

**DB init:** `infra/db/init-pgvector.sql` auto-creates the `vector` extension via docker-entrypoint-initdb.

## Local Development (without Docker)

### Backend (uv)
```bash
cd runtime
uv sync --all-extras
uv run uvicorn ailine_runtime.api.app:create_app --factory --reload --port 8000
```

### Frontend (pnpm)
```bash
cd frontend
corepack enable
pnpm install
pnpm dev   # http://localhost:3000
```

### Database
```bash
cd runtime
uv run alembic upgrade head
```

## Project Structure
```
agents/            # ailine_agents package (Pydantic AI 1.58.0 + LangGraph)
  ailine_agents/   # 4 typed agents, tool/model bridges, workflows, skill registry
skills/            # 11 SKILL.md files (lesson-planner, socratic-tutor, accessibility-coach, etc.)
runtime/
  ailine_runtime/
    domain/        # Pure entities + port protocols
    adapters/      # Concrete implementations
    app/           # Use cases / services
    api/           # FastAPI routers + middleware + streaming
    workflow/      # LangGraph orchestration (re-exports from ailine_agents)
    accessibility/ # Quality gate + exports
    shared/        # Config, container, errors, i18n, observability
    data/          # Static data (standards, i18n)
frontend/          # Next.js 16
infra/
  db/              # DB init scripts (pgvector extension)
```

## GCP Deploy
```bash
gcloud auth login
gcloud config set project ailine-hackathon
gcloud builds submit --tag gcr.io/ailine-hackathon/api:$(git rev-parse --short HEAD)
gcloud run deploy ailine-api \
  --image gcr.io/ailine-hackathon/api:$(git rev-parse --short HEAD) \
  --region us-central1 --platform managed
```

## Secrets
Production secrets via GCP Secret Manager. Never commit .env files.
