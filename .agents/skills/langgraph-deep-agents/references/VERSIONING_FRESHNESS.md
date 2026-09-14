# LangGraph Deep Agents — Versioning and Freshness

Full source list, version pins, and SOTA deltas. LangGraph APIs evolve
frequently — always verify import paths, class names, and method signatures
against the latest docs before shipping user code. Do not hardcode minor
versions in user code. Dated reconciliation history lives in `CHANGELOG.md`.

## Official docs and sources

- **Official docs**: https://docs.langchain.com/oss/python/langgraph/
- **Event streaming (v3)**: https://docs.langchain.com/oss/python/langgraph/event-streaming
- **Stream-mode API (v2)**: https://docs.langchain.com/oss/python/langgraph/streaming
- **GitHub (LangGraph)**: https://github.com/langchain-ai/langgraph
- **GitHub (Deep Agents)**: https://github.com/langchain-ai/deepagents (MIT license -- verify star count and version at source)
- **Deep Agents docs**: https://docs.langchain.com/oss/python/deepagents/overview
- **Deep Agents changelog**: https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md
- **Deep Agents PyPI**: https://pypi.org/project/deepagents/
- **Deep Agents CLI (deploy/init)**: https://pypi.org/project/deepagents-cli/
- **dcode TUI (`deepagents-code`)**: https://pypi.org/project/deepagents-code/
- **LangSmith Deployment**: https://www.langchain.com/langsmith/deployment
- **`create_agent`**: https://reference.langchain.com/python/langchain/agents/factory/create_agent
- **Subagents pattern**: https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
- **Migrate from langgraph-supervisor** (package no longer actively maintained): https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- **LangChain handoffs** (swarm replacement): https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- **Supervisor library (legacy)**: https://github.com/langchain-ai/langgraph-supervisor-py
- **Swarm library (legacy)**: https://github.com/langchain-ai/langgraph-swarm-py
- **MCP tools adapter** for LangChain/LangGraph: https://github.com/langchain-ai/langchain-mcp-adapters
- **OpenTelemetry GenAI semantic conventions** (Development/Experimental), for tracing nodes/tools: https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Deep Agents standalone library

Deep Agents is a standalone library (not merged into LangGraph core) built on
LangGraph runtime. Provides planning (`write_todos`, **opt-in since 0.7.0**),
subagent spawning (task tool), filesystem backends
(in-memory/disk/LangGraph store/sandboxes), long-term memory, HITL, and
auto-summarization. CLIs are **separate packages** — see Current pins.

## Key recent additions

- **LangGraph 1.0 GA**: durable state + built-in persistence + first-class HITL as stable primitives; only notable breaking change is the deprecation of `langgraph.prebuilt` — enhanced functionality moved to `langchain.agents`.
- **LangGraph 1.2.x**: builds on v1.1.x Deep Agent templates and distributed runtime support in the CLI; v2 type-safe streaming/invoke with Pydantic/dataclass coercion and time-travel fixes for RESUME values and subgraph parent checkpoints; **event streaming** `stream_events(version="v3")` with typed projections; model retry middleware, content moderation middleware (OpenAI), `SystemMessage` support in `create_agent`, summarization middleware, HITL middleware; pluggable sandbox integrations (Modal, Daytona, Runloop). Current measured line is **1.2.11** (2026-08-11) — no 1.2.11-specific API break was published in the sources checked 2026-08-28.
- **`create_react_agent` is deprecated.** Use `from langchain.agents import create_agent` with `system_prompt=` (not `prompt=`). Official migrate: https://docs.langchain.com/oss/python/migrate/langgraph-v1
- **`langgraph-supervisor` is no longer actively maintained.** Replacement: `create_agent` + subagents as `@tool`. Official: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
- **`langgraph-swarm` last PyPI `0.1.0` (2025-12-04).** Replacement: LangChain handoffs. There is **no** official `migrate/langgraph-swarm` page; formal sunset **UNVERIFIED**.
- **Deep Agents `0.6.12`** (2026-06-25, end of the 0.6 line -- see "Current pins" below): adds `BedrockPromptCachingMiddleware`. Prior 0.6.x history: 0.6.9 configurable subagent response format; 0.6.7 exported `DeepAgentState` + `Command` propagates `goto`/graph; 0.6.5 `RubricMiddleware`; 0.6.0 `DeltaChannel` + event streaming v2. Also carries async subagents, multi-modal `read_file`, backend protocol update for binary files, `dcode` CLI, and ACP integration.
- **Functional API** (`@entrypoint`, `@task`) available alongside the graph API for imperative-style durable workflows — verify the current surface against the LangGraph changelog.
- LangGraph `version="v2"` on `stream`/`invoke` returns typed `StreamPart` dicts `{type, ns, data}`; invoke returns `GraphOutput` with `.value` and `.interrupts`. Default remains v1 for backwards compatibility. Incremental adoption supported. Official stream-mode name is **`checkpoints`** (plural).
- LangGraph Platform renamed to LangSmith Deployment (October 2025). Self-hosted options: lite (free), enterprise (in-VPC), hybrid BYOC.
- Checkpointer backends: `InMemorySaver` (dev; `MemorySaver` is the same in-RAM class — official persistence examples use `InMemorySaver`), SqliteSaver, PostgresSaver (prod recommended), DynamoDBSaver (AWS), MongoDB, Redis.
- Known limitation: `middleware` and custom `state_schema` mutually exclusive in `create_agent()`.
- Comparison: LangGraph = production-grade stateful (best observability via LangSmith). CrewAI = fastest time-to-production. AutoGen = maintenance mode. Deep Agents = complex multi-step tasks with context isolation.

## Operational and security references

- **OWASP LLM Top 10 2025 relevance** (LLM06 Excessive Agency, LLM10 Unbounded Consumption): enforce `interrupt_before` on destructive nodes, cap iteration counts, scope cross-thread Store namespaces. https://genai.owasp.org/llm-top-10/
- **Runtime defaults** (repo policy): Python 3.13 via `uv` / `.python-version` (Python 3.14 only if the project explicitly opts in). Deep Agents CLI tested under this runtime.

## Security advisories — checkpoint and serialization backends (re-checked 2026-08-28)

This skill's checkpointer guidance (`InMemorySaver` / `MemorySaver`, `SqliteSaver`, `PostgresSaver`, `DynamoDBSaver`, MongoDB, Redis in `references/LANGGRAPH_CORE_PATTERNS.md`) already names package versions above every floor below — pin above the floor, not just above what the guidance names.

| Advisory | Package | Nature | Floor |
|---|---|---|---|
| CVE-2025-68664 | `langchain-core` | **CRITICAL** -- unescaped `lc` key in `dumps`/`dumpd` allows secret extraction at `loads` (serialization injection). Reintroduced in the 1.0 line, hence two fix versions. | **1.2.5** and **0.3.81** |
| CVE-2026-27794 | `langgraph-checkpoint` | RCE via pickle in caching (`BaseCache` defaulted to `JsonPlusSerializer(pickle_fallback=True)`). GHSA-mhr3-j7m5-c7c9. | **>=4.0.0** |
| CVE-2026-28277 | `langgraph` / `langgraph-checkpoint` (msgpack deserialization in checkpoint load) | Unsafe msgpack object reconstruction. **Patched** (Check Point Research 2026-06-11; CSA note 2026-06-15). | **`langgraph >=1.0.10`**, **`langgraph-checkpoint >=4.0.1`** |
| CVE-2025-67644 | `langgraph-checkpoint-sqlite` | SQL injection via filter **key** | **3.0.1** |
| CVE-2026-27022 | **npm** `@langchain/langgraph-checkpoint-redis` | RediSearch injection | **1.0.2** (not 1.0.1) |
| CVE-2026-71433 | `langgraph-checkpoint-postgres` and `langgraph-checkpoint-sqlite` | Namespace prefix matching crosses segment boundaries (`LIKE '<path>%'` on dot-joined namespaces) — scoped Store `search` / `list_namespaces` can return another tenant's items. GHSA-47pj-3jcm-6whg. | **3.1.1** |

Note: `langgraph-checkpoint-redis` is **0.5.2 on PyPI** (measured 2026-08-28) and **1.0.x on npm** -- independent numbering, not a contradiction. CVE-2026-27022 targets the **npm** package; the PyPI package is a different artifact.

Cross-reference: the broader AI/ML supply-chain advisory set for this sweep (`google-adk` CVE-2026-4810, `pydantic-ai` CVE-2026-65975, the Starlette-not-FastMCP CVE-2026-48710) lives in `skills/code-quality/security-ai-ml-llm/SKILL.md` -- not repeated here because this skill does not recommend those packages.

Measured current backends (PyPI 2026-08-28, not yanked): `langgraph-checkpoint 4.2.0`, `langgraph-checkpoint-sqlite 3.1.1`, `langgraph-checkpoint-postgres 3.1.2`, `langgraph-checkpoint-redis 0.5.2`. All sit above the floors above.

## Current pins (as-of 2026-08-28) — `deepagents 0.7.10`, no extra silent break since 0.7.0

- **`deepagents 0.7.10`** is current on PyPI, published `2026-08-28T00:45:15Z` (measured directly via `pypi.org/pypi/deepagents/json`). GitHub compare: `deepagents==0.7.9...deepagents==0.7.10`.
- **`langgraph 1.2.11`** is current (PyPI upload `2026-08-11T14:00:35Z`, measured directly via `pypi.org/pypi/langgraph/json`). Requires `langchain-core>=1.4.7,<2`, `langgraph-checkpoint>=4.1.0,<5`, `langgraph-prebuilt>=1.1.0,<1.2`, `langgraph-sdk>=0.4.2,<0.5`.
- **0.7.10 dependency floors** (PyPI `requires_dist`, measured 2026-08-28): `langchain>=1.3.18,<2.0.0`, `langchain-core>=1.6.1,<2.0.0`, `langchain-anthropic>=1.7.0,<2.0.0`, `langchain-google-genai>=4.3.7,<5.0.0`, `langsmith>=0.11.1`, `packaging>=23.2`, `wcmatch>=11.0`. Extras: `aws` -> `langchain-aws>=1.7.4,<2.0.0`; `quickjs` -> `langchain-quickjs>=0.3.5`; `video` -> `av>=18.0.0,<19.0.0` + `pillow>=12.3.0,<13.0.0`.
- Companion measured versions (same day, not yanked): `langchain 1.3.18` (requires `langgraph>=1.2.11,<1.3`), `langchain-core 1.6.1`, `langchain-anthropic 1.7.0`, `langchain-google-genai 4.3.7`.
- `mcp` and `langgraph` arrive only transitively via `langchain` -- neither is a direct `deepagents` dependency. **No additional silent breaker from `0.7.0` through `0.7.10`** -- the 12-item migration checklist below (0.6.12 -> 0.7.0) is the operative migration guide.
- **0.7.6–0.7.10 notes** (official Deep Agents CHANGELOG; not silent 0.7.0-class breakers):
  - **0.7.6** (2026-08-13): offload conversation history to a distinct session ID when summarizing.
  - **0.7.7** (2026-08-18): batched concurrent `ContextHubBackend` mutations; `BackendProtocol.glob` recursive for bare patterns.
  - **0.7.8** (2026-08-20): add `files` state only for state backends.
  - **0.7.9** (2026-08-25): disable tracing inputs on middleware; honour `excluded_tools` in harness profiles; enforce full criterion coverage in `RubricMiddleware`; clarify zero execute-timeout semantics. Repo commit `da67c86` removed the deprecated in-tree `libs/cli` package (not the separate PyPI CLIs).
  - **0.7.10** (2026-08-28): prevent local shell commands from stealing TUI input; surface sandbox glob failures instead of reporting no matches.
- **CLIs are not the library.** `deepagents-code` (`dcode` TUI) is a separate PyPI package on its own `0.1.x` line — measured **0.1.64** (2026-08-28T01:16Z), pins `deepagents==0.7.10`. `deepagents-cli` is the deploy/init CLI — measured **0.3.0** (2026-08-24). `deepagents-acp` measured **0.0.11**. Do not read a version from one line into another. Do not `pip install deepagents-code` expecting the Python library.
- **`langchain-anthropic 1.7.x`** accepts model strings via passthrough (no enum validation): `model="anthropic:claude-sonnet-5"` and `model="anthropic:claude-opus-5"` both resolve. Validate any newly-referenced model ID with a real call before production. **Do not invent newer model IDs.**
- **Companion libraries (legacy):** `langgraph-supervisor 0.0.31` last upload **2025-11-19**; `langgraph-swarm 0.1.0` last upload **2025-12-04**. Both still declare `langchain-core` `<2`, so pip can resolve a common version, but **do not start new work on them**. Official replacement is `create_agent` + subagents / LangChain handoffs. Runtime API compatibility of those two packages against the current deepagents line has not been exercised.
- **Pin `0.7.10` for new work** -- same stable line as `0.7.0`, no additional silent breaker reported since. `0.6.12` (2026-06-25) is the end of the 0.6 line, not a maintained LTS (`main` cut over to 0.7 at commit `965cbd5`; there is no 0.6.13). Freezing on `0.6.12` is a legitimate short-term choice only when recorded as "frozen on an end-of-line release pending 0.7 migration" -- never as "0.7 isn't ready", which is no longer true.

## Freshness (as-of 2026-07-30) — deepagents 0.7.0 is STABLE

`deepagents 0.7.0` shipped stable on 2026-07-29 (PyPI upload `2026-07-29T16:27:28Z`; GitHub release tag `deepagents==0.7.0`; curated notes at https://docs.langchain.com/oss/python/releases/changelog#deepagents-v0-7-0). Progression was `0.7.0a7` (07-14) → `a8` (07-22) → `b1` (07-23) → `b2` (07-24) → `0.7.0` (07-29). This section holds the 0.6.12 → 0.7.0 migration checklist; see "Current pins" above for the version currently shipping.

### Pin decision (state the reason, not just the number)

- Pinning `0.7.0` (or the current `0.7.10`, see "Current pins" above) is correct for new work, and correct for existing work **after** the migration checklist below is walked.
- Pinning `==0.6.12` is defensible only as a short, explicit freeze while migrating — record it as "frozen on an end-of-line release pending 0.7 migration", never as "0.7 is not ready": 0.6.x gets no further fixes.
- Track https://github.com/langchain-ai/deepagents/releases for the next breaking release; a first patch after a breaking major is the usual shakeout point.

### 0.6.12 → 0.7.0 migration checklist (breaking, from the release notes)

Silent behaviour changes — these do not raise on import:

1. **`create_deep_agent` no longer includes `TodoListMiddleware`.** The `write_todos` tool, the `todos` state channel, and the todo-planning prompt are all absent by default. Restore with `middleware=[TodoListMiddleware()]` (`from langchain.agents.middleware import TodoListMiddleware` — it is a LangChain middleware, not a `deepagents` one), and add it to **each** `SubAgent`'s middleware to restore it there too. (#4929)
2. **Default prompts are now lean.** The authored base prompt is empty and tool-usage prose that duplicated tool schemas is trimmed. `BASE_AGENT_PROMPT` is deprecated (removal in `deepagents==0.9.0`) but still importable and still returns the old text verbatim: `create_deep_agent(system_prompt=BASE_AGENT_PROMPT)` restores previous behaviour. (#4859, #4979)
3. **`write_file` creates-or-replaces.** It no longer returns a file-exists error, and its description no longer tells the model to read first. There is **no create-only compatibility mode**. Any prompt, test, or guardrail that leaned on the file-exists error to force `edit_file` must instead omit `write_file`, add an explicit permission/interrupt rule, or use `edit_file` where existing content must survive. (#4109)
4. **`delete` is now exposed to the model** whenever the backend supports it, is recursive, and is classified as a **write**. An existing rule that allows writes to a path therefore also authorizes recursively deleting that subtree unless a narrower deny/interrupt rule covers the target. Deny and interrupt checks switched to bulk path overlap (not exact-path) because deletes affect descendants. To keep old behaviour: add a deny/interrupt rule, or omit `delete` from `FilesystemMiddleware(tools=...)`. `CompositeBackend` raises unsupported-operation when a routed sub-backend cannot delete; the tool is hidden entirely when the backend does not implement it. (#3659, #3691, #3765, #3851)
5. **`FilesystemBackend` and `LocalShellBackend` default to `virtual_mode=True`.** Paths are anchored under `root_dir`, `..` traversal is rejected, and paths resolving outside `root_dir` raise `ValueError`. Previously an unspecified `virtual_mode` warned and fell back to `False`, where absolute host paths were used as-is and `..` could escape. Pass `virtual_mode=False` explicitly to restore the old (unconfined) behaviour — prefer not to. (#4541)

Hard breaks — these raise:

6. **Backend compatibility shims removed.** Pass concrete `BackendProtocol` instances (not factories); give `StoreBackend` an explicit `namespace`; use `ls` / `glob` / `grep` / `ReadResult`. Removed: `ls_info`, `als_info`, `glob_info`, `aglob_info`, `grep_raw`, `agrep_raw`. (#4541)
7. **`files_update` removed** from `WriteResult` and `EditResult` (attribute and constructor keyword). Custom backends must stop passing `files_update=`; callers must stop reading `result.files_update`. `StateBackend` emits state writes directly. (#4541)
8. **`SummarizationMiddleware(history_path_prefix=...)` removed** — now raises `TypeError`. Use `CompositeBackend(artifacts_root=...)`. (#4541)
9. **Prompt constants removed:** `TASK_SYSTEM_PROMPT`, `ASYNC_TASK_SYSTEM_PROMPT`, `SUMMARIZATION_SYSTEM_PROMPT`, `FILESYSTEM_SYSTEM_PROMPT`, `EXECUTION_SYSTEM_PROMPT`. The `system_prompt` default on `SubAgentMiddleware`, `AsyncSubAgentMiddleware`, `SummarizationToolMiddleware`, and `create_summarization_tool_middleware` is now `None` (injects no prose). Pass your own string to restore text. (#4859)
10. **`LINE_NUMBER_WIDTH` removed** from `deepagents.backends.utils` and `deepagents.middleware.filesystem`. (#4561)

Output-format breaks — only bite code that parses agent-facing tool output:

11. **`ls` / `glob` render empty results as `No files found`**, not `[]`. Direct backend APIs still return structured empty `LsResult` / `GlobResult`. (#3709)
12. **`read_file` dropped the fixed-width `cat -n` gutter.** Line and continuation markers are dynamically aligned and separated from source by two spaces. (#4561) — this is the "breaking change in `read_file`" the earlier entries referred to, now pinned down precisely.

### 0.7.0 additions worth adopting

- **`FilesystemMiddleware(tools=[...])`** — keyword-only allowlist of built-in filesystem tools, typed by the newly exported `FsToolName` literal (`"ls"`, `"read_file"`, `"write_file"`, `"edit_file"`, `"delete"`, `"glob"`, `"grep"`, `"execute"`). Pass `"all"` or omit to keep everything. A list **must** include `"read_file"` or the constructor raises `ValueError`. Omitted built-ins become non-executable; custom user tools are unaffected. This is the supported way to withhold `delete`. (#4325, #4698)
- **Bounded search.** `GrepResult` / `GlobResult` carry a `truncated` flag so backends can return valid partial results at a match cap or deadline, and agent-facing output tells the model to narrow the search. `FilesystemMiddleware(grep_max_count=...)` sets the default cap (`1000`; `None` disables) and the model can override per call via `max_count`; `grep`/`agrep` on `BackendProtocol` and all built-in backends accept keyword-only `max_count`. `FilesystemBackend.grep()` also accepts keyword-only `context_lines`, and its `glob` gains brace expansion (`*.{py,md}`). Local ripgrep output is streamed and cut at the cap. (#4063, #4570, #4706)
- **Middleware override by name** — custom middleware passed to `create_deep_agent(..., middleware=[...])` replaces a default instance when `.name` matches, so `SummarizationMiddleware` can be overridden without also excluding the built-in. (#4251)
- **Paginated `read_file`** reports the returned source-line range and next `offset`, plus total/remaining line counts when the backend knows the file length; resume offsets stay safe when sandbox limits shorten the page. (#4540)
- **`deepagents[video]`** samples video files into JPEG frames for `read_file`, with `offset`/`limit` in seconds. (#4094)
- `RubricMiddleware` accepts any positive `max_iterations` (hard upper bound removed) and emits terminal `max_iterations_reached` instead of a final non-looping `needs_revision`. (#4405, #4406)
- Fireworks prompt-cache session affinity auto-enables when a compatible `langchain-fireworks` is installed; NVIDIA Nemotron 3 Ultra harness profile added. (#4598, #4192, #4455)
- Fix worth knowing: fields marked `PrivateStateAttr` — including those declared via `create_deep_agent(state_schema=...)` — are now kept out of subagent inputs and returned parent-state updates. (#4587)

**Not the same package:** there is an **npm** `deepagents` (JS line, unrelated
version numbers), a separate PyPI `deepagents-code` (the `dcode` TUI, on its
own `0.1.x` line), and a separate PyPI `deepagents-cli` (deploy/init). None is
the Python `deepagents` library this skill covers; do not read a version from
one line into the other.
