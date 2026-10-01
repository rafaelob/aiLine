<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-08-28 -->

# LangGraph Multi-Agent Patterns

> Multi-agent (LangGraph): https://docs.langchain.com/oss/python/langgraph/
> Subagents (`create_agent`): https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
> Migrate from langgraph-supervisor: https://docs.langchain.com/oss/python/migrate/langgraph-supervisor
> Handoffs (swarm replacement): https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
> Deep Agents: https://github.com/langchain-ai/deepagents
> Deep Agents docs: https://docs.langchain.com/oss/python/deepagents/overview

**Legacy packages (do not start new work):** `langgraph-supervisor` is no longer actively maintained (official migrate page). `langgraph-swarm` last published `0.1.0` on 2025-12-04; there is no official `migrate/langgraph-swarm` page — formal sunset **UNVERIFIED**. Existing graphs: migrate. New graphs: patterns 1–2 below.

## Pattern 1: Supervisor via `create_agent` + tool-wrapped subagents (current)

A main agent coordinates specialists by calling them as tools. This is the official replacement for `create_supervisor`.

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

research_agent = create_agent(
    model=model,
    tools=[web_search],
    system_prompt="You are a research expert.",
)

math_agent = create_agent(
    model=model,
    tools=[add, multiply],
    system_prompt="You are a math expert.",
)


@tool("research_expert", description="Research expert for current events and web lookups.")
def call_research_agent(query: str) -> str:
    result = research_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


@tool("math_expert", description="Math expert for calculations.")
def call_math_agent(query: str) -> str:
    result = math_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


supervisor = create_agent(
    model=model,
    tools=[call_research_agent, call_math_agent],
    system_prompt="Route research questions to research_expert and math to math_expert.",
    checkpointer=InMemorySaver(),
)
```

Interrupt/resume: compile **only the outermost** graph with a checkpointer; leave subagents without `checkpointer=...` so they inherit the parent. Pass `thread_id` on the outer `invoke()` / `stream_events()`. `interrupt()` inside a subagent tool bubbles as `__interrupt__`; resume with `Command(resume=...)`.

Nested supervisors: flatten to one tool per leaf, or wrap a middle-tier `create_agent` as a tool on the top supervisor. `output_mode` (`full_history` / `last_message`) is now formatting inside the tool wrapper.

**When to use**: Clear task decomposition, centralized control, heterogeneous workers, structured workflows.

### Legacy: `langgraph-supervisor` (`create_supervisor`)

```bash
pip install langgraph-supervisor   # last PyPI 0.0.31, 2025-11-19 — unmaintained
```

```python
# LEGACY — migrate; do not copy for new work
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent  # deprecated

researcher = create_react_agent(model, tools=[search_tool], name="researcher", prompt="...")
workflow = create_supervisor([researcher, ...], model=model, prompt="Route tasks...")
app = workflow.compile(checkpointer=checkpointer)
```

## Pattern 2: Handoffs (current; swarm replacement)

State-driven tools return `Command` to update `current_step` / `active_agent`. Prefer **a single agent with middleware** that swaps prompt and tools per step. Use multiple agent subgraphs only when a node is itself a complex graph.

```python
from langchain.tools import tool
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def transfer_to_specialist(runtime) -> Command:
    """Transfer to the specialist agent."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content="Transferred to specialist",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "current_step": "specialist",
        }
    )
```

Subgraph handoffs use `Command.PARENT` with `goto=` and **must** pass the triggering `AIMessage` plus a matching `ToolMessage` (otherwise conversation history is malformed). Official tutorial: https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs-customer-support

**When to use**: Sequential constraints, conversational stage changes, customer-support flows, peer routing without a central supervisor hop.

### Legacy: `langgraph-swarm`

```bash
pip install langgraph-swarm   # last PyPI 0.1.0, 2025-12-04
```

```python
# LEGACY — migrate; do not copy for new work
from langgraph.prebuilt import create_react_agent  # deprecated
from langgraph.types import Command

def transfer_to_sales():
    """Hand off the conversation to the sales agent."""
    return Command(goto="sales_agent")
```

Formal package sunset **UNVERIFIED** (no official migrate page).

## Pattern 3: Hierarchical Teams

Nested `StateGraph` subgraphs for complex organizational structures. Use this when you need static subgraph discovery, checkpoint namespaces per tier, or shared state keys — not because you still have `create_supervisor` of supervisors.

```
[Top Supervisor]
    |---> [Research Team Lead]
    |         |---> [Web Researcher]
    |         |---> [Paper Researcher]
    |---> [Engineering Team Lead]
              |---> [Frontend Dev]
              |---> [Backend Dev]
```

Each team is a subgraph. The top graph delegates to team leads, who delegate to workers.

```python
# Research team subgraph
research_team = StateGraph(TeamState)
research_team.add_node("lead", research_lead_node)
research_team.add_node("web", web_researcher_node)
research_team.add_node("papers", paper_researcher_node)
# ... edges ...
compiled_research = research_team.compile()

# Top-level graph
top_graph = StateGraph(TopState)
top_graph.add_node("supervisor", top_supervisor_node)
top_graph.add_node("research_team", compiled_research)
top_graph.add_node("engineering_team", compiled_engineering)
# ... edges ...
```

**When to use**: Large-scale systems, domain specialization, team-based decomposition, complex organizations.

## Pattern 4: Deep Agents (Standalone Library)

A planner agent creates a structured todo list, then spawns subagents to execute each item with isolated context.

### Installation

```bash
pip install deepagents
# or
uv add deepagents
# dcode TUI (separate package, 0.1.x): pip install deepagents-code
# deploy/init CLI (separate package): pip install deepagents-cli
```

### Core API: create_deep_agent

```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware  # 0.7.0: no longer default
from langchain.chat_models import init_chat_model

# Basic usage -- returns compiled LangGraph graph
# 0.7.0 through current 0.7.10: NO planning tool, EMPTY authored base prompt
agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research and write a summary"}]})

# Custom configuration
agent = create_deep_agent(
    model=init_chat_model("anthropic:claude-sonnet-5-5"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
    middleware=[TodoListMiddleware()],
)

# Use with LangGraph features
agent = create_deep_agent()
async for part in agent.astream(input, config, stream_mode="updates", version="v2"):
    print(part)
```

### Middleware Architecture

Two middleware auto-attached by default on `deepagents 0.7.0` (still true on **0.7.10**); the planning one became opt-in.

1. **`TodoListMiddleware`** (`write_todos` tool + instructions): explicit planning with task decomposition, progress tracking, and dynamic plan revision. **Auto-attached through `0.6.x` only.** On `0.7.0+` you must pass `middleware=[TodoListMiddleware()]` (from `langchain.agents.middleware`) — and repeat it in each `SubAgent`'s middleware. If you skip it, the agent simply plans less; nothing errors.

2. **Filesystem middleware**: Adds file tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, and on `0.7.0+` a recursive `delete` when the backend supports it). Offloads large context to storage, preventing context window overflow. Auto-summarization triggers when conversations grow long.

3. **Subagent middleware**: Adds `task` tool for spawning specialized subagents with isolated context windows. Keeps main agent's context clean while going deep on specific subtasks.

Filesystem backends: in-memory (default), local disk, LangGraph store (cross-thread), Modal/Daytona/Deno sandboxes (isolated execution), composite routing, or custom.

Also includes: shell access (`execute` tool), MCP support, auto-summarization, large output handling, long-term memory (Store), and separate CLIs (`deepagents-cli`, `deepagents-code` / `dcode`). Security: "trust the LLM" model -- enforce boundaries at tool/sandbox level. For simpler tasks, use `create_agent` instead of Deep Agents.

**When to use**: Complex decomposition, document generation, codebase-wide changes, multi-step research, context isolation.

## Choosing the Right Pattern

| Pattern | Control | Complexity | Best For | Status |
|---------|---------|------------|----------|--------|
| `create_agent` + subagents | Centralized | Medium | Task routing, clear specializations | **Current** (replaces langgraph-supervisor) |
| LangChain handoffs | State-driven | Low-Medium | Conversational stage changes, peer routing | **Current** (replaces langgraph-swarm) |
| Hierarchical StateGraph | Layered | High | Large teams, domain hierarchy | Current |
| Deep Agents | Plan-driven | High | Complex decomposition, isolated execution | Current (`deepagents 0.7.10`) |
| `langgraph-supervisor` | Centralized | Medium | Existing graphs only | **Legacy** — unmaintained |
| `langgraph-swarm` | Decentralized | Low-Medium | Existing graphs only | **Legacy** — last 0.1.0 2025-12-04; sunset UNVERIFIED |

### Mental Model Test
- **Looks like a flowchart with loops** -> LangGraph (StateGraph)
- **Looks like a conversation thread / stage machine** -> Handoffs (`Command` + middleware)
- **Looks like a job description board** -> `create_agent` + tool-wrapped subagents
- **Looks like a project plan with subtasks** -> Deep Agents (planning)

### Key Insight
The framework matters less than the infrastructure around it -- state persistence, retry handling, deployment, and monitoring determine reliability more than the agent pattern choice.

## Comparison (March 2026)

**LangGraph**: production-grade stateful + LangSmith observability + time-travel + HITL (steeper learning curve). **CrewAI**: fastest time-to-production, role-based (less mature monitoring). **AutoGen**: conversational patterns (maintenance mode). **Google ADK**: Google ecosystem, A2A, multi-language (tighter coupling).
