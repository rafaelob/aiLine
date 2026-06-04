---
name: langgraph-deep-agents
description: |-
  Build stateful, graph-based, multi-agent AI systems with LangGraph orchestration and the Deep Agents harness. Covers StateGraph with typed reducers, persistence (MemorySaver, SQLite, Postgres, DynamoDB, MongoDB, Redis), human-in-the-loop (interrupt_before/after, dynamic interrupt(), Command(resume=)), subgraph composition, streaming v2 (7 typed StreamPart modes), short-term thread memory and long-term cross-thread Store, multi-agent patterns (supervisor, swarm, hierarchical teams), and create_deep_agent planning with subagent delegation. Use when building durable graph agents with checkpointing/resume, approval workflows, or LangSmith Deployment; mentions "langgraph", "deep agents", "stategraph", "checkpointer", "multi-agent orchestration"; or needs LangGraph implementation code. Do not use for vendor-neutral topology/handoff decisions (use agent-orchestration-patterns) or the OpenAI Agents SDK stack (use openai-agents-sdk-python).
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.0.5
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
  - coding
  - project_level
  audience: developer
  output_format: markdown
  modality: text
---

# LangGraph Deep Agents

Implementation playbook for building stateful, graph-based AI agent systems using LangGraph. Covers StateGraph construction with typed reducers, persistence with multiple backends, human-in-the-loop workflows (3 interrupt mechanisms), subgraph composition, v2 type-safe streaming (7 modes), short-term and long-term memory, multi-agent patterns (supervisor, swarm, hierarchical teams), and the Deep Agents standalone library for hierarchical planning with subagent delegation.

## When to Use

- Building agents that require explicit control flow (conditional branching, loops, cycles)
- Implementing durable execution with checkpointing and resume-after-failure
- Designing human-in-the-loop approval or review workflows (interrupt_before, interrupt_after, dynamic interrupt())
- Composing complex multi-agent systems (supervisor via langgraph-supervisor-py, swarm via langgraph-swarm-py, hierarchical teams)
- Implementing the Deep Agents pattern (create_deep_agent with write_todos planning, subagent delegation, filesystem backends)
- Needing both short-term (thread checkpoints) and long-term (cross-thread Store) memory
- Streaming agent execution at token, node, custom event, checkpoint, tasks, or debug granularity (7 modes)
- Deploying graph-based agents to LangSmith Deployment (self-hosted or managed) or embedding in applications

## Inputs to Collect

1. **Agent purpose** -- what problem does the graph solve?
2. **State schema** -- what data flows through the graph (TypedDict, Pydantic model, or dataclass)?
3. **Node design** -- what processing steps are needed (LLM calls, tool execution, data transformation)?
4. **Edge logic** -- what conditions determine the flow between nodes?
5. **Persistence needs** -- MemorySaver (dev), SQLite, PostgreSQL, DynamoDB, MongoDB, Redis?
6. **Human-in-the-loop** -- which steps require human approval, review, or input?
7. **Multi-agent pattern** -- single agent, supervisor, swarm, hierarchical teams, or Deep Agents?
8. **Memory requirements** -- thread-scoped (checkpoints), cross-thread (Store), or both?
9. **Streaming needs** -- values, updates, messages, custom, checkpoint, tasks, debug, or multiple simultaneous?
10. **Deployment target** -- LangSmith Deployment (managed/self-hosted), self-hosted standalone, or embedded?
11. **Deep Agents needs** -- planning via write_todos, subagent spawning, filesystem backend, sandbox?

## Execution Playbook

Five steps, each with copy-paste code in `references/IMPLEMENTATION_SNIPPETS.md`. Work through them in order; skip steps that do not apply (e.g. single-agent graphs skip Step 4).

1. **State Schema and Graph Structure** — define the state that flows through the graph (TypedDict / Pydantic / dataclass) with the right reducers (no annotation = overwrite; `add_messages` = append + dedup by ID; custom `(old, new) -> merged`), then wire nodes as pure functions returning partial updates and edges (static or conditional via `add_conditional_edges`).
2. **Persistence, Checkpointing, and Streaming** — compile with a `checkpointer` (snapshot per super-step → resume, time-travel, HITL), inspect via `get_state` / `get_state_history`, and stream in one of 7 modes (`values`, `updates`, `messages`, `custom`, `checkpoint`, `tasks`, `debug`). Opt into `version="v2"` for typed `StreamPart` dicts, `GraphOutput` (`.value` / `.interrupts`), and Pydantic/dataclass coercion.
3. **Human-in-the-Loop and Memory** — add approval gates via 3 interrupt mechanisms (`interrupt_before`, `interrupt_after`, dynamic `interrupt()` inside nodes), resume with `Command(resume=...)` or `update_state`; use thread checkpoints for short-term memory and a cross-thread `Store` (namespaced by user_id) for long-term memory.
4. **Multi-Agent Patterns** — pick supervisor (`langgraph-supervisor-py`, central routing), swarm (`langgraph-swarm-py`, peer handoff via `Command(goto=...)`, ~40% lower latency vs supervisor), hierarchical teams (nested subgraphs), or Deep Agents (`create_deep_agent`). Define clear agent boundaries.
5. **Tool Integration, Deep Agents, and Deployment** — wire tools via `ToolNode` + `tools_condition` or `create_react_agent`; configure Deep Agents middleware (write_todos, filesystem, subagent task tool) and a filesystem backend (`StateBackend`, `FilesystemBackend`, `StoreBackend`, `ContextHubBackend`, `LocalShellBackend`, `CompositeBackend`, sandboxes); deploy to LangSmith Deployment (managed/lite/enterprise/BYOC), standalone server, or embedded, with LangSmith tracing.

**Read `references/IMPLEMENTATION_SNIPPETS.md`** for the full code for every step. **Read `references/LANGGRAPH_CORE_PATTERNS.md`** (Steps 1-2), **`references/LANGGRAPH_HITL_MEMORY.md`** (Step 3), and **`references/LANGGRAPH_MULTI_AGENT.md`** (Step 4) for conceptual depth.

## Deliverables / Definition of Done

- [ ] State schema defined with appropriate reducers (add_messages, custom)
- [ ] Graph nodes and edges implemented and tested individually
- [ ] Conditional routing logic validated with test cases
- [ ] Checkpointing configured and tested (resume after failure, time-travel)
- [ ] Human-in-the-loop interrupts working (interrupt_before/after, dynamic interrupt())
- [ ] Memory configured (short-term thread checkpoints and/or long-term Store)
- [ ] Multi-agent pattern implemented with clear agent boundaries (if applicable)
- [ ] v2 streaming verified at the required granularity
- [ ] Tools integrated and tested via ToolNode or create_react_agent
- [ ] Deep Agents configured with appropriate middleware and filesystem backend (if applicable)
- [ ] Deployed to target environment with health checks and observability
- [ ] Graph visualization generated and documented

## Common Pitfalls

1. **Mutable state in nodes** -- Nodes should return new state dicts, not mutate the input state directly.
2. **Missing reducers** -- Without proper reducers (e.g., `add_messages`), state updates overwrite instead of accumulate.
3. **Forgetting checkpointer for HITL** -- Human-in-the-loop requires checkpointing; without it, interrupts lose state. Humans may take hours/days to respond -- persistence is essential.
4. **Infinite loops** -- Conditional edges can create cycles; always include termination conditions.
5. **Over-complex graphs** -- Start simple; add nodes and edges incrementally. Visualize the graph to verify structure.
6. **Ignoring stream modes** -- Different consumers need different stream modes; choose the right one for your UI/API. Use v2 for type safety.
7. **Tight coupling between subgraphs** -- Subgraphs should communicate via well-defined state interfaces, not shared mutable data.
8. **Using v1 dict access on v2 GraphOutput** -- Old-style `result["key"]` is deprecated since v1.1 (emits `LangGraphDeprecatedSinceV11`), removed in v3.0. Use `result.value` and `result.interrupts`.
9. **In-memory storage in production** -- MemorySaver is ephemeral and local; use PostgresSaver/DynamoDB for production (fault tolerance, multi-worker).
10. **Cross-user memory leakage** -- Always namespace Store memories by user_id to prevent cross-user data leaks.
11. **Middleware + custom state_schema** -- Currently mutually exclusive in `create_agent()`; workaround by attaching state to message metadata.

## Example Prompts

- "Build a research agent graph with a planner node, parallel research nodes, and a synthesis node."
- "Add human-in-the-loop approval before the agent executes any database write operations using dynamic interrupt()."
- "Implement a supervisor pattern using langgraph-supervisor-py where a router delegates to code, research, and writing specialists."
- "Create a swarm multi-agent system using langgraph-swarm-py with handoff tools between triage, sales, and support agents."
- "Create a Deep Agent with create_deep_agent() that plans a document, spawns subagents for each section, then assembles the final output."
- "Add long-term memory via Store so my agent remembers user preferences across conversations."
- "Set up v2 streaming with multiple simultaneous modes (updates + messages) for a chat UI."

## Invocation

```
Use the langgraph-deep-agents skill to [describe your graph-based agent need].
```

## Versioning and Freshness

As-of 2026-06-04. Current lines: **`langgraph 1.2.4`** (1.0 GA: durable state, built-in persistence, first-class HITL; `langgraph.prebuilt` deprecated → `langchain.agents`) and **`deepagents 0.6.8`** (released 2026-06-03; standalone library on the LangGraph runtime — write_todos planning, task-tool subagents, filesystem backends, async subagents, multi-modal `read_file`, `dcode` CLI, ACP). LangGraph Platform renamed to **LangSmith Deployment** (Oct 2025). Checkpointers: MemorySaver (dev), SqliteSaver, PostgresSaver (prod), DynamoDBSaver, MongoDB, Redis. Known limit: `middleware` + custom `state_schema` mutually exclusive in `create_agent()`. LangGraph APIs evolve frequently — verify import paths, class names, and signatures against the latest docs; do not hardcode minor versions in user code. Comparison: LangGraph = production-grade stateful (best observability via LangSmith); CrewAI = fastest time-to-production; AutoGen = maintenance mode; Deep Agents = complex multi-step tasks with context isolation.

**Read `references/VERSIONING_FRESHNESS.md`** for the full source list (official docs, GitHub, PyPI, supervisor/swarm libs), all version deltas, OpenTelemetry/OWASP relevance, runtime defaults, and the model-family reference.

## Reference files

- **`references/IMPLEMENTATION_SNIPPETS.md`** — full copy-paste code for all 5 Execution Playbook steps. Read when implementing any step (state schema, checkpointing/streaming, HITL/memory, multi-agent, tools/Deep Agents/deployment).
- **`references/LANGGRAPH_CORE_PATTERNS.md`** — StateGraph fundamentals, reducers, conditional edges, persistence, v2 streaming/invoke. Read for Steps 1-2 depth.
- **`references/LANGGRAPH_HITL_MEMORY.md`** — interrupt mechanisms, `Command(resume=)`, short-term checkpoints, long-term Store. Read for Step 3 depth.
- **`references/LANGGRAPH_MULTI_AGENT.md`** — supervisor, swarm, hierarchical teams, Deep Agents patterns with code. Read for Step 4 depth.
- **`references/LANGGRAPH_1_2_DEEPAGENTS_0_6_NOTES.md`** — SOTA deltas for LangGraph 1.2.x + Deep Agents 0.6.x (extras, subagent typing, backends). Read when targeting the current release line.
- **`references/VERSIONING_FRESHNESS.md`** — complete source links, version pins, freshness notes, OWASP/OTel relevance, runtime/model references. Read to verify currency before shipping.
