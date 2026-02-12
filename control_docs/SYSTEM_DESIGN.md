# System Design

## Architecture

Hexagonal (Ports-and-Adapters). Domain core has zero framework imports.

- **Domain:** entities, value objects, domain services (pure Pydantic)
- **Ports:** Protocol interfaces (ChatLLM, Embeddings, VectorStore, UnitOfWork, CurriculumProvider, EventBus, STT, TTS, SignRecognition, ObjectStorage)
- **Adapters:** concrete implementations (Anthropic, OpenAI, Gemini, pgvector, ChromaDB, Qdrant, etc.)
- **Application:** use cases orchestrating domain + ports (plan generation, tutor chat, material ingestion, RAG query, sign recognition, skill registry)
- **Infrastructure:** FastAPI routers, SQLAlchemy repos, LangGraph workflows

## Data Flows

### Plan Generation Pipeline (Parallel LangGraph)

User request -> FastAPI SSE endpoint -> LangGraph StateGraph:

1. Parallel fan-out: [RAG_Search | Profile_Analyzer] (simultaneous via static edges)
2. Fan-in -> PlannerAgent (Pydantic AI 1.58.0, StudyPlanDraft output) (ADR-059)
3. QualityGateAgent (deterministic validator, score 0-100)
4. Conditional: score < 80 -> Refine loop (max 2 iters) | else -> ExecutorAgent
5. ExecutorAgent (Pydantic AI + LangGraph ToolNode) with tool bridge (ToolDef -> @agent.tool) (ADR-048/059)
6. Export Formatter (10 variants)
   -> SSE astream_events v2 streamed to frontend with typed event contract

SSE Event Types: run.started, stage.started, stage.progress, quality.scored, quality.decision, refinement.started, refinement.completed, tool.started, tool.completed, stage.completed, stage.failed, run.completed, run.failed, heartbeat

### Tutor Chat

Student message -> WebSocket -> LangGraph tutor StateGraph:

1. Route (classify: needs RAG? yes -> Retrieve | no -> Respond)
2. Respond (Socratic system prompt + accessibility playbook + RAG context)
3. Format (TutorTurnOutput with structured sections)
   -> AsyncPostgresSaver checkpointer for session persistence

### Sign Language (Browser -> Server)

Webcam -> MediaPipe JS (Hands+Pose) -> TF.js MLP classifier -> Gloss labels (limited to 3-4 navigation gestures for MVP)
-> Dedicated WebSocket /ws/accessibility/libras -> LLM gloss->sentence -> Response
Text -> VLibras widget (text->Libras 3D avatar, government CDN)

### Material Ingestion

Upload -> parse (PDF/DOCX/TXT) -> chunk (512 tokens, 64 overlap) -> embed (gemini-embedding-001 @ 1536d MRL) -> pgvector HNSW upsert

### SmartRouterAdapter (Multi-LLM)

Weighted complexity classifier -> route to primary/cheap/escalation (see patterns below).
Escalation triggers: JSON parse fail, schema validation fail, low validator score. Model badge in UI.

## Key Implementation Patterns

### UnitOfWork (SQLAlchemy 2.x Async)
- `async_sessionmaker(expire_on_commit=False)` per request scope
- Pool: `pool_pre_ping=True`, `pool_size=5`, `max_overflow=5` (ADR-052)
- Repository accessors cached on UoW instance (lazy init)
- Step-level UoW: each LangGraph node opens/closes own UoW; never hold session across LLM calls
- JSONB columns stored as plain `Mapped[dict]`; explicit `DomainModel.model_validate()` in mapper

### SmartRouter Scoring
- Weights: 0.25 tokens + 0.25 structured + 0.25 tools + 0.15 history + 0.10 intent (ADR-049)
- Thresholds: score <= 0.40 cheap, 0.41-0.70 middle, >= 0.71 primary
- Hard overrides: tools_required or strict_json -> disallow cheap regardless of score
- Cache: TTL 5 min (±20% jitter) keyed by node_type + tool/schema hash + intent category
- Escalation ladder: same-model self-repair → one tier up → max 4-6 total attempts

### SSE Event Contract
- 14 events: run.started, stage.started/progress/completed/failed, quality.scored/decision, refinement.started/completed, tool.started/completed, run.completed/failed, heartbeat
- Envelope: `{run_id, seq, ts, type, stage, payload}`
- Terminal safety: RunContext async context manager guarantees exactly-once terminal (ADR-055)
- Replay: InMemoryReplayStore (dev) / RedisReplayStore (ZSET, score=seq, TTL 30min) (ADR-054)
- Thread safety: asyncio.Lock on SSEEventEmitter.emit for parallel LangGraph branches
- Reverse proxy: X-Accel-Buffering: no header on SSE endpoints

### Branch Error Envelopes
- `safe_branch(fn, *a, **kw)` -> `{"ok": bool, "payload": T|None, "error": str|None}`
- Fan-in proceeds if at least one branch succeeds; partial results surfaced in SSE

### TenantContext
- `teacher_id` extracted from JWT only (never request body)
- `TeacherId = NewType("TeacherId", uuid.UUID)` wrapper for type safety
- All repository methods require `TeacherId` parameter; no implicit global

## ADR Log

59 ADRs (ADR-001 through ADR-059). Key: 001 Hexagonal | 002-003 SQLAlchemy+pgvector | 006 SSE+WS | 012 multi-tenancy | 013 parallel LangGraph | 017/028-029/049 SmartRouter | 024/038 typed SSE | 042 recursion_limit=25 | 048 direct Anthropic API (no SDK) | 050 tiered quality gate | 051 FakeLLM CI | 053 composite FK | 054 SSE replay (Redis ZSET) | 055 RunContext terminal guarantee | 056 pool sizing | 057 Web Worker sign lang | 058 ThemeContext | 059 ailine_agents (Pydantic AI)

Full ADR details: `references/technology_research_synthesis.md`

## Dependencies in Use

**Backend (Python 3.13, uv-managed):**
FastAPI 0.129.0, SQLAlchemy 2.0.46, Alembic 1.18.4, asyncpg 0.31.0, Pydantic 2.12.5,
LangGraph 1.0.8, Pydantic AI 1.58.0, ailine-agents 0.1.0, DeepAgents 0.4.1,
Anthropic SDK 0.79.0, OpenAI SDK 2.20.0, google-genai 1.63.0,
pgvector-python 0.4.2, structlog 25.4.0, sse-starlette 3.2.0, faster-whisper 1.2.1,
uuid-utils 0.14.0, langgraph-checkpoint-postgres 3.0.4, aiosqlite 0.21.0, pypdf 5.x

**Frontend (Node 24, pnpm):**
Next.js 16.1.6, React 19.2.4, Tailwind 4.1.18, shadcn/ui 3.8.4, next-intl 4.8.2,
Zustand 5.0.11, motion 12.34.0, Recharts 3.7.0, DOMPurify 3.3.1,
@mediapipe/tasks-vision 0.10.32, @tensorflow/tfjs 4.22.0, @microsoft/fetch-event-source 2.0.1

**Infrastructure:** PostgreSQL 17, pgvector 0.8.1, Redis 7.x, Docker Compose v2
