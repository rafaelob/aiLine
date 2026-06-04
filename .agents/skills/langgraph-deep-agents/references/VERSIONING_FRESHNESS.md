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
- **LangGraph v1.2.4** (current as of 2026-06-04): builds on v1.1.x Deep Agent templates and distributed runtime support in the CLI; v2 type-safe streaming/invoke with Pydantic/dataclass coercion and time-travel fixes for RESUME values and subgraph parent checkpoints; model retry middleware, content moderation middleware (OpenAI), `SystemMessage` support in `create_agent`, summarization middleware, HITL middleware; pluggable sandbox integrations (Modal, Daytona, Runloop).
- **Deep Agents `0.6.8`** (2026-06-03): async subagents, multi-modal `read_file`, backend protocol update for binary files, `dcode` CLI, and ACP integration.
- **Functional API** (`@entrypoint`, `@task`) available alongside the graph API for imperative-style durable workflows — verify the current surface against the LangGraph changelog.
- LangGraph `version="v2"` streaming returns typed `StreamPart` dicts; invoke returns `GraphOutput` with `.value` and `.interrupts`. Default remains v1 for backwards compatibility. Incremental adoption supported.
- LangGraph Platform renamed to LangSmith Deployment (October 2025). Self-hosted options: lite (free), enterprise (in-VPC), hybrid BYOC.
- Checkpointer backends: MemorySaver (dev), SqliteSaver, PostgresSaver (prod recommended), DynamoDBSaver (AWS), MongoDB, Redis.
- Known limitation: `middleware` and custom `state_schema` mutually exclusive in `create_agent()`.
- Comparison: LangGraph = production-grade stateful (best observability via LangSmith). CrewAI = fastest time-to-production. AutoGen = maintenance mode. Deep Agents = complex multi-step tasks with context isolation.

## Freshness (as-of 2026-06-04)

Verified against the local SOTA guides `guia_completo_agentes/guia_langgraph_orquestracao.html` and `guia_completo_agentes/guia_deepagents.html`.

- **LangGraph docs (Python)**: https://docs.langchain.com/oss/python/langgraph/overview — **LangGraph 1.0 is GA** (durable state, built-in persistence, first-class HITL; `langgraph.prebuilt` deprecated in favor of `langchain.agents`). Current line: **`langgraph 1.2.4`**. Checkpointers: MemorySaver, SqliteSaver, PostgresSaver, DynamoDBSaver, MongoDB, Redis.
- **LangGraph GitHub + releases**: https://github.com/langchain-ai/langgraph/releases and https://changelog.langchain.com/announcements/langgraph-1-0-is-now-generally-available (verify latest minor version at release time; do not hardcode in user code).
- **Deep Agents**: https://docs.langchain.com/oss/python/deepagents/overview and https://reference.langchain.com/python/deepagents/ ; releases: https://github.com/langchain-ai/deepagents/releases ; PyPI: https://pypi.org/project/deepagents/ (standalone library built on LangGraph runtime; **current line `deepagents == 0.6.8` released 2026-06-03**, Python `>=3.11,<4.0`). Extras: `deepagents[quickjs]` (Code Interpreter), `deepagents-acp` (IDE/ACP integration), `deepagents-code` (`dcode` CLI). April–May 2026 updates: async subagents (needs LangSmith Deployment), multi-modal `read_file` (PDF/audio/video), backend protocol update for binary files.
- **Supervisor**: https://github.com/langchain-ai/langgraph-supervisor-py ; **Swarm**: https://github.com/langchain-ai/langgraph-swarm-py
- **LangSmith Deployment** (was LangGraph Platform, rename Oct 2025): https://www.langchain.com/langsmith/deployment
- **MCP tools adapter** for LangChain/LangGraph: https://github.com/langchain-ai/langchain-mcp-adapters
- **OpenTelemetry GenAI semconv** (Development/Experimental) for tracing nodes/tools: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- **OWASP LLM Top 10 2025 relevance** (LLM06 Excessive Agency, LLM10 Unbounded Consumption): enforce interrupt_before on destructive nodes, cap iteration counts, scope cross-thread Store namespaces. https://genai.owasp.org/llm-top-10/
- **Runtime defaults** (repo policy): Python 3.13 via `uv` / `.python-version` (Python 3.14 only if project explicitly opts in). Deep Agents CLI tested under this runtime.
- **Model reference** in example (`init_chat_model("openai:gpt-5.4-mini")`) aligns with repo CLAUDE.md model family (gpt-5.5 / gpt-5.4-mini / gpt-5.4-nano; also Opus 4.8, Sonnet 4.6, Haiku 4.5; gemini-3.1-pro-preview, gemini-3.5-flash).
