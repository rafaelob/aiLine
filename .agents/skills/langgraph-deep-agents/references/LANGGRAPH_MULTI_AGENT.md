<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-04-02 -->

# LangGraph Multi-Agent Patterns

> Multi-agent docs: https://langchain-ai.github.io/langgraph/concepts/multi_agent/
> Supervisor library: https://github.com/langchain-ai/langgraph-supervisor-py
> Swarm library: https://github.com/langchain-ai/langgraph-swarm-py
> Deep Agents: https://github.com/langchain-ai/deepagents
> Deep Agents docs: https://docs.langchain.com/oss/python/deepagents/overview

## Pattern 1: Supervisor (via langgraph-supervisor-py)

A central supervisor agent routes tasks to specialized workers via tool-based handoff mechanism.

```bash
pip install langgraph-supervisor
```

```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

# Create specialized worker agents
researcher = create_react_agent(model, tools=[search_tool], name="researcher")
coder = create_react_agent(model, tools=[code_tool], name="coder")
writer = create_react_agent(model, tools=[write_tool], name="writer")

# Create supervisor that orchestrates workers
supervisor = create_supervisor(
    model,
    agents=[researcher, coder, writer],
    prompt="Route tasks to the appropriate specialist.",
)
app = supervisor.compile(checkpointer=checkpointer)
```

Key features: tool-based handoff, flexible message history, inherits streaming/memory/HITL, `create_forward_message_tool` for direct output forwarding.

### Multi-Level Hierarchies

Nest supervisors: each team is a `create_supervisor(model, agents=[...])`, then pass `team.compile()` as agents to a top-level supervisor.

**When to use**: Clear task decomposition, centralized control, heterogeneous workers, structured workflows.

## Pattern 2: Swarm (via langgraph-swarm-py)

Agents hand off to each other dynamically. No central controller. System remembers last active agent.

```bash
pip install langgraph-swarm
```

```python
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

def transfer_to_sales():
    """Hand off the conversation to the sales agent."""
    return Command(goto="sales_agent")

def transfer_to_support():
    """Hand off the conversation to the support agent."""
    return Command(goto="support_agent")

# Each agent has handoff tools
triage_agent = create_react_agent(
    model, tools=[transfer_to_sales, transfer_to_support], name="triage"
)
sales_agent = create_react_agent(
    model, tools=[transfer_to_support, *sales_tools], name="sales_agent"
)
support_agent = create_react_agent(
    model, tools=[transfer_to_sales, *support_tools], name="support_agent"
)
```

Decentralized (each agent decides next), persistent routing (remembers last active agent), ~40% faster than supervisor (no intermediary hop), fewer LLM calls.

**When to use**: Peer-to-peer collaboration, dynamic routing, conversational handoffs, customer service flows.

## Pattern 3: Hierarchical Teams

Nested supervisors for complex organizational structures.

```
[Top Supervisor]
    |---> [Research Team Lead]
    |         |---> [Web Researcher]
    |         |---> [Paper Researcher]
    |---> [Engineering Team Lead]
              |---> [Frontend Dev]
              |---> [Backend Dev]
```

Each team is a subgraph with its own supervisor. The top supervisor delegates to team leads, who delegate to workers.

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
```

### Core API: create_deep_agent

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

# Basic usage -- returns compiled LangGraph graph
agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research and write a summary"}]})

# Custom configuration
agent = create_deep_agent(
    model=init_chat_model("openai:gpt-5.5"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)

# Use with LangGraph features
agent = create_deep_agent()
# Stream, checkpoint, HITL, Studio -- all LangGraph features work
async for part in agent.astream(input, config, stream_mode="updates"):
    print(part)
```

### Middleware Architecture

Three middleware auto-attached by default:

1. **write_todos middleware**: Adds `write_todos` tool + instructions. Enables explicit planning with task decomposition, progress tracking, and dynamic plan revision.

2. **Filesystem middleware**: Adds file tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`). Offloads large context to storage, preventing context window overflow. Auto-summarization triggers when conversations grow long.

3. **Subagent middleware**: Adds `task` tool for spawning specialized subagents with isolated context windows. Keeps main agent's context clean while going deep on specific subtasks.

Filesystem backends: in-memory (default), local disk, LangGraph store (cross-thread), Modal/Daytona/Deno sandboxes (isolated execution), composite routing, or custom.

Also includes: shell access (`execute` tool), MCP support, auto-summarization, large output handling, long-term memory (Store), and CLI with web search/sandboxes/HITL. Security: "trust the LLM" model -- enforce boundaries at tool/sandbox level. For simpler tasks, use `create_react_agent` instead.

**When to use**: Complex decomposition, document generation, codebase-wide changes, multi-step research, context isolation.

## Choosing the Right Pattern

| Pattern | Control | Complexity | Best For | Performance |
|---------|---------|------------|----------|-------------|
| Supervisor | Centralized | Medium | Task routing, clear specializations | Extra hop per delegation |
| Swarm | Decentralized | Low-Medium | Conversational handoffs, peer agents | ~40% faster than supervisor |
| Hierarchical | Layered | High | Large teams, domain hierarchy | Depends on depth |
| Deep Agents | Plan-driven | High | Complex decomposition, isolated execution | Context-efficient |

### Mental Model Test
- **Looks like a flowchart with loops** -> LangGraph (StateGraph)
- **Looks like a conversation thread** -> Swarm (handoffs)
- **Looks like a job description board** -> Supervisor (routing)
- **Looks like a project plan with subtasks** -> Deep Agents (planning)

### Key Insight
The framework matters less than the infrastructure around it -- state persistence, retry handling, deployment, and monitoring determine reliability more than the agent pattern choice.

## Comparison (March 2026)

**LangGraph**: production-grade stateful + LangSmith observability + time-travel + HITL (steeper learning curve). **CrewAI**: fastest time-to-production, role-based (less mature monitoring). **AutoGen**: conversational patterns (maintenance mode). **Google ADK**: Google ecosystem, A2A, multi-language (tighter coupling).
