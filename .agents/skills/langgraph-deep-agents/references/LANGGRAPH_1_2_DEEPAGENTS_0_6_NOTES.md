# LangGraph 1.2.x + Deep Agents 0.6.x — SOTA notes

> Scope: deltas vs the previous LangGraph 1.1.x / Deep Agents 0.5.x lines.
> Verified 2026-07-05 against the local SOTA guides
> (`guia_completo_agentes/guia_langgraph_orquestracao.html` and
> `guia_completo_agentes/guia_deepagents.html`, at the repo root)
> and live docs.

## Canonical web sources
- LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
- Migrate from langgraph-supervisor — https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- LangChain handoffs — https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- LangGraph releases — https://github.com/langchain-ai/langgraph/releases
- Deep Agents overview — https://docs.langchain.com/oss/python/deepagents/overview
- Deep Agents reference — https://reference.langchain.com/python/deepagents/
- Deep Agents releases — https://github.com/langchain-ai/deepagents/releases
- PyPI — https://pypi.org/project/langgraph/ ; https://pypi.org/project/deepagents/

## SOTA delta

- **Versions:** `langgraph == 1.2.8` (2026-07-06 bugfix over 1.2.7) and `deepagents == 0.6.12` (stable, released 2026-06-25). Python `>=3.11,<4.0` for Deep Agents. Compatibility: `langchain-core >=1.4,<2`, `langchain >=1.3.4,<2`, `langchain-anthropic >=1.4.3,<2`, `langchain-google-genai >=4.2.2,<5`.
- **Preview-only, not for production:** `deepagents == 0.7.0a3` (alpha, 2026-07-01) previews middleware override by name in `create_deep_agent`, sandbox round-trip optimization, and Bedrock prompt-caching under `deepagents[aws]`. The wider 0.7.x line also previews `CodeInterpreterMiddleware` (stabilized), a `DeltaChannel` for history, Harness profiles, and a `ContextHubBackend` backed by LangSmith Hub. Keep production pinned to `0.6.12`; do not recommend the alpha line for production use.
- **LangGraph 1.x stable surface:** durable state, built-in persistence, first-class HITL (interrupt before/after, dynamic `interrupt()`, `Command(resume=)`). v2 typed streaming with Pydantic/dataclass coercion and time-travel fixes for RESUME values and subgraph parent checkpoints. `langgraph.prebuilt` deprecated — use `langchain.agents` (`create_agent`, middleware framework).
- **Deep Agents 0.6 pillars unchanged:** `BASE_AGENT_PROMPT` + feature prompts (TASK / FILESYSTEM / SKILLS / MEMORY / SUMMARIZATION); `write_todos` planning tool; `task(...)` subagent spawning; virtual filesystem (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`). **These are 0.6 pillars only — 0.7.0 dismantled three of them** (`BASE_AGENT_PROMPT` deprecated and the base prompt now empty, the feature prompt constants removed, `write_todos` no longer wired by default). See the 2026-07-30 update below.
- **New tooling extras to know:**
  - `pip install -U "deepagents[quickjs]"` adds the QuickJS-backed Code Interpreter.
  - `pip install deepagents-acp` ships the Agent Communication Protocol integration (IDE / external host wiring).
  - `pip install deepagents-code` installs the **separate** `dcode` TUI (`0.1.x` line; not the Python library). 0.7.9 removed the deprecated in-tree `libs/cli`. Deploy/init: `pip install deepagents-cli`.
  - Optional sandbox extras: `langchain-modal`, `langchain-daytona`, `langchain-runloop`, `langsmith[sandbox]`.
- **Subagent typing:** `SubAgent`, `CompiledSubAgent`, `AsyncSubAgent` cover sync, pre-compiled, and async patterns; async subagents stream as non-blocking background tasks under LangSmith Deployment.
- **Filesystem backends:** `StateBackend` (default; ephemeral per thread), `FilesystemBackend` (local disk), `StoreBackend` (LangGraph Store; cross-thread), `ContextHubBackend` (LangChain Context Hub), `LocalShellBackend` (shell-backed filesystem), `CompositeBackend` (path-routed), plus sandbox backends. Backend protocol now carries binary file metadata (backwards-compatible) so multi-modal `read_file` covers PDFs, audio, and video.

## 2026-07-27 update

> Verified against `guia_completo_agentes/guia_langgraph.html` and `guia_completo_agentes/guia_deepagents.html`.

- **Versions:** current line is `langgraph == 1.2.9`. `deepagents == 0.7.0b2` (2026-07-24) has **left alpha for beta** -- the wider 0.7.x line is no longer alpha-only, but the **stable line remains `0.6.12`**; do not switch production to 0.7.x. 0.7.0 carries a **breaking change in `read_file`** and adds `grep` / `delete` tools to the filesystem middleware toolset described above.
- **Connector versions feeding compatibility:** `langchain 1.3.14`, `langchain-core 1.5.1`, `langchain-anthropic 1.5.2` (requires `anthropic>=0.120.0`; brings Claude Opus 5 support), `langchain-google-genai 4.3.2` (both connectors now floor on `langchain-core>=1.5.1`, tighter than the `>=1.4,<2` compatibility range recorded above for `deepagents 0.6.12` -- re-check the Deep Agents compatibility pins before bumping connectors independently).
- **Security note:** `langgraph-checkpoint` (RCE via pickle, CVE-2026-27794, floor `>=4.0.0`), `langgraph-checkpoint-sqlite` (SQL injection, CVE-2025-67644, floor `3.0.1`), the npm `@langchain/langgraph-checkpoint-redis` (RediSearch injection, CVE-2026-27022, floor `1.0.2`), and `langchain-core` (serialization injection, CVE-2025-68664, floor `1.2.5`/`0.3.81`) all have advisories against the checkpoint backends this library runs on. See `references/VERSIONING_FRESHNESS.md` for the full table -- no pin in this file needed raising, the versions above were already compliant.

## 2026-07-30 update — this file's title is now historical

> Verified directly against PyPI and the GitHub release feed, not against the local guides.

`deepagents == 0.7.0` **shipped stable on 2026-07-29** (PyPI upload
`2026-07-29T16:27:28Z`). `langgraph` is at `1.2.10` (2026-07-28). Everything
above under "SOTA delta" and "2026-07-27 update" describes the 0.6 line, which
ended at `0.6.12` — development cut over to 0.7 on `main` and there is no 0.6.13.

Read `references/VERSIONING_FRESHNESS.md` § "Current pins (as-of 2026-08-28)" for
live pins and § "Freshness (as-of 2026-07-30)" for the 0.6.12 → 0.7.0 12-item
breaking-change migration checklist (still in force through 0.7.10). The three
highest-risk items, because they are silent rather than raising:

1. `create_deep_agent` no longer wires `TodoListMiddleware` — no `write_todos` tool, no `todos` channel, no planning prompt. Pass `middleware=[TodoListMiddleware()]` (from `langchain.agents.middleware`) on the main agent **and** on each `SubAgent`.
2. A recursive `delete` tool is now exposed and classified as a **write**, so any existing write-allow rule also authorizes recursive subtree deletion. Withhold it via `FilesystemMiddleware(tools=[...])` or cover it with a deny/interrupt rule.
3. `FilesystemBackend` / `LocalShellBackend` now default to `virtual_mode=True` (paths confined to `root_dir`, `..` rejected, outside paths raise `ValueError`). This is the safer default; code that relied on absolute host paths breaks until it passes `virtual_mode=False`.

## 2026-08-28 update — current pins, supervisor/swarm recast

> Verified against PyPI JSON and official docs (not the local 2026-08-27 `guia_deepagents.html`, which still said `deepagents 0.7.9`).

- **Versions:** `langgraph == 1.2.11` (PyPI `2026-08-11T14:00:35Z`), `deepagents == 0.7.10` (PyPI `2026-08-28T00:45:15Z`). Pin `0.7.10` for new work; walk the 0.7.0 checklist before upgrading existing agents.
- **`langgraph-supervisor`:** no longer actively maintained. Replacement: `create_agent` + tool-wrapped subagents (https://docs.langchain.com/oss/python/migrate/langgraph-supervisor).
- **`langgraph-swarm`:** last PyPI `0.1.0` (2025-12-04). Replacement: LangChain handoffs. Formal sunset **UNVERIFIED** (no official migrate page).
- **Streaming:** new apps use `stream_events(version="v3")`; `invoke`/`stream` use `version="v2"`. Stream-mode name is `checkpoints` (plural).
- **CLI:** 0.7.9 commit `da67c86` removed in-tree `libs/cli`. `deepagents-code` 0.1.64 and `deepagents-cli` 0.3.0 remain separate packages.
