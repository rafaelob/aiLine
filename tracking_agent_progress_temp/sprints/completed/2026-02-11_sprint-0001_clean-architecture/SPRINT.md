# Sprint 0001 — Clean Architecture Refactor

**Status:** completed | **Date:** 2026-02-11
**Goal:** Restructure into hexagonal architecture with domain/ports/adapters, DI
container, Pydantic Settings.

---

## Scope & Acceptance Criteria

The entire `runtime/ailine_runtime/` package must be reorganized into a hexagonal
(ports-and-adapters) architecture. Domain entities are pure Pydantic models with
zero framework dependencies. All external capabilities (LLMs, embeddings, vector
stores, databases, events, media) are abstracted behind `typing.Protocol` ports.
A lightweight DI container wires adapters to ports at startup. Configuration uses
Pydantic Settings with environment variable support. Structured logging,
error hierarchy, and i18n are established as shared infrastructure.

---

## Stories

### S1-001: Domain entities [x]

**Description:** Created the full set of domain entity types as pure Pydantic
models. These types represent the core domain concepts and carry no framework
dependencies -- they are importable and testable in isolation.

**Entity types created (22 total):**
- Pipeline: `RunStage`, `ExportFormat`, `RunEvent`, `PipelineRun`
- Planning: `Objective`, `PlanStep`, `StudentStep`, `StudentPlan`
- Accessibility: `AccessibilityAdaptation`, `AccessibilityPackDraft`,
  `AccessibilityNeed`, `SupportIntensity`
- Curriculum: `CurriculumSystem`, `CurriculumObjective`
- Materials: `Material`, `MaterialChunk`, `StudyPlanDraft`
- Tutoring: `LearnerProfile`, `TutorPersona`, `TutorMaterialsScope`,
  `TutorAgentSpec`, `TutorTurnOutput`, `TutorMessage`, `TutorSession`

**Files:** `runtime/ailine_runtime/domain/entities/*.py` (8 files)

**Acceptance:** All entities importable, Pydantic validation works on
construction with valid and invalid data.

---

### S1-002: Port protocols [x]

**Description:** Defined the port layer as `typing.Protocol` classes with
`@runtime_checkable`. This enables structural subtyping -- adapters satisfy
ports by implementing the right methods, without inheritance coupling.

**Protocols created (13 total):**
- LLM: `ChatLLM`
- Embeddings: `Embeddings`
- Vector store: `VectorStore`, `VectorSearchResult`
- Persistence: `Repository`, `UnitOfWork`
- Curriculum: `CurriculumProvider`
- Events: `EventBus`
- Media: `STT` (speech-to-text), `TTS` (text-to-speech),
  `SignRecognition`, `ImageDescriber`
- Storage: `ObjectStorage`

**Files:** `runtime/ailine_runtime/domain/ports/*.py` (9 files)

**Acceptance:** All protocols importable, `isinstance()` checks pass at adapter
registration time for concrete implementations.

---

### S1-003: Shared config (Pydantic Settings) [x]

**Description:** Centralized all configuration into a single Pydantic Settings
class that loads from environment variables and `.env` files.

**Design:**
- Root `Settings` class with `env_prefix="AILINE_"`.
- Nested sub-configs: `LLMConfig`, `EmbeddingConfig`, `VectorStoreConfig`,
  `DatabaseConfig`, `RedisConfig`.
- `AliasChoices` for API keys so both `ANTHROPIC_API_KEY` and
  `AILINE_ANTHROPIC_API_KEY` are accepted (developer convenience).

**Files:** `runtime/ailine_runtime/shared/config.py`

**Acceptance:** `Settings()` loads from `.env` file; missing required keys raise
a clear `ValidationError` at startup.

---

### S1-004: DI container [x]

**Description:** A lightweight dependency injection container implemented as a
frozen dataclass with a `build()` factory method. No DI framework required.

**Design:**
- `Container` is a `@dataclass(frozen=True)` holding resolved port
  implementations.
- `Container.build(settings: Settings) -> Container` reads the settings,
  instantiates the correct adapters, and returns a populated container.
- Fields: `llm`, `embeddings`, `vectorstore`, `event_bus` (extensible).

**Files:** `runtime/ailine_runtime/shared/container.py`

**Acceptance:** `Container.build(settings)` returns a container with all ports
populated and ready for injection into services and workflows.

---

### S1-005: Error hierarchy + i18n [x]

**Description:** Established a structured error hierarchy and an
internationalization utility for user-facing messages.

**Error hierarchy:**
- `AiLineError` base class with `code: str`, `message: str`,
  `details: dict | None`.
- Subclasses: `PlanGenerationError`, `ValidationError`, `ProviderError`,
  `RateLimitError`, `NotFoundError`.
- Each error carries a machine-readable code for API error envelopes.

**i18n:**
- `t(key: str, locale: str = "en") -> str` function.
- Loads translations from `data/i18n/*.json` files.
- Falls back from specific locale (e.g., `pt-BR`) to language (`pt`) to
  default (`en`).

**Files:** `runtime/ailine_runtime/shared/errors.py`,
`runtime/ailine_runtime/shared/i18n.py`

**Acceptance:** Errors carry structured codes suitable for API responses.
`t("key", "pt-BR")` returns a localized string with proper fallback chain.

---

### S1-006: Observability (structlog) [x]

**Description:** Set up structured logging using structlog, ready for OTEL
integration later.

**API:**
- `configure_logging(json_mode: bool = False)` -- call once at startup.
- `get_logger(name: str) -> BoundLogger` -- returns a contextualized logger.
- `log_event(event_type: str, **kwargs)` -- convenience for pipeline events.

**Files:** `runtime/ailine_runtime/shared/observability.py`

**Acceptance:** Structured JSON logs output during pipeline execution with
consistent key structure.

---

### S1-007: Workflow refactor [x]

**Description:** Extracted the LangGraph workflow into a dedicated module with
clean node functions and state management.

**Design:**
- `RunState` TypedDict for LangGraph state.
- Node functions: `planner_node`, `validate_node`, `bump_refine`,
  `executor_node`.
- Conditional edge: `should_execute`.
- StateGraph compiled into a runnable workflow.
- Old `workflow_langgraph.py` delegates to the new module for backward
  compatibility.

**Files:** `runtime/ailine_runtime/workflow/plan_workflow.py`,
`runtime/ailine_runtime/workflow/__init__.py`

**Acceptance:** Workflow graph compiles and executes through the full
plan-validate-execute cycle.

---

### S1-008: API routers [x]

**Description:** Restructured the API layer into a factory function with
modular routers.

**Design:**
- `create_app()` factory: creates FastAPI app, registers health check, CORS
  middleware, and routers.
- Routers: `materials` (material CRUD), `plans` (plan generation/retrieval),
  `tutors` (tutor session management).
- SSE streaming utilities in `api/streaming/sse.py` for real-time pipeline
  events.

**Files:** `runtime/ailine_runtime/api/*.py`,
`runtime/ailine_runtime/api/routers/*.py`,
`runtime/ailine_runtime/api/streaming/sse.py` (9 files total)

**Acceptance:** FastAPI app starts, `GET /health` returns 200, all routers
registered and reachable.

---

### S1-009: Initial adapter stubs [x]

**Description:** Created the first concrete adapter implementations that
satisfy the domain port protocols.

**Adapters created:**
- **Agents:**
  - `DeepAgentsPlanner` -- wraps DeepAgents for plan generation
    (`adapters/agents/deepagents_planner.py`).
  - `ClaudeSDKExecutor` -- wraps Claude Agent SDK for plan execution
    (`adapters/agents/claude_sdk_executor.py`).
- **LLM:**
  - `AnthropicChatLLM` -- Anthropic API via `anthropic` SDK.
  - `OpenAIChatLLM` -- OpenAI API via `openai` SDK.
  - `GeminiChatLLM` -- Google Gemini API via `google-genai` SDK.
- **Events:**
  - `InMemoryEventBus` -- simple in-process pub/sub for development.

**Files:** `runtime/ailine_runtime/adapters/agents/*.py`,
`runtime/ailine_runtime/adapters/llm/*.py`,
`runtime/ailine_runtime/adapters/events/inmemory_bus.py`
(11 directories with `__init__.py`, 5 concrete adapter files)

**Acceptance:** All adapters importable, structural protocol compliance verified
(each adapter satisfies its corresponding port protocol).

---

## Dependencies

Sprint 0 (Foundation & API Fixes) -- all API call-sites must be correct before
restructuring around them.

---

## Decisions

- **ADR-001:** Hexagonal Architecture with `typing.Protocol` for structural
  subtyping. Chosen over ABC inheritance for loose coupling and testability.
- **ADR-002:** Pydantic Settings for configuration with `env_prefix`. Chosen
  over raw `os.environ` or `python-dotenv` alone for validation and typing.
- **ADR-003:** structlog for structured logging. Chosen over stdlib `logging`
  for JSON output, context binding, and OTEL compatibility.
- **ADR-004:** Frozen dataclass DI container. Chosen over dependency-injection
  frameworks (e.g., `dependency-injector`, `injector`) for simplicity, zero
  extra dependencies, and explicit wiring.

---

## Architecture Created

```
runtime/ailine_runtime/
├── domain/
│   ├── entities/        # 8 files, 22 domain types (pure Pydantic)
│   │   ├── __init__.py
│   │   ├── pipeline.py          # RunStage, ExportFormat, RunEvent, PipelineRun
│   │   ├── planning.py          # Objective, PlanStep, StudentStep, StudentPlan
│   │   ├── accessibility.py     # AccessibilityAdaptation, AccessibilityPackDraft,
│   │   │                        #   AccessibilityNeed, SupportIntensity
│   │   ├── curriculum.py        # CurriculumSystem, CurriculumObjective
│   │   ├── materials.py         # Material, MaterialChunk, StudyPlanDraft
│   │   └── tutoring.py          # LearnerProfile, TutorPersona, TutorMaterialsScope,
│   │                            #   TutorAgentSpec, TutorTurnOutput, TutorMessage,
│   │                            #   TutorSession
│   └── ports/           # 9 files, 13 protocols
│       ├── __init__.py
│       ├── llm.py               # ChatLLM
│       ├── embeddings.py        # Embeddings
│       ├── vectorstore.py       # VectorStore, VectorSearchResult
│       ├── persistence.py       # Repository, UnitOfWork
│       ├── curriculum.py        # CurriculumProvider
│       ├── events.py            # EventBus
│       ├── media.py             # STT, TTS, SignRecognition, ImageDescriber
│       └── storage.py           # ObjectStorage
├── shared/              # 6 files
│   ├── __init__.py
│   ├── config.py                # Settings (Pydantic Settings)
│   ├── container.py             # Container (frozen dataclass DI)
│   ├── errors.py                # AiLineError hierarchy
│   ├── i18n.py                  # t() translation function
│   └── observability.py         # configure_logging, get_logger, log_event
├── adapters/            # 11 directories, 5 concrete adapters
│   ├── agents/
│   │   ├── deepagents_planner.py
│   │   └── claude_sdk_executor.py
│   ├── llm/
│   │   ├── anthropic_llm.py
│   │   ├── openai_llm.py
│   │   └── gemini_llm.py
│   └── events/
│       └── inmemory_bus.py
├── workflow/             # 2 files
│   ├── __init__.py
│   └── plan_workflow.py         # LangGraph StateGraph (RunState, nodes, edges)
├── api/                  # 9 files
│   ├── __init__.py
│   ├── app.py                   # create_app() factory
│   ├── routers/
│   │   ├── materials.py
│   │   ├── plans.py
│   │   └── tutors.py
│   └── streaming/
│       └── sse.py               # SSE utilities
└── app/                  # 2 files (services placeholder)
    └── __init__.py
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large refactor breaks existing behavior | Sprint 0 verified call-sites first |
| Protocol compliance not enforced at import | `@runtime_checkable` + registration checks |
| Over-engineering for pre-MVP stage | Kept container and adapters minimal |
| i18n files missing for some locales | Fallback chain: specific locale -> language -> en |

---

## Completion Summary

All nine stories delivered. The runtime is now organized into a clean hexagonal
architecture: 22 domain entities, 13 port protocols, a Pydantic Settings config,
a frozen-dataclass DI container, structured error handling with i18n, structlog
observability, a refactored LangGraph workflow, modular API routers with SSE
streaming, and five concrete adapter implementations.

---

## Remaining Work (Code Review — Feb 11)

A comprehensive code review identified 17 issues that must be resolved before
Sprint 2. These are tracked in `control_docs/TODO.md` under
"Sprint 1 — Completion Fixes (Code Review)" (items S1-FIX-01 through S1-FIX-17).

**Critical (3):** Protocol/adapter signature mismatches, duplicate tutor models,
legacy config imports in routers.

**High (5):** Incomplete container wiring, legacy api_app.py, duplicate plan models,
LearnerProfile collision, no-op protocol check.

**Medium (6):** `\\n` join bug in exports, client-per-call in OpenAI/Gemini adapters,
deprecated utcnow(), embedding dimensions inconsistency, SECURITY.md vs ADR
contradiction, CORS misconfiguration.

**Low (3):** Inline __import__, duplicate SupportIntensity, logging handler leak.
