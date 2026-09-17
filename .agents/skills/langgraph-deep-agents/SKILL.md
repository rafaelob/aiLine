---
name: langgraph-deep-agents
description: >-
  Build stateful LangGraph or Deep Agents graphs with checkpointing, HITL and
  streaming. Use when designing StateGraph control flow, durable execution
  with resume-after-failure, human-in-the-loop approval steps, multi-agent
  composition, or Deep Agents subagent delegation. Vendor-neutral topology ->
  agent-orchestration-patterns.
  OpenAI Agents SDK -> openai-agents-sdk-python.
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.4.0
  category: ai-agents
  subcategory: orchestration
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - ai-agents
  - langgraph
  - langgraph-1-2
  - deep-agents
  - dcode
  - acp
  - stategraph
  - orchestration
  - persistence
  - human-in-the-loop
  - streaming
  - multi-agent
  - project_level
  audience: developer
  output_format: markdown
  modality: text
---

# LangGraph Deep Agents

Implementation playbook for building stateful, graph-based AI agent systems using LangGraph. Covers StateGraph construction with typed reducers, persistence with multiple backends, human-in-the-loop workflows (3 interrupt mechanisms), subgraph composition, v2 type-safe streaming (7 modes) plus `stream_events(version="v3")`, short-term and long-term memory, current multi-agent patterns (`create_agent` with tool-wrapped subagents, LangChain handoffs, hierarchical `StateGraph` teams), and the Deep Agents standalone library for hierarchical planning with subagent delegation. `langgraph-supervisor` and `langgraph-swarm` are legacy — do not start new work there.

## Scope

- Building agents that require explicit control flow (conditional branching, loops, cycles)
- Implementing durable execution with checkpointing and resume-after-failure
- Designing human-in-the-loop approval or review workflows (interrupt_before, interrupt_after, dynamic interrupt())
- Composing multi-agent systems: **new work** uses `langchain.agents.create_agent` with subagents wrapped as tools, LangChain handoffs, or nested `StateGraph` teams. `langgraph-supervisor` / `langgraph-swarm` are unmaintained packages — migrate existing graphs, do not start new ones
- Implementing the Deep Agents pattern (create_deep_agent with subagent delegation, filesystem backends, and opt-in `write_todos` planning — see the 0.7.0 note in Step 5)
- Needing both short-term (thread checkpoints) and long-term (cross-thread Store) memory
- Streaming agent execution at token, node, custom event, checkpoint, tasks, or debug granularity (7 modes), or via event streaming `stream_events(version="v3")`
- Deploying graph-based agents to LangSmith Deployment (self-hosted or managed) or embedding in applications

## Inputs to Collect

1. **Agent purpose** -- what problem does the graph solve?
2. **State schema** -- what data flows through the graph (TypedDict, Pydantic model, or dataclass)?
3. **Node design** -- what processing steps are needed (LLM calls, tool execution, data transformation)?
4. **Edge logic** -- what conditions determine the flow between nodes?
5. **Persistence needs** -- InMemorySaver (dev; `MemorySaver` is the same in-RAM class), SQLite, PostgreSQL, DynamoDB, MongoDB, Redis?
6. **Human-in-the-loop** -- which steps require human approval, review, or input?
7. **Multi-agent pattern** -- single agent, `create_agent` + subagents, LangChain handoffs, hierarchical `StateGraph` teams, or Deep Agents? (Not new supervisor/swarm packages.)
8. **Memory requirements** -- thread-scoped (checkpoints), cross-thread (Store), or both?
9. **Streaming needs** -- event streaming (`stream_events` v3) vs stream-mode (`values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, `debug`)?
10. **Deployment target** -- LangSmith Deployment (managed/self-hosted), self-hosted standalone, or embedded?
11. **Deep Agents needs** -- planning via write_todos (opt-in since 0.7.0), subagent spawning, filesystem backend, sandbox? Is the agent allowed to delete files?

## Execution Playbook

Five steps, each with copy-paste code in `references/IMPLEMENTATION_SNIPPETS.md`. Work through them in order; skip steps that do not apply (e.g. single-agent graphs skip Step 4).

1. **State Schema and Graph Structure** — define the state that flows through the graph (TypedDict / Pydantic / dataclass) with the right reducers (no annotation = overwrite; `add_messages` = append + dedup by ID; custom `(old, new) -> merged`), then wire nodes as pure functions returning partial updates and edges (static or conditional via `add_conditional_edges`).
2. **Persistence, Checkpointing, and Streaming** — compile with a `checkpointer` (snapshot per super-step → resume, time-travel, HITL), inspect via `get_state` / `get_state_history`, and stream in one of 7 modes (`values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, `debug`). Opt into `version="v2"` for typed `StreamPart` dicts, `GraphOutput` (`.value` / `.interrupts`), and Pydantic/dataclass coercion. For **new code, prefer `stream_events(version="v3")`** (`graph.stream_events(..., version="v3")`): provides typed projections per channel — `stream.messages`, `stream.values`, `stream.output`, `stream.subgraphs`, `stream.interrupts`, `stream.interrupted`, `stream.extensions` — iterable directly without parsing raw event dicts. `stream.tool_calls` is **not** a default `StateGraph` projection; register `ToolCallTransformer` from `langgraph.prebuilt` (or use LangChain agent streaming). Do not confuse `stream_events` `version="v3"` with `invoke`/`stream` `version="v2"` (those remain valid for `GraphOutput` and interrupt resume). Use `stream.interleave("values", "messages")` to consume multiple projections in arrival order.
3. **Human-in-the-Loop and Memory** — add approval gates via 3 interrupt mechanisms (`interrupt_before`, `interrupt_after`, dynamic `interrupt()` inside nodes), resume with `Command(resume=...)` or `update_state`; use thread checkpoints for short-term memory and a cross-thread `Store` (namespaced by user_id) for long-term memory.
4. **Multi-Agent Patterns** — for **new work**, pick `create_agent` + tool-wrapped subagents (supervisor replacement; official migrate: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor), LangChain handoffs (`Command` tools updating `current_step` / `active_agent`; prefer single agent + middleware), hierarchical teams (nested subgraphs), or Deep Agents (`create_deep_agent`). `langgraph-supervisor` is **no longer actively maintained**. `langgraph-swarm` last published `0.1.0` on 2025-12-04; there is **no** official `migrate/langgraph-swarm` page — treat it as legacy (formal sunset **UNVERIFIED**). Define clear agent boundaries.
5. **Tool Integration, Deep Agents, and Deployment** — wire tools via `ToolNode` + `tools_condition`; **avoid `create_react_agent` from `langgraph.prebuilt`** (deprecated in LangGraph v1, emits `@deprecated` warning; use `from langchain.agents import create_agent` with `system_prompt=` instead of `prompt=`). Configure Deep Agents middleware (filesystem, subagent task tool, and planning) and a filesystem backend (`StateBackend`, `FilesystemBackend`, `StoreBackend`, `ContextHubBackend`, `LocalShellBackend`, `CompositeBackend`, sandboxes); deploy to LangSmith Deployment (managed/lite/enterprise/BYOC), standalone server, or embedded, with LangSmith tracing. **Deep Agents 0.7.0 (stable 2026-07-29) changed three defaults** — still in force through **0.7.10** — `create_deep_agent` no longer wires `TodoListMiddleware` (pass `middleware=[TodoListMiddleware()]` from `langchain.agents.middleware`, on the main agent *and* each `SubAgent`, or the agent silently stops planning); the authored base prompt is now empty (`BASE_AGENT_PROMPT` deprecated, removal in 0.9.0, still importable to restore); and a recursive `delete` tool is exposed and counted as a **write**. Restrict the toolset with `FilesystemMiddleware(tools=[...])` (allowlist typed by `FsToolName`; must include `"read_file"`). Deep Agents 0.6.x middleware additions: **`RubricMiddleware`** (auto-eval loop, 0.6.5); **`CodeInterpreterMiddleware`** (QuickJS JS/TS sandbox, `pip install "deepagents[quickjs]"`, adds `eval` tool, experimental); **`BedrockPromptCachingMiddleware`** (0.6.12). **Breaking 0.6.8:** `SubagentRunStream`, `AsyncSubagentRunStream`, `SubagentTransformer` removed from public exports (were internal beta). HITL via `interrupt_on={"tool_name": True | {"allowed_decisions": [...]}}` (requires `checkpointer`, `version="v2"` in invoke). **PTC security gotcha:** when `CodeInterpreterMiddleware(ptc=["tool"])` is used, tools invoked from inside JS code bypass `interrupt_on` approval workflows — never include HITL-gated tools in the PTC allowlist.

**Read `references/IMPLEMENTATION_SNIPPETS.md`** for the full code for every step. **Read `references/LANGGRAPH_CORE_PATTERNS.md`** (Steps 1-2), **`references/LANGGRAPH_HITL_MEMORY.md`** (Step 3), and **`references/LANGGRAPH_MULTI_AGENT.md`** (Step 4) for conceptual depth.

## Deliverables / Definition of Done

- [ ] State schema defined with appropriate reducers (add_messages, custom)
- [ ] Graph nodes and edges implemented and tested individually
- [ ] Conditional routing logic validated with test cases
- [ ] Checkpointing configured and tested (resume after failure, time-travel)
- [ ] Human-in-the-loop interrupts working (interrupt_before/after, dynamic interrupt())
- [ ] Memory configured (short-term thread checkpoints and/or long-term Store)
- [ ] Multi-agent pattern implemented with clear agent boundaries (if applicable); new work does not depend on `langgraph-supervisor` / `langgraph-swarm`
- [ ] Streaming verified: `stream_events(version="v3")` for new apps, or `invoke`/`stream` `version="v2"` where `GraphOutput` / `StreamPart` is required
- [ ] Tools integrated and tested via ToolNode or `create_agent`
- [ ] Deep Agents configured with appropriate middleware and filesystem backend (if applicable)
- [ ] Deployed to target environment with health checks and observability
- [ ] Graph visualization generated and documented

## Common Pitfalls

1. **Mutable state in nodes** -- Nodes should return new state dicts, not mutate the input state directly.
2. **Missing reducers** -- Without proper reducers (e.g., `add_messages`), state updates overwrite instead of accumulate.
3. **Forgetting checkpointer for HITL** -- Human-in-the-loop requires checkpointing; without it, interrupts lose state. Humans may take hours/days to respond -- persistence is essential.
4. **Infinite loops** -- Conditional edges can create cycles; always include termination conditions.
5. **Over-complex graphs** -- Start simple; add nodes and edges incrementally. Visualize the graph to verify structure.
6. **Ignoring stream modes** -- Different consumers need different stream modes; choose the right one for your UI/API. Use v2 for type safety on `stream`/`invoke`; prefer `stream_events` v3 for new apps.
7. **Tight coupling between subgraphs** -- Subgraphs should communicate via well-defined state interfaces, not shared mutable data.
8. **Using v1 dict access on v2 GraphOutput** -- Old-style `result["key"]` is deprecated since v1.1 (emits `LangGraphDeprecatedSinceV11`), removed in v3.0. Use `result.value` and `result.interrupts`.
9. **In-memory storage in production** -- `InMemorySaver` / `MemorySaver` is ephemeral and local; use PostgresSaver/DynamoDB for production (fault tolerance, multi-worker).
10. **Cross-user memory leakage** -- Always namespace Store memories by user_id to prevent cross-user data leaks. Pin Postgres/SQLite stores at **>=3.1.1** (CVE-2026-71433 namespace prefix matching).
11. **Middleware + custom state_schema** -- Currently mutually exclusive in `create_agent()`; workaround by attaching state to message metadata.
12. **`create_react_agent` from `langgraph.prebuilt` is deprecated** -- LangGraph v1 moved these prebuilts to `langchain.agents`. Use `from langchain.agents import create_agent(model, tools, system_prompt=...)`. Do not start new graphs on `langgraph-supervisor` / `langgraph-swarm`; those packages still call `create_react_agent` internally.
13. **PTC bypasses HITL** -- `CodeInterpreterMiddleware` PTC calls go through the interpreter bridge, not the normal tool calling path. `interrupt_on` approval workflows are NOT enforced for PTC-invoked tools. Never put HITL-gated tools in the PTC allowlist.
14. **Unpatched checkpoint/serialization dependencies carry active CVEs** -- `langgraph-checkpoint` <4.0.0 (pickle RCE, CVE-2026-27794), `langgraph-checkpoint-sqlite` <3.0.1 (SQL injection via filter key, CVE-2025-67644), `langgraph-checkpoint-postgres` / `langgraph-checkpoint-sqlite` <3.1.1 (namespace prefix matching, CVE-2026-71433), the **npm** `@langchain/langgraph-checkpoint-redis` <1.0.2 (RediSearch injection, CVE-2026-27022 -- npm-only; PyPI `langgraph-checkpoint-redis` versions independently at 0.5.x and is not that CVE), and `langchain-core` <1.2.5 / <0.3.81 (serialization injection via unescaped `lc` key in `dumps`/`dumpd`, CVE-2025-68664, reintroduced in the 1.0 line hence two fix versions) are the checkpoint-layer backends this skill recommends. CVE-2026-28277 (msgpack deserialization) is patched in `langgraph` **>=1.0.10** and `langgraph-checkpoint` **>=4.0.1** (Check Point Research, 2026-06-11); current pins sit above those floors. Full advisory table in `references/VERSIONING_FRESHNESS.md`.

15. **Upgrading to `deepagents 0.7.0` (through current `0.7.10`) widens what the agent may destroy, silently.** `delete` is now a real, recursive, model-visible filesystem tool classified as a **write**, so a permission rule that already allowed writes under a path now also authorizes recursively deleting that subtree; deny/interrupt checks moved to bulk path overlap rather than exact-path match. Two more silent flips ship with it: `write_file` creates-or-replaces instead of erroring on an existing file (so any guardrail that relied on the file-exists error to force `edit_file` is gone, with no create-only mode), and `FilesystemBackend`/`LocalShellBackend` default to `virtual_mode=True` (paths confined to `root_dir`, `..` rejected, outside paths raise `ValueError`). Before upgrading, re-read your permission rules against the new semantics, withhold `delete` via `FilesystemMiddleware(tools=[...])` or a deny/interrupt rule, and walk the full 12-item checklist in `references/VERSIONING_FRESHNESS.md`.

## Example Prompts

- "Build a research agent graph with a planner node, parallel research nodes, and a synthesis node."
- "Add human-in-the-loop approval before the agent executes any database write operations using dynamic interrupt()."
- "Implement a supervisor with `create_agent` and tool-wrapped subagents (not langgraph-supervisor) that routes to code, research, and writing specialists."
- "Create conversational handoffs with LangChain `Command` tools between triage, sales, and support (not langgraph-swarm)."
- "Migrate an existing `create_supervisor` graph to `create_agent` + subagents."
- "Create a Deep Agent with create_deep_agent() that plans a document, spawns subagents for each section, then assembles the final output."
- "Add long-term memory via Store so my agent remembers user preferences across conversations."
- "Set up `stream_events(version='v3')` with messages + values projections for a chat UI."

## Invocation

```
Use the langgraph-deep-agents skill to [describe your graph-based agent need].
```

## Versioning and Freshness

Current lines, measured 2026-08-28 via `pypi.org/pypi/<pkg>/json`: **`langgraph 1.2.11`** (upload `2026-08-11T14:00:35Z`) and **`deepagents 0.7.10`** (upload `2026-08-28T00:45:15Z`). Local `guia_completo_agentes/guia_deepagents.html` still said `0.7.9` as of 2026-08-27 — **official PyPI wins**. `0.7.1`–`0.7.10` add no extra silent breakers beyond the 0.7.0 set. Two decisions follow from that and nothing else does:

- **Pin `0.7.10` for new work.** The retired advice "0.7 is alpha, pin 0.6.12" is now false. `0.6.12` is the end of the 0.6 line, not a maintained fallback: there is no 0.6.13. Freezing there is a legitimate short-term choice, but record it as a freeze on an end-of-line release, never as "0.7 isn't ready".
- **Treat an existing agent's upgrade as a migration, not a bump.** 12 breaking items from 0.6.12 → 0.7.0 still apply through 0.7.10, and the three highest-consequence ones are silent (no default `TodoListMiddleware`, empty authored base prompt, recursive model-visible `delete` classified as a write).

For new code prefer `stream_events(version="v3")` over parsing raw event dicts; do not confuse it with `invoke`/`stream` `version="v2"`, which controls `GraphOutput` and `StreamPart` typing. Official stream-mode name is **`checkpoints`** (plural), not `checkpoint`. Model examples use `model="anthropic:claude-sonnet-5"` via `langchain-anthropic` passthrough (no enum validation), so validate any newly-referenced model ID with a real call before production. Do not invent newer model IDs. LangGraph APIs evolve frequently: verify import paths, class names and signatures against the latest docs, and never hardcode minor versions in user code.

**Read `references/VERSIONING_FRESHNESS.md`** before pinning, upgrading, or quoting a version: it holds the current dependency pins and floors (2026-08-28), the 0.6.12 -> 0.7.0 migration checklist and pin-decision reasoning, 0.7.6–0.7.10 notes, the full source list (official docs, GitHub, PyPI, supervisor/swarm status), OpenTelemetry/OWASP relevance, runtime defaults, and the checkpoint-backend security advisory table. Dated reconciliation history is in `CHANGELOG.md`.

## Reference files

- **`references/IMPLEMENTATION_SNIPPETS.md`** — full copy-paste code for all 5 Execution Playbook steps. Read when implementing any step (state schema, checkpointing/streaming, HITL/memory, multi-agent, tools/Deep Agents/deployment).
- **`references/LANGGRAPH_CORE_PATTERNS.md`** — StateGraph fundamentals, reducers, conditional edges, persistence, v2 streaming/invoke. Read for Steps 1-2 depth.
- **`references/LANGGRAPH_HITL_MEMORY.md`** — interrupt mechanisms, `Command(resume=)`, short-term checkpoints, long-term Store. Read for Step 3 depth.
- **`references/LANGGRAPH_MULTI_AGENT.md`** — current `create_agent`/subagents and LangChain handoffs, plus legacy supervisor/swarm. Read for Step 4 depth.
- **`references/LANGGRAPH_1_2_DEEPAGENTS_0_6_NOTES.md`** — SOTA deltas for LangGraph 1.2.x + Deep Agents 0.6.x (extras, subagent typing, backends) with a 2026-08-28 current-line pointer. Read when targeting the current release line.
- **`references/VERSIONING_FRESHNESS.md`** — complete source links, version pins, freshness notes, OWASP/OTel relevance, runtime/model references. Read to verify currency before shipping.
