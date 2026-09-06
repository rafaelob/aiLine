<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-04-02 -->

# LangGraph Core Patterns

> Official docs: https://langchain-ai.github.io/langgraph/
> GitHub: https://github.com/langchain-ai/langgraph
> LangGraph 1.1+: v2 streaming and invoke

## StateGraph Fundamentals

### Defining State

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Reducer: appends + dedup by ID
    current_step: str                         # No annotation: overwrite
    results: Annotated[list, lambda a, b: a + b]  # Custom reducer: concat
```

**Reducers**: no annotation = overwrite; `add_messages` = append + dedup by ID; custom `(old, new) -> merged`. State schema can be TypedDict, Pydantic model, or dataclass. When using Pydantic/dataclass with v2, outputs are automatically coerced to the correct type.

### Building the Graph

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")
graph.add_edge("tools", "agent")
graph.add_conditional_edges("agent", route_function, {"use_tools": "tools", "done": END})
```

### Nodes and Routing

```python
def agent_node(state: AgentState) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response]}  # Return partial state update

def route_function(state: AgentState) -> str:
    last = state["messages"][-1]
    return "use_tools" if hasattr(last, "tool_calls") and last.tool_calls else "done"
```

Nodes are pure functions: accept state, return partial state dict. Never mutate input state directly.

## Persistence and Checkpointing

Saves state at every super-step boundary (all nodes scheduled for that step execute, then checkpoint). A super-step is a single "tick" of the graph.

### Checkpointer Backends

| Backend | Use Case | Package |
|---------|----------|---------|
| `MemorySaver` | Dev/testing (ephemeral, local) | `langgraph.checkpoint.memory` |
| `SqliteSaver` | Light production | `langgraph-checkpoint-sqlite` |
| `PostgresSaver` | Production (recommended) | `langgraph-checkpoint-postgres` |
| `DynamoDBSaver` | AWS production (S3 for large payloads) | `langgraph-checkpoint-dynamodb` |
| MongoDB | MongoDB-backed | `langgraph-checkpoint-mongodb` |
| Redis | Redis-backed | `langgraph-checkpoint-redis` |

```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-123-conv-1"}}
result = app.invoke({"messages": [("user", "Hello")]}, config)
result = app.invoke({"messages": [("user", "Follow up")]}, config)  # State restored

# Inspect state
state = app.get_state(config)  # state.values, state.next
for snapshot in app.get_state_history(config):
    print(snapshot.values)
```

DynamoDBSaver: small checkpoints (<350 KB) in DynamoDB; large payloads to S3 with reference pointer. Agent Server/API: checkpointers and stores handled automatically.

## Streaming (7 Modes)

### v1 (Default)

```python
# Full state after each node
async for event in app.astream(input, config, stream_mode="values"):
    ...

# State deltas from each node
async for event in app.astream(input, config, stream_mode="updates"):
    node_name, delta = next(iter(event.items()))

# Token-level LLM streaming
async for event in app.astream(input, config, stream_mode="messages"):
    print(event[0].content, end="", flush=True)

# Multiple modes simultaneously
async for event in app.astream(input, config, stream_mode=["updates", "messages"]):
    ...
```

### v2 (Type-Safe, Opt-In)

Add `version="v2"` to `invoke()`/`stream()` for typed outputs. Stream yields `StreamPart` dicts (`type`, `ns`, `data`); invoke returns `GraphOutput` with `.value` and `.interrupts`.

StreamPart types (from `langgraph.types`): `ValuesStreamPart`, `UpdatesStreamPart`, `MessagesStreamPart`, `CustomStreamPart`, `CheckpointStreamPart`, `TasksStreamPart`, `DebugStreamPart`. Discriminated union on `part["type"]` for full type narrowing. Default remains v1; old-style dict access on v2 emits deprecation warning.

### Custom Events

```python
from langchain_core.callbacks import adispatch_custom_event

async def my_node(state: AgentState) -> dict:
    await adispatch_custom_event("progress", {"step": 1, "total": 3})
    return {"current_step": "done"}
```

## Subgraph Composition

```python
sub_graph = StateGraph(SubState)
sub_graph.add_node("step1", step1_fn)
sub_graph.add_edge(START, "step1")
sub_graph.add_edge("step1", END)
compiled_sub = sub_graph.compile()

parent_graph = StateGraph(ParentState)
parent_graph.add_node("sub_process", compiled_sub)  # Subgraph as a node
parent_graph.add_edge(START, "sub_process")
parent_graph.add_edge("sub_process", END)
```

State mapping between parent and subgraph is automatic when keys match, or customizable via state transformers.

## Tool Integration

### ToolNode (Prebuilt)

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return do_search(query)

tool_node = ToolNode([search])
graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", tools_condition)  # Routes to "tools" or END
```

### Prebuilt ReAct Agent

```python
from langgraph.prebuilt import create_react_agent

app = create_react_agent(model, tools=[search, calculator], checkpointer=checkpointer)
```

`create_react_agent` parameters: model, tools, checkpointer, store, interrupt_before, interrupt_after, system_message (since recent updates).

### MCP Tools

```python
# Via langchain-mcp-adapters
from langchain_mcp_adapters import MCPToolkit

toolkit = MCPToolkit(server_params=...)
tools = toolkit.get_tools()
```

## Middleware (LangGraph 1.1+)

### Model Retry Middleware
Automatically retries failed model calls with configurable exponential backoff.

### Content Moderation Middleware (OpenAI)
Detects and handles unsafe content in agent interactions. Supports checking user input, model output, and tool results.

### Summarization Middleware
Auto-summarizes conversation history when it grows too long, keeping context manageable.

### Human-in-the-Loop Middleware
Configures which tools require human approval before execution.

## Key Architecture Principles

1. **Graph-first**: Explicit control flow via nodes and edges; no implicit routing.
2. **State-driven**: All data flows through a typed state schema with reducers.
3. **Checkpoint-enabled**: Every super-step produces a checkpoint for durability.
4. **Composable**: Subgraphs as nodes; mix prebuilt and custom components.
5. **Stream-native**: 7 streaming modes for different consumers and granularities.
6. **Type-safe (v2)**: Typed StreamPart and GraphOutput for editor/type-checker support.
