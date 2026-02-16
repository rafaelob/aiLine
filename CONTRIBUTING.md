# Contributing to AiLine

Thank you for your interest in contributing to AiLine!

## Project Principles

- **Inclusion first:** ASD, ADHD, learning disabilities, hearing and visual impairments are first-class requirements, not afterthoughts.
- **Teacher amplification:** Humans decide; AI agents execute and validate. Teachers always have final say.
- **Security by default:** Tool whitelists, minimal data collection, tenant isolation.
- **Glass Box AI:** Every AI decision is visible, scored, and auditable.

## Getting Started

```bash
# 1. Clone and configure
git clone <repo-url> && cd aiLine
cp .env.example .env
# Add your API keys (see .env.example for required keys)

# 2. Launch all services
docker compose up -d --build

# 3. Access
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
```

## Development Setup

### Backend (Python 3.13 + FastAPI)

```bash
cd runtime
uv sync                    # Install dependencies
uv run pytest -v --cov     # Run 1,940+ tests
uv run ruff check .        # Lint
uv run mypy .              # Type check
```

### Agents (Pydantic AI + LangGraph)

```bash
cd agents
uv sync
uv run pytest -v           # Run 277 tests
```

### Frontend (Next.js 16 + React 19)

```bash
cd frontend
pnpm install
pnpm dev                   # Dev server at http://localhost:3000
pnpm test                  # Run 1,096+ tests
pnpm lint                  # ESLint
pnpm typecheck             # TypeScript strict
```

## How to Propose Changes

1. Open an issue describing the change
2. Fork the repository and create a feature branch
3. Include in your PR:
   - Context and motivation
   - Design decisions (reference existing ADRs if applicable)
   - Accessibility impact assessment
   - Tests for new functionality
4. Ensure all quality gates pass:
   - `uv run ruff check .` (Python lint)
   - `uv run mypy .` (Python types)
   - `pnpm lint` (JS/TS lint)
   - `pnpm typecheck` (TypeScript)
   - All tests green

## Code Style

- **Python:** Ruff + Black, Google-style docstrings, type hints everywhere
- **TypeScript:** ESLint flat config, strict mode, no `any`
- **Components:** Under 300 lines, single responsibility
- **Functions:** Under 60 lines
- **Accessibility:** All interactive elements need `aria-labels`, proper focus management

## Architecture

The project uses **Hexagonal Architecture** (Ports-and-Adapters):
- `runtime/ailine_runtime/domain/` — Pure domain (zero framework imports)
- `runtime/ailine_runtime/adapters/` — External integrations
- `runtime/ailine_runtime/api/` — FastAPI routes and middleware
- `agents/ailine_agents/` — AI agent definitions and workflows
- `frontend/src/` — Next.js 16 with App Router

See [SYSTEM_DESIGN.md](control_docs/SYSTEM_DESIGN.md) for full architecture docs.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
