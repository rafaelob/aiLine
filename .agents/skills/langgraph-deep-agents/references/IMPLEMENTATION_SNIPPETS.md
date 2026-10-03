# LangGraph Deep Agents — Implementation Snippets

Copy-paste implementation code for each Execution Playbook step. Verify import
paths, class names, and method signatures against the latest docs (LangGraph
APIs evolve frequently). For conceptual depth, also read the companion
references: `LANGGRAPH_CORE_PATTERNS.md`, `LANGGRAPH_HITL_MEMORY.md`,
`LANGGRAPH_MULTI_AGENT.md`, `LANGGRAPH_1_2_DEEPAGENTS_0_6_NOTES.md`.

## Step 1: State Schema and Graph Structure

Define the state that flows through the graph and the graph's node/edge topology.

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Reducer: append + dedup by ID
    next_step: str                           # No annotation: overwrite
    results: Annotated[list, lambda a, b: a + b]  # Custom reducer: concat
```

**Reducers**: no annotation = overwrite; `add_messages` = append + dedup by ID; custom `(old, new) -> merged`.

Design nodes as pure functions (or async functions) that accept state and return partial state updates. Define edges (static or conditional) to control flow.

```python
graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("analyze", analyze_node)
graph.add_node("respond", respond_node)

graph.add_edge(START, "research")
graph.add_conditional_edges("research", route_after_research, {"analyze": "analyze", "done": END})
graph.add_edge("analyze", "respond")
graph.add_edge("respond", END)
```

## Step 2: Persistence, Checkpointing, and Streaming

Add durable execution and real-time output.

- **Checkpointing**: Saves state as snapshots at every super-step (all nodes scheduled for a step execute, producing a checkpoint). Enables resume after failures, time-travel debugging, and human-in-the-loop interrupts.

```python
from langgraph.checkpoint.memory import InMemorySaver
# MemorySaver is the same in-RAM class; official persistence examples use InMemorySaver.
# Production backends:
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.postgres import PostgresSaver
# Also: DynamoDBSaver (AWS), MongoDB, Redis checkpointers
# Security (re-checked 2026-08-28): langgraph-checkpoint, langgraph-checkpoint-sqlite,
# langgraph-checkpoint-postgres, and the npm @langchain/langgraph-checkpoint-redis package
# carry CVEs below stated floors -- see references/VERSIONING_FRESHNESS.md before pinning.

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-123-conv-1"}}
result = app.invoke({"messages": [("user", "Hello")]}, config)
```

- **State inspection and time-travel**:
```python
state = app.get_state(config)  # state.values, state.next
for snapshot in app.get_state_history(config):
    print(snapshot.values)
```

- **Streaming** (7 modes):
  - `stream_mode="values"`: Full state after each node
  - `stream_mode="updates"`: State delta from each node
  - `stream_mode="messages"`: Token-level streaming from LLM nodes
  - `stream_mode="custom"`: Custom events emitted from nodes via `adispatch_custom_event`
  - `stream_mode="checkpoints"`: Checkpoint snapshots (plural — official stream-mode name)
  - `stream_mode="tasks"`: Task-level events
  - `stream_mode="debug"`: Debug-level events for development

```python
# v1 (default): yields bare data
async for event in app.astream(input, config, stream_mode="updates"):
    print(event)

# v2 (opt-in): yields typed StreamPart dicts
async for part in app.astream(input, config, stream_mode="updates", version="v2"):
    print(part["type"], part["data"])  # Typed: UpdatesStreamPart

# v2 invoke: returns GraphOutput with .value and .interrupts
result = app.invoke(input, config, version="v2")
print(result.value, result.interrupts)

# Multiple modes simultaneously
async for event in app.astream(input, config, stream_mode=["updates", "messages"]):
    ...

# New apps: event streaming v3 (typed projections). Do not confuse with invoke/stream version="v2".
stream = app.stream_events(input, config, version="v3")
for message in stream.messages:
    print(message.text)
final_state = stream.output
```

**v2 StreamPart types** (importable from `langgraph.types`): `ValuesStreamPart`, `UpdatesStreamPart`, `MessagesStreamPart`, `CustomStreamPart`, `CheckpointStreamPart`, `TasksStreamPart`, `DebugStreamPart`. Union type `StreamPart` is a discriminated union on `part["type"]`.

**Pydantic / dataclass coercion under v2**: with `version="v2"`, `invoke()` and values-mode stream output are automatically coerced to your declared Pydantic model or dataclass type — prefer a typed state schema so downstream consumers never hand-parse dicts.

**Time-travel fixes (v2)**: replays no longer reuse stale RESUME values, and subgraphs correctly restore the checkpoint for the parent's historical state. Re-run audited HITL traces under v2 if you previously observed drift.

## Step 3: Human-in-the-Loop and Memory

Implement approval workflows and persistent memory.

- **3 interrupt mechanisms**:
  1. `interrupt_before=["node_name"]`: Pause **before** a node runs. Human reviews state and approves/rejects/modifies.
  2. `interrupt_after=["node_name"]`: Pause **after** a node runs. Useful for reviewing results.
  3. `interrupt()` function: Dynamic, conditional pausing inside nodes based on runtime conditions.

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["sensitive_action"],
)

# Resume after human approval:
from langgraph.types import Command
app.invoke(Command(resume={"approved": True}), config)

# Or modify state before continuing:
app.update_state(config, {"planned_action": modified_action})
app.invoke(None, config)
```

Dynamic interrupt inside a node:
```python
from langgraph.types import interrupt

def sensitive_node(state):
    if state["risk_level"] == "high":
        human_response = interrupt(
            {"question": "This action is high-risk. Proceed?", "details": state["action"]}
        )
        if not human_response.get("approved"):
            return {"messages": [AIMessage(content="Action cancelled.")]}
    return execute_action(state)
```

- **Short-term memory**: Thread-scoped state via checkpoints. All state within a thread persists across invocations. Different threads have independent state.
- **Long-term memory**: Cross-thread `Store` interface for user preferences, learned facts, shared knowledge.

```python
from langgraph.store.memory import InMemoryStore
# Production: database-backed stores

store = InMemoryStore()
app = graph.compile(checkpointer=checkpointer, store=store)

# In nodes:
def my_node(state, config, *, store):
    user_id = config["configurable"]["user_id"]
    memories = store.search(("users", user_id, "preferences"))
    store.put(("users", user_id, "preferences"), key="theme", value={"preference": "dark_mode"})
    return {"messages": [...]}
```

## Step 4: Multi-Agent Patterns

Choose and implement the right multi-agent architecture.

- **Supervisor (current)**: `from langchain.agents import create_agent` plus specialists wrapped as `@tool`. Official replacement for unmaintained `langgraph-supervisor` (`create_supervisor`). Compile only the outermost graph with a checkpointer. See `references/LANGGRAPH_MULTI_AGENT.md`.

- **Handoffs (current)**: LangChain handoffs — tools return `Command` updating `current_step` / `active_agent`. Prefer a single agent + middleware. Replaces `langgraph-swarm` (last PyPI 0.1.0, 2025-12-04; sunset UNVERIFIED).

- **Hierarchical Teams**: Nested `StateGraph` subgraphs. Top graph delegates to team-lead subgraphs, who delegate to workers.

- **Deep Agents** (standalone library `deepagents`): Hierarchical planning pattern with `create_deep_agent()`. Middleware architecture: write_todos (planning), filesystem tools (context offloading), task tool (subagent spawning). Pluggable filesystem backends. Built on LangGraph runtime.

For all patterns, define clear agent boundaries and use the graph structure to enforce the coordination protocol.

## Step 5: Tool Integration, Deep Agents, and Deployment

Wire tools, configure Deep Agents, and deploy.

- **ToolNode**: Built-in node that executes tool calls from LLM responses.
- **tools_condition**: Routes to "tools" node or END based on tool_calls presence.
- **`create_agent`**: Prebuilt ReAct-style agent (`from langchain.agents import create_agent`, `system_prompt=`). Do **not** use deprecated `create_react_agent` from `langgraph.prebuilt`.
- **MCP tools**: Via `langchain-mcp-adapters` for external tool server access.

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.agents import create_agent

tools = [search_tool, calculator_tool]
tool_node = ToolNode(tools)
graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", tools_condition)

# Prebuilt agent (LangGraph v1: create_react_agent is deprecated)
app = create_agent(model, tools=tools, system_prompt="You are a helpful assistant.", checkpointer=checkpointer)
```

- **Deep Agents** (`pip install deepagents`, MIT license; Python `>=3.11,<4.0` — 3.11 through 3.14). The current pin lives in `references/VERSIONING_FRESHNESS.md` § "Current pins" — read it there rather than trusting a version restated here, and verify at https://pypi.org/project/deepagents/. `0.7.0` is a **breaking** release: `0.6.12` (2026-06-25) is the end of the 0.6 line and gets no further fixes. Walk the 12-item migration checklist in `references/VERSIONING_FRESHNESS.md` § "Freshness (as-of 2026-07-30)" before upgrading an existing agent — several breaks are silent (behaviour and permission changes, not `ImportError`):

```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware  # 0.7.0: no longer default
from langchain.chat_models import init_chat_model

# Basic usage -- returns compiled LangGraph graph.
# 0.7.0 note: this agent has NO planning tool and an EMPTY authored base prompt.
agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research and summarize LangGraph"}]})

# Custom configuration.
# On 0.7.0, pass TodoListMiddleware explicitly if you want write_todos planning
# (and repeat it in each SubAgent's middleware to restore it there too).
agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-5-5"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
    middleware=[TodoListMiddleware()],
)
```

**Model-selection caveat:** `langchain-anthropic` accepts any model string via passthrough (no enum validation) — this is how `"anthropic:claude-sonnet-5"` (previous generation) resolves. As of `langchain-anthropic 1.7.0` (requires `anthropic>=0.120.0`, measured 2026-08-28), the connector is current with the Anthropic SDK -- this is also what brings **Claude Opus 5** to LangChain (`model="anthropic:claude-opus-5"` via the same passthrough). `claude-sonnet-5-5` (released 2026-09-28) is a real, non-invented ID — confirmed at https://www.anthropic.com/claude-sonnet-5-5 — but whether this specific string resolves through `langchain-anthropic`'s passthrough is **UNVERIFIED** by this pass; run a real validation call before production for any newly-referenced model ID, since passthrough means no enum validation catches a typo or an unsupported ID. Do not invent newer model IDs.

Deep Agents middleware:
1. **`TodoListMiddleware`** (`write_todos` tool + planning instructions) — **auto-attached only through `0.6.x`. On `0.7.0` it is opt-in**: pass `middleware=[TodoListMiddleware()]` from `langchain.agents.middleware`, on the main agent and on every `SubAgent`. Omitting it silently removes the tool, the `todos` state channel, and the planning prompt.
2. **Filesystem middleware** (auto-attached): adds `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` for context offloading — plus, **on `0.7.0`, a recursive `delete`** whenever the backend supports it. Restrict the set with the keyword-only allowlist `FilesystemMiddleware(tools=[...])` (typed by the exported `FsToolName` literal; the list must include `"read_file"`).
3. **Subagent middleware** (auto-attached): adds `task` tool for spawning subagents with isolated context windows. On `0.7.0` its `system_prompt` defaults to `None`, so it injects no tool-usage prose.

Filesystem backends (named classes): `StateBackend` (default; ephemeral per thread, stored in LangGraph state), `FilesystemBackend` (local disk), `StoreBackend` (LangGraph Store, cross-thread persistence), `ContextHubBackend` (LangChain Context Hub), `LocalShellBackend` (shell-backed filesystem), `CompositeBackend` (route paths across multiple backends). Sandboxes (Modal, Daytona, Runloop) and S3/PostgreSQL are available via `deepagents-backends` or custom implementations.

Additional Deep Agents features: auto-summarization (triggers when conversations grow long), shell access (`execute` with sandboxing), MCP support via `langchain-mcp-adapters`, **async subagents** (April 2026 — subagents run as non-blocking background tasks so users keep interacting with the main agent; requires LangSmith Deployment), **multi-modal `read_file`** (PDFs, audio, and video in addition to images), updated backend protocol / file format in State and Store backends to support binary files (backwards-compatible). CLIs are **separate packages**, not the library: `dcode` TUI is `pip install deepagents-code` (own `0.1.x` line; 0.7.9 removed the deprecated in-tree `libs/cli`); deploy/init is `pip install deepagents-cli`; ACP is `pip install deepagents-acp`.

- **Deployment options**:
  - **LangSmith Deployment** (formerly LangGraph Platform): Managed deployment with built-in persistence, streaming, monitoring. Self-hosted lite (free, 100k nodes/month), self-hosted enterprise (fully in VPC), hybrid BYOC (SaaS control plane + self-hosted data plane).
  - **Standalone Server**: Lightweight option with Agent Servers + PostgreSQL + Redis. Kubernetes (production) or Docker (dev).
  - **Embedded**: Compile the graph and invoke directly within your application.
  - **Observability**: LangSmith for tracing (`LANGSMITH_TRACING=true`), step-by-step traces with token counts per node, replay failed runs with modified inputs.
