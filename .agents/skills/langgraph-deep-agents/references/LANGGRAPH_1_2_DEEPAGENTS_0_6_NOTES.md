# LangGraph 1.2.x + Deep Agents 0.6.x — SOTA notes

> Scope: deltas vs the previous LangGraph 1.1.x / Deep Agents 0.5.x lines.
> Verified 2026-06-04 against the local SOTA guides
> (`guia_completo_agentes/guia_langgraph_orquestracao.html` and
> `guia_completo_agentes/guia_deepagents.html`, at the repo root)
> and live docs.

## Canonical web sources
- LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph multi-agent (supervisor/swarm) — https://docs.langchain.com/oss/python/langgraph/multi-agent
- LangGraph releases — https://github.com/langchain-ai/langgraph/releases
- Deep Agents overview — https://docs.langchain.com/oss/python/deepagents/overview
- Deep Agents reference — https://reference.langchain.com/python/deepagents/
- Deep Agents releases — https://github.com/langchain-ai/deepagents/releases
- PyPI — https://pypi.org/project/langgraph/ ; https://pypi.org/project/deepagents/

## SOTA delta

- **Versions:** `langgraph == 1.2.4` and `deepagents == 0.6.8` (released 2026-06-03). Python `>=3.11,<4.0` for Deep Agents.
- **LangGraph 1.x stable surface:** durable state, built-in persistence, first-class HITL (interrupt before/after, dynamic `interrupt()`, `Command(resume=)`). v2 typed streaming with Pydantic/dataclass coercion and time-travel fixes for RESUME values and subgraph parent checkpoints. `langgraph.prebuilt` deprecated — use `langchain.agents` (`create_agent`, middleware framework).
- **Deep Agents 0.6 pillars unchanged:** `BASE_AGENT_PROMPT` + feature prompts (TASK / FILESYSTEM / SKILLS / MEMORY / SUMMARIZATION); `write_todos` planning tool; `task(...)` subagent spawning; virtual filesystem (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`).
- **New tooling extras to know:**
  - `pip install -U "deepagents[quickjs]"` adds the QuickJS-backed Code Interpreter.
  - `pip install deepagents-acp` ships the Agent Communication Protocol integration (IDE / external host wiring).
  - `pip install deepagents-code` installs the `dcode` CLI for terminal-driven coding workflows.
  - Optional sandbox extras: `langchain-modal`, `langchain-daytona`, `langchain-runloop`, `langsmith[sandbox]`.
- **Subagent typing:** `SubAgent`, `CompiledSubAgent`, `AsyncSubAgent` cover sync, pre-compiled, and async patterns; async subagents stream as non-blocking background tasks under LangSmith Deployment.
- **Filesystem backends:** `StateBackend` (default; ephemeral per thread), `FilesystemBackend` (local disk), `StoreBackend` (LangGraph Store; cross-thread), `ContextHubBackend` (LangChain Context Hub), `LocalShellBackend` (shell-backed filesystem), `CompositeBackend` (path-routed), plus sandbox backends. Backend protocol now carries binary file metadata (backwards-compatible) so multi-modal `read_file` covers PDFs, audio, and video.
