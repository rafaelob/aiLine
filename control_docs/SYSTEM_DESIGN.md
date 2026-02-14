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

Student message -> SSE (fetch-event-source) -> LangGraph tutor StateGraph:

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

- **UnitOfWork:** `async_sessionmaker(expire_on_commit=False)`, pool 10+10 (ADR-052), step-level UoW per LangGraph node
- **SmartRouter:** 0.25 tokens + 0.25 structured + 0.25 tools + 0.15 history + 0.10 intent (ADR-049). Thresholds: <=0.40 cheap, 0.41-0.70 middle, >=0.71 primary. Hard overrides for tools/strict_json. Escalation ladder up to 4-6 attempts.
- **SSE:** 14 events, `{run_id, seq, ts, type, stage, payload}` envelope. Terminal guarantee via RunContext (ADR-055). Redis ZSET replay (ADR-054). asyncio.Lock for thread safety.
- **Branch errors:** `safe_branch()` -> `{ok, payload, error}`. Fan-in on partial success.
- **TenantContext:** `teacher_id` from JWT only, `TeacherId` NewType wrapper, all repos require it.

## ADR Log

60 ADRs (ADR-001 through ADR-060). Key decisions: 001 Hexagonal | 002-003 SQLAlchemy+pgvector | 006 SSE+WS | 012 multi-tenancy | 013 parallel LangGraph | 017/028-029/049 SmartRouter | 024/038 typed SSE | 042 recursion_limit=25 | 048 direct Anthropic API (no SDK) | 050 tiered quality gate | 051 FakeLLM CI | 053 composite FK | 054 SSE replay (Redis ZSET) | 055 RunContext terminal guarantee | 056 pool sizing | 057 Web Worker sign lang | 058 ThemeContext | 059 ailine_agents (Pydantic AI) | 060 structural tenant isolation + centralized authz


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

**Infrastructure:** PostgreSQL 16, pgvector 0.8.1, Redis 7.x, Docker Compose v2
