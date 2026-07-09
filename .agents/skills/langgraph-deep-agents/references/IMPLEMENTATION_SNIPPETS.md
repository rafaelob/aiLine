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
from langgraph.checkpoint.memory import MemorySaver
# Production backends:
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.postgres import PostgresSaver
# Also: DynamoDBSaver (AWS), MongoDB, Redis checkpointers

checkpointer = MemorySaver()
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
  - `stream_mode="checkpoint"`: Checkpoint snapshots
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

- **Supervisor** (via `langgraph-supervisor-py`): Central supervisor routes tasks to specialized workers via tool-based handoff mechanism. Supports multi-level hierarchies (supervisor managing supervisors), message forwarding (`create_forward_message_tool`), flexible message history management.

- **Swarm** (via `langgraph-swarm-py`): Agents hand off control to each other dynamically using `Command(goto="agent_name")`. System remembers last active agent. Decentralized, no central controller. ~40% reduction in end-to-end response time vs supervisor (eliminates supervisor intermediary hop).

- **Hierarchical Teams**: Nested supervisors via subgraph composition. Top supervisor delegates to team leads (subgraphs), who delegate to workers.

- **Deep Agents** (standalone library `deepagents`): Hierarchical planning pattern with `create_deep_agent()`. Middleware architecture: write_todos (planning), filesystem tools (context offloading), task tool (subagent spawning). Pluggable filesystem backends. Built on LangGraph runtime.

For all patterns, define clear agent boundaries and use the graph structure to enforce the coordination protocol.

## Step 5: Tool Integration, Deep Agents, and Deployment

Wire tools, configure Deep Agents, and deploy.

- **ToolNode**: Built-in node that executes tool calls from LLM responses.
- **tools_condition**: Routes to "tools" node or END based on tool_calls presence.
- **create_react_agent**: Prebuilt ReAct agent with tool loop.
- **MCP tools**: Via `langchain-mcp-adapters` for external tool server access.

```python
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent

tools = [search_tool, calculator_tool]
tool_node = ToolNode(tools)
graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", tools_condition)

# Prebuilt ReAct agent
app = create_react_agent(model, tools=tools, checkpointer=checkpointer)
```

- **Deep Agents** (`pip install deepagents`, MIT license, current stable line `deepagents == 0.6.12` released 2026-06-25; Python `>=3.11,<4.0` — 3.11 through 3.14; verify at https://pypi.org/project/deepagents/). A preview-only `0.7.0a3` alpha (2026-07-01) exists with middleware override by name, sandbox round-trip optimization, and Bedrock prompt-caching (`deepagents[aws]`) — do not use the alpha line in production:

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

# Basic usage -- returns compiled LangGraph graph
agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research and summarize LangGraph"}]})

# Custom configuration
agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-5"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)
```

**Model-selection caveat:** `langchain-anthropic` accepts any model string via passthrough (no enum validation), so `"anthropic:claude-sonnet-5"` works as shown above -- but the last published connector (`1.4.8`, 2026-06-26) predates Sonnet 5's GA (2026-06-30), and no changelog confirms tested support for Sonnet-5-specific beta features (new tokenizer, beta headers). Run a real validation call before production and track `langchain-anthropic` releases newer than `1.4.8`.

Deep Agents middleware (auto-attached):
1. **write_todos middleware**: Adds `write_todos` tool + instructions for explicit planning and todo tracking.
2. **Filesystem middleware**: Adds `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` for context offloading.
3. **Subagent middleware**: Adds `task` tool for spawning subagents with isolated context windows.

Filesystem backends (named classes): `StateBackend` (default; ephemeral per thread, stored in LangGraph state), `FilesystemBackend` (local disk), `StoreBackend` (LangGraph Store, cross-thread persistence), `ContextHubBackend` (LangChain Context Hub), `LocalShellBackend` (shell-backed filesystem), `CompositeBackend` (route paths across multiple backends). Sandboxes (Modal, Daytona, Runloop) and S3/PostgreSQL are available via `deepagents-backends` or custom implementations.

Additional Deep Agents features: auto-summarization (triggers when conversations grow long), shell access (`execute` with sandboxing), MCP support via `langchain-mcp-adapters`, CLI with web search/persistent memory/HITL, **async subagents** (April 2026 — subagents run as non-blocking background tasks so users keep interacting with the main agent; requires LangSmith Deployment), **multi-modal `read_file`** (PDFs, audio, and video in addition to images), updated backend protocol / file format in State and Store backends to support binary files (backwards-compatible), the `dcode` CLI (`pip install deepagents-code`) for terminal-driven coding workflows, and an Agent Communication Protocol (ACP) integration via `pip install deepagents-acp` for IDE wiring.

- **Deployment options**:
  - **LangSmith Deployment** (formerly LangGraph Platform): Managed deployment with built-in persistence, streaming, monitoring. Self-hosted lite (free, 100k nodes/month), self-hosted enterprise (fully in VPC), hybrid BYOC (SaaS control plane + self-hosted data plane).
  - **Standalone Server**: Lightweight option with Agent Servers + PostgreSQL + Redis. Kubernetes (production) or Docker (dev).
  - **Embedded**: Compile the graph and invoke directly within your application.
  - **Observability**: LangSmith for tracing (`LANGSMITH_TRACING=true`), step-by-step traces with token counts per node, replay failed runs with modified inputs.
