# LangGraph Deep Agents — Versioning and Freshness

Full source list, version pins, and SOTA deltas. LangGraph APIs evolve
frequently — always verify import paths, class names, and method signatures
against the latest docs before shipping user code. Do not hardcode minor
versions in user code.

## Official docs and sources

- **Official docs**: https://langchain-ai.github.io/langgraph/
- **GitHub (LangGraph)**: https://github.com/langchain-ai/langgraph
- **GitHub (Deep Agents)**: https://github.com/langchain-ai/deepagents (MIT license -- verify star count and version at source)
- **Deep Agents PyPI**: https://pypi.org/project/deepagents/
- **Deep Agents CLI**: https://pypi.org/project/deepagents-cli/
- **LangSmith Deployment**: https://www.langchain.com/langsmith/deployment
- **Supervisor library**: https://github.com/langchain-ai/langgraph-supervisor-py
- **Swarm library**: https://github.com/langchain-ai/langgraph-swarm-py

## Deep Agents standalone library

Deep Agents is a standalone library (not merged into LangGraph core) built on
LangGraph runtime. Provides planning (write_todos), subagent spawning (task
tool), filesystem backends (in-memory/disk/LangGraph store/sandboxes),
long-term memory, HITL, and auto-summarization. CLI available separately.

## Key recent additions

- **LangGraph 1.0 GA**: durable state + built-in persistence + first-class HITL as stable primitives; only notable breaking change is the deprecation of `langgraph.prebuilt` — enhanced functionality moved to `langchain.agents`.
- **LangGraph v1.2.7** (current as of 2026-06-30, bugfix release over 1.2.6): builds on v1.1.x Deep Agent templates and distributed runtime support in the CLI; v2 type-safe streaming/invoke with Pydantic/dataclass coercion and time-travel fixes for RESUME values and subgraph parent checkpoints; model retry middleware, content moderation middleware (OpenAI), `SystemMessage` support in `create_agent`, summarization middleware, HITL middleware; pluggable sandbox integrations (Modal, Daytona, Runloop).
- **Deep Agents `0.6.12`** (stable, 2026-06-25): adds `BedrockPromptCachingMiddleware`. Prior 0.6.x history: 0.6.9 configurable subagent response format; 0.6.7 exported `DeepAgentState` + `Command` propagates `goto`/graph; 0.6.5 `RubricMiddleware`; 0.6.0 `DeltaChannel` + event streaming v2. Also carries async subagents, multi-modal `read_file`, backend protocol update for binary files, `dcode` CLI, and ACP integration.
- **Deep Agents `0.7.0a3`** (alpha/preview only, 2026-07-01): middleware override by name in `create_deep_agent`, sandbox round-trip optimization, Bedrock prompt-caching via `deepagents[aws]`; the 0.7.x line also previews `CodeInterpreterMiddleware`, a `DeltaChannel` for history, Harness profiles, and `ContextHubBackend` (LangSmith Hub). Preview only -- keep production pinned to `0.6.12`.
- **Functional API** (`@entrypoint`, `@task`) available alongside the graph API for imperative-style durable workflows — verify the current surface against the LangGraph changelog.
- LangGraph `version="v2"` streaming returns typed `StreamPart` dicts; invoke returns `GraphOutput` with `.value` and `.interrupts`. Default remains v1 for backwards compatibility. Incremental adoption supported.
- LangGraph Platform renamed to LangSmith Deployment (October 2025). Self-hosted options: lite (free), enterprise (in-VPC), hybrid BYOC.
- Checkpointer backends: MemorySaver (dev), SqliteSaver, PostgresSaver (prod recommended), DynamoDBSaver (AWS), MongoDB, Redis.
- Known limitation: `middleware` and custom `state_schema` mutually exclusive in `create_agent()`.
- Comparison: LangGraph = production-grade stateful (best observability via LangSmith). CrewAI = fastest time-to-production. AutoGen = maintenance mode. Deep Agents = complex multi-step tasks with context isolation.

## Freshness (as-of 2026-07-05)

Verified against the local SOTA guides `guia_completo_agentes/guia_langgraph_orquestracao.html` and `guia_completo_agentes/guia_deepagents.html`.

- **LangGraph docs (Python)**: https://docs.langchain.com/oss/python/langgraph/overview — **LangGraph 1.0 is GA** (durable state, built-in persistence, first-class HITL; `langgraph.prebuilt` deprecated in favor of `langchain.agents`). Current line: **`langgraph 1.2.8`** (2026-07-06 bugfix over 1.2.7). Checkpointers: MemorySaver, SqliteSaver, PostgresSaver, DynamoDBSaver, MongoDB, Redis.
- **LangGraph GitHub + releases**: https://github.com/langchain-ai/langgraph/releases and https://changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available (verify latest minor version at release time; do not hardcode in user code).
- **Deep Agents**: https://docs.langchain.com/oss/python/deepagents/overview and https://reference.langchain.com/python/deepagents/ ; releases: https://github.com/langchain-ai/deepagents/releases ; PyPI: https://pypi.org/project/deepagents/ (standalone library built on LangGraph runtime; **current stable line `deepagents == 0.6.12` released 2026-06-25**, Python `>=3.11,<4.0`). Compatibility: `langchain-core >=1.4,<2`, `langchain >=1.3.4,<2`, `langchain-anthropic >=1.4.3,<2`, `langchain-google-genai >=4.2.2,<5`. A **preview-only** `0.7.0a3` alpha (2026-07-01) adds middleware override by name, sandbox round-trip optimization, Bedrock prompt-caching (`deepagents[aws]`), and (0.7.x line) `CodeInterpreterMiddleware`, `DeltaChannel` history, Harness profiles, `ContextHubBackend` (LangSmith Hub) -- not for production. Extras: `deepagents[quickjs]` (Code Interpreter), `deepagents-acp` (IDE/ACP integration), `deepagents-code` (`dcode` CLI). April–May 2026 updates: async subagents (needs LangSmith Deployment), multi-modal `read_file` (PDF/audio/video), backend protocol update for binary files.
- **Supervisor**: https://github.com/langchain-ai/langgraph-supervisor-py ; **Swarm**: https://github.com/langchain-ai/langgraph-swarm-py
- **LangSmith Deployment** (was LangGraph Platform, rename Oct 2025): https://www.langchain.com/langsmith/deployment
- **MCP tools adapter** for LangChain/LangGraph: https://github.com/langchain-ai/langchain-mcp-adapters
- **OpenTelemetry GenAI semconv** (Development/Experimental) for tracing nodes/tools: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- **OWASP LLM Top 10 2025 relevance** (LLM06 Excessive Agency, LLM10 Unbounded Consumption): enforce interrupt_before on destructive nodes, cap iteration counts, scope cross-thread Store namespaces. https://genai.owasp.org/llm-top-10/
- **Runtime defaults** (repo policy): Python 3.13 via `uv` / `.python-version` (Python 3.14 only if project explicitly opts in). Deep Agents CLI tested under this runtime.
- **Model reference** in example (`init_chat_model("openai:gpt-5.4-mini")`) aligns with repo CLAUDE.md model family (gpt-5.5 / gpt-5.4-mini / gpt-5.4-nano; also Opus 4.8, **Sonnet 5 (recommended)** / Sonnet 4.6 (legacy), Haiku 4.5; gemini-3.1-pro-preview, gemini-3.5-flash). All Deep Agents code examples in the guide now pass `model="anthropic:claude-sonnet-5"` explicitly (model default resolves via `HarnessProfile`/`init_chat_model`, but pin the ID explicitly in code). **Passthrough caveat:** `langchain-anthropic` accepts any model string via passthrough (no enum validation), so `"anthropic:claude-sonnet-5"` works -- but the last published connector (`1.4.8`, 2026-06-26) predates Sonnet 5's GA (2026-06-30), and no changelog confirms tested support for Sonnet-5-specific beta features (new tokenizer, beta headers). Validate with a real call before production; track `langchain-anthropic` releases newer than `1.4.8`.
