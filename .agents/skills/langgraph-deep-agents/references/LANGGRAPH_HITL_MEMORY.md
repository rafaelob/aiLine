<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-04-02 -->

# LangGraph Human-in-the-Loop and Memory

> HITL docs: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
> Memory docs: https://langchain-ai.github.io/langgraph/concepts/memory/
> Persistence docs: https://langchain-ai.github.io/langgraph/concepts/persistence/

## Human-in-the-Loop (HITL)

LangGraph's HITL architecture rests on three pillars: **checkpointing** (state persistence), **interrupts** (execution pausing), and **commands** (human responses). Humans may respond immediately or take hours/days -- persistence ensures the workflow survives the wait.

### Mechanism 1: Interrupt Before

Pause execution **before** a node runs. Human reviews state and approves, rejects, or modifies.

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_action"],  # Pause before this node
)

# Run until interrupt
result = app.invoke(input, config)
# result.next == ("execute_action",) -- paused here

# Inspect what the agent wants to do
state = app.get_state(config)
pending_action = state.values["planned_action"]

# Option 1: Approve and continue
from langgraph.types import Command
app.invoke(Command(resume={"approved": True}), config)

# Option 2: Reject and provide feedback
app.invoke(Command(resume={"approved": False, "feedback": "Too risky"}), config)

# Option 3: Modify state before continuing
app.update_state(config, {"planned_action": modified_action})
app.invoke(None, config)  # Continue with modified state
```

### Mechanism 2: Interrupt After

Pause execution **after** a node runs. Useful for reviewing results before proceeding.

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_after=["generate_draft"],  # Pause after this node
)
```

### Mechanism 3: Dynamic Interrupts

Use the `interrupt()` function inside a node for conditional pausing based on runtime conditions:

```python
from langgraph.types import interrupt

def sensitive_node(state):
    if state["risk_level"] == "high":
        # Pause and ask the human
        human_response = interrupt(
            {"question": "This action is high-risk. Proceed?", "details": state["action"]}
        )
        if not human_response.get("approved"):
            return {"messages": [AIMessage(content="Action cancelled by human.")]}
    # Proceed with action
    return execute_action(state)
```

### HITL Patterns

1. **Approval gate**: Interrupt before destructive actions; require explicit approval.
2. **Review and edit**: Interrupt after generation; human edits output before it continues.
3. **Input collection**: Interrupt to request additional information from the human.
4. **Escalation**: Interrupt when the agent detects uncertainty or risk beyond its threshold.
5. **Learning from feedback**: Combine interrupts with Store to save human corrections as long-term memories.

### HITL with v2

```python
# v2 invoke returns GraphOutput with .interrupts
result = app.invoke(input, config, version="v2")
if result.interrupts:
    # Handle interrupts
    for interrupt_data in result.interrupts:
        print(interrupt_data)
    # Resume
    app.invoke(Command(resume={"approved": True}), config, version="v2")
```

## Memory

### Short-Term Memory (Thread State)

Thread state is automatically persisted via checkpointing. All state within a thread persists across invocations. Different threads have independent state.

```python
config = {"configurable": {"thread_id": "user-123"}}

# First turn
app.invoke({"messages": [("user", "My name is Alice")]}, config)

# Second turn (agent remembers the name from thread state)
app.invoke({"messages": [("user", "What is my name?")]}, config)
```

### Long-Term Memory (Cross-Thread Store)

For memory that persists across threads (user preferences, learned facts, organizational knowledge), use the `Store` interface. Memory is stored as JSON documents organized using namespaces (like folders) and keys (like filenames).

```python
from langgraph.store.memory import InMemoryStore
# For production: database-backed stores (verify current API in docs)

store = InMemoryStore()

app = graph.compile(
    checkpointer=checkpointer,
    store=store,
)
```

### Accessing the Store in Nodes

```python
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

def my_node(state: AgentState, config: RunnableConfig, *, store: BaseStore):
    user_id = config["configurable"]["user_id"]

    # Read memories (namespace-based search)
    memories = store.search(("users", user_id, "preferences"))

    # Write a memory
    store.put(
        ("users", user_id, "preferences"),
        key="theme",
        value={"preference": "dark_mode", "confidence": 0.9},
    )

    return {"messages": [...]}
```

### Memory Patterns

1. **User profile**: Store user preferences, past interactions, and learned facts.
2. **Semantic memory**: Store embeddings of past interactions for similarity-based retrieval.
3. **Episodic memory**: Store summaries of past conversations as retrievable episodes.
4. **Shared knowledge**: Store organizational or domain knowledge accessible across all threads.

### Memory Best Practices

Namespace by user ID (prevent cross-user leakage). Version memories for freshness. Prune with TTL or relevance. Inject only relevant memories, not all. Read at turn start, write at turn end. Agent Server/API manages stores automatically.

## Combining HITL and Memory

A common pattern: the agent learns from human feedback and stores corrections as long-term memories.

```python
def review_node(state, *, store):
    # Agent generates a response
    response = generate_response(state)

    # Interrupt for human review
    feedback = interrupt({"draft": response, "question": "Is this correct?"})

    if feedback.get("correction"):
        # Store the correction as a long-term memory
        store.put(
            ("corrections", state["topic"]),
            key=str(uuid4()),
            value={"original": response, "correction": feedback["correction"]},
        )
        return {"messages": [AIMessage(content=feedback["correction"])]}

    return {"messages": [AIMessage(content=response)]}
```

## Persistence Comparison

| Feature | Checkpoints (Short-Term) | Store (Long-Term) |
|---------|------------------------|-------------------|
| Scope | Single thread | Cross-thread |
| Lifetime | Thread lifetime | Indefinite |
| Structure | Full state snapshots | Key-value documents |
| Access | Automatic via thread_id | Explicit via namespace/key |
| Use case | Conversation history, HITL | User preferences, facts |
| Auto-managed | Yes (Agent Server) | Yes (LangGraph API) |

## Checkpointer Backends

MemorySaver (dev only, ephemeral). SqliteSaver (light prod). **PostgresSaver** (recommended, durable, multi-worker). DynamoDBSaver (AWS, infinite scale). MongoDB, Redis also supported. In-memory not acceptable for production.
