# Changelog
All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Hexagonal architecture: domain entities, port protocols, adapter implementations
- Plan pipeline: LangGraph parallel fan-out (ADR-042), SmartRouter (ADR-049), quality gate (ADR-050)
- ailine_agents package: 4 Pydantic AI 1.58.0 typed agents (Planner, Executor, QualityGate, Tutor) + tool/model bridges (ADR-059)
- LangGraph workflows: plan_workflow (Planner->QualityGate->Refine->Executor), tutor_workflow
- FastAPI 8 routers, SSE 14 typed events, DI container with FakeLLM/FakeSTT/FakeTTS (ADR-051)
- LLM adapters: Anthropic, OpenAI, Gemini + FakeChatLLM; SmartRouterAdapter (rules+weighted)
- SQLAlchemy 2.x async ORM (11 tables, UUID v7), Alembic migrations, UoW+Repository, composite FK (ADR-053)
- Embeddings (Gemini/OpenAI 1536d MRL), vector stores (pgvector HNSW/ChromaDB/InMemory)
- Material ingestion (chunk 512t/64 overlap, embed, index), RAG query, curriculum (BNCC/CCSS/NGSS)
- Tutor agents: LangGraph workflow, session management, playbooks
- Media: WhisperSTT, OpenAISTT, ElevenLabsTTS, OCR, MediaPipeSignRecognition + CI fakes
- Demo mode (3 scenarios), i18n (PT-BR/EN/ES), observability (structlog+OTEL)
- Docker Compose (Postgres+pgvector, Redis, API, Frontend), Next.js 16 frontend (React Compiler, 9 themes)
- Frontend: Pipeline Viewer, Plan Tabs, Score Gauge, Export Viewer, Visual Schedule, Persona Toggle, Accessibility Twin, VLibras, Webcam
- SSE replay (InMemory+Redis ZSET, ADR-054), RunContext terminal guarantee (ADR-055)
- Web Worker sign language (ADR-057), ThemeContext MutationObserver (ADR-058)
- VLibras a11y, reduced-motion sync, React Activity low-distraction, compute_route() pure fn
- Live API tests (@pytest.mark.live_llm): 65 total (55 runtime + 10 agents)
- 1265+ backend tests (1199 runtime + 129 agents), 331+ frontend tests
- 59 ADRs (ADR-001 through ADR-059), technology research synthesis
- Custom Skill Registry: YAML frontmatter parser, SkillRegistry with scan/query/prompt-fragment, wired into Planner + Tutor agents
- SKILL.md frontmatter migration: 11 skills moved to metadata block with compatibility structure
- CCSS ELA curriculum data (ccss_ela.json): 46 Common Core English Language Arts K-8 standards
- Bloom's Taxonomy: bloom_level field on all 4 curriculum systems, filter in search API
- Libras STT ML Pipeline: training scaffold, TF.js MLP classifier, webcam landmarks, gloss->LLM streaming

### Changed
- FastAPI upgraded 0.128.8 -> 0.129.0; runtime + agents lock files upgraded
- OpenAI SDK upgraded to 2.x (openai>=2.11,<3) — required by pydantic-ai
- Runtime workflows (plan_workflow.py, tutor_workflow.py) now thin re-exports from ailine_agents
- Routers (plans.py, plans_stream.py) use AgentDepsFactory.from_container()
- SmartRouter rebalanced: 0.25/0.25/0.25/0.15/0.10 (ADR-049); pools: 5/5 (ADR-052)
- uuid-utils for UUID v7, motion (was framer-motion), proxy.ts (was middleware.ts)

### Removed
- claude-agent-sdk removed from dependencies (ADR-048)
- Deleted: executor_agent_sdk.py, planner_deepagents.py, claude_sdk_executor.py, deepagents_planner.py, adapters_agent_sdk.py

### Fixed
- Ruff lint: 33 errors fixed across runtime + agents (N806 uppercase vars, SIM109, RUF005, I001, F401, UP035, RUF022, SIM300, RUF059)
- Anthropic model ID: claude-haiku-4-20250414 -> claude-haiku-4-5-20251001
- Gemini streaming: generate_content_stream requires await (google-genai API change)
- ChatLLM protocol/adapter signature unified; LearnerProfile name collision resolved
- Container.build() wires all adapters; embedding dimensions default=1536
- OpenAI+Gemini clients in __init__; datetime.utcnow()->datetime.now(UTC)
- DeepAgents structured_response None (ADR-043); all 17 S1 review + 21 expert items resolved
