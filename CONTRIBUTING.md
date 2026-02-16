# Contributing to AiLine

Thank you for your interest in contributing to **AiLine** (Adaptive Inclusive Learning — Individual Needs in Education)! Every contribution helps make education more accessible.

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
# Health:    http://localhost:8000/health/ready
```

### Demo Mode

AiLine includes a built-in demo with pre-configured profiles:

1. Visit `http://localhost:3000` and click "Try the Demo"
2. Choose a profile: Teacher, Student (4 accessibility profiles), or Parent
3. The demo seeds sample data automatically — no API keys needed for exploration

## Development Setup

### Backend (Python 3.13 + FastAPI)

```bash
cd runtime
uv sync                    # Install dependencies
uv run pytest -v --cov     # Run 1,940+ tests
uv run ruff check .        # Lint
uv run black --check .     # Format check
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

### Docker (recommended)

```bash
docker compose up -d --build
docker compose exec api bash -c "cd /app && uv run pytest -v"
```

## How to Propose Changes

1. Open an issue describing the change (use our templates)
2. Fork the repository and create a feature branch (`feature/your-feature`)
3. Include in your PR:
   - Context and motivation
   - Design decisions (reference existing ADRs if applicable)
   - Accessibility impact assessment
   - Tests for new functionality
4. Ensure all quality gates pass before submitting

## Accessibility-First Development

AiLine supports 9 accessibility themes. When building UI:

- **Always** add `aria-labels` to interactive elements
- **Always** ensure keyboard navigation works (Tab, Enter, Escape, Arrow keys)
- **Always** respect `prefers-reduced-motion` for animations
- **Always** use CSS variables (`--color-text`, `--color-muted`, etc.) instead of hardcoded colors
- **Always** test with multiple themes: `default`, `tea` (ASD), `tdah` (ADHD), `dyslexia`, `hearing`
- Use `cn()` from `@/lib/cn` for conditional class names
- Components should be under 300 lines

### Accessibility Testing

```bash
# Run axe-core accessibility audit
cd frontend && pnpm exec playwright test --grep a11y
```

## Internationalization (i18n)

AiLine supports 3 locales: English (`en`), Portuguese (`pt-BR`), and Spanish (`es`).

- Translation files: `frontend/src/messages/{locale}.json`
- Use `useTranslations('namespace')` in client components
- Use `getTranslations({ locale, namespace })` in server components
- **All user-facing text must be translated** — no hardcoded strings

To add a new translation key:
1. Add the key to `en.json` first
2. Add corresponding keys to `pt-BR.json` and `es.json`
3. Use the key via `t('your_key')` in components

## Agent Skills

AiLine has 17 agent skills following the [agentskills.io](https://agentskills.io) spec. To create a new skill:

1. Create `skills/your-skill-name/SKILL.md` following the spec
2. Include: metadata, description, instructions, examples, resources
3. **Important:** Metadata values must be `string` only (no objects/arrays)
4. Register in `agents/ailine_agents/skills/registry.py`
5. Add tests in `agents/tests/`

## Architecture

The project uses **Hexagonal Architecture** (Ports-and-Adapters):

```
runtime/ailine_runtime/
  domain/          # Pure entities + port protocols (zero imports)
  adapters/        # Anthropic, OpenAI, Gemini, pgvector adapters
  app/             # Use cases and services
  api/             # FastAPI routers + middleware + SSE streaming
agents/ailine_agents/
  agents/          # 5 Pydantic AI agents
  workflows/       # LangGraph workflows
  skills/          # Skill runtime (registry, loader, composer)
frontend/src/
  app/             # Next.js 16 App Router pages
  components/      # React 19 client components
  stores/          # Zustand state stores
```

See [SYSTEM_DESIGN.md](control_docs/SYSTEM_DESIGN.md) and [Architecture Diagrams](docs/architecture-diagram.md) for details.

## Quality Gates

All PRs must pass:

| Gate | Command |
|------|---------|
| Python lint | `uv run ruff check .` |
| Python format | `uv run black --check .` |
| Python types | `uv run mypy .` |
| JS/TS lint | `pnpm lint` |
| TypeScript | `pnpm typecheck` |
| Backend tests | `cd runtime && uv run pytest` |
| Agent tests | `cd agents && uv run pytest` |
| Frontend tests | `pnpm test` |
| Docker build | `docker compose up -d --build` |

## Code Review Checklist

- [ ] Does the change serve the user (teacher, student, or parent)?
- [ ] Is accessibility preserved or improved?
- [ ] Are new UI elements keyboard-navigable and screen-reader friendly?
- [ ] Is the code in the right architectural layer?
- [ ] Are there tests for the new behavior?
- [ ] Is i18n complete (all 3 locales)?
- [ ] Does Docker Compose still build and run?

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
