# Guide to Memory for Agents and Context Engineering (October 2025)

This document expands and deepens the **exhaustive guide** presented earlier.  It gathers virtually all public evidence available up to **October 2025** about **memory for agents** and **context engineering**, including open‑source frameworks, academic papers, technical blogs, corporate articles (OpenAI, Anthropic, Google, Microsoft, etc.) and community discussions.  The goal is to provide a holistic view—from theoretical foundations to concrete implementations—for anyone who needs to design AI agents capable of **remembering, reasoning and collaborating** on complex tasks.

> **Note on structure**:  This guide is organised into sections with detailed subtopics.  Each section presents a conceptual overview followed by practical examples, relevant frameworks and discussions of advantages, disadvantages and applications.  For every important assertion you will find references at the end of this document in the **FULL LINKS** section.

## Table of Contents

1. [Context and Motivation](#context-and-motivation)
2. [Taxonomies of Memory for Agents](#taxonomies-of-memory-for-agents)
3. [Memory Layers and Storage Schemes](#memory-layers-and-storage-schemes)
4. [Frameworks, Libraries and Memory Platforms](#frameworks-libraries-and-memory-platforms)
   1. [Commercial and Cloud Platforms](#commercial-and-cloud-platforms)
   2. [Open‑Source Frameworks and Libraries](#open-source-frameworks-and-libraries)
5. [Context Engineering: Concepts, Techniques and Patterns](#context-engineering-concepts-techniques-and-patterns)
   1. [Components of Context](#components-of-context)
   2. [Classification and Variants of RAG](#classification-and-variants-of-rag)
   3. [Compression, Compaction and Structured Notes](#compression-compaction-and-structured-notes)
   4. [Isolation of Contexts and Multi‑Agents](#isolation-of-contexts-and-multi-agents)
   5. [Auditing, Privacy Controls and Governance](#auditing-privacy-controls-and-governance)
6. [Advanced Patterns and Cutting‑Edge Research](#advanced-patterns-and-cutting-edge-research)
7. [Practical Examples and Python Implementations](#practical-examples-and-python-implementations)
8. [Trends, Challenges and Future Possibilities](#trends-challenges-and-future-possibilities)
9. [References and Further Reading](#references-and-further-reading)
10. [FULL LINKS](#full-links)

---

## Context and Motivation

**Context window and memory limitations**:  Large language models (LLMs) have finite context windows.  Even with multi‑million‑token contexts, attention is a limited resource.  For agents that interact for hours, months or years, storing the entire history is impractical and can lead to hallucinations and incoherence.  The best systems combine **structured external memory** and **dynamic context** to keep conversations cohesive, personalised and efficient.

**Importance of memory for user experience**:  Studies show that most support customers must repeat information and that repetition is a major source of frustration.  Persistent memories improve the user experience, reduce resolution time and enable deep personalisation.  Companies like OpenAI, Anthropic and Mindset AI incorporated memory into their products (ChatGPT, Claude, Mindset Agent Memory) specifically to close this “memory gap.”

**From prompt engineering to context engineering**:  While prompt engineering involves static instructions, context engineering is a dynamic problem of **knowledge orchestration**.  It involves selecting, transforming and formatting relevant information—ranging from system instructions, recent messages and tool outputs to persistent memories and business facts—to fit within the context window and maximise answer quality.  Companies and researchers realised that optimising this assembly is as important as training large models.

---

## Taxonomies of Memory for Agents

Memories can be classified in several ways.  This section synthesises taxonomies proposed by academic research and specialised blogs.

* **Type of information (object)**:  memories may be **personal** (specific to the user) or **non‑personal** (general knowledge, policies, procedures).  This distinction matters for governance and personalisation.  Personal memories require privacy and expiry controls.
* **Storage form**:  memories may be **parametric** (inside the model’s weights) or **non‑parametric** (external, usually as text, embeddings or graphs).  Parametric memories correspond to pre‑training; external memories are dynamic and controllable.
* **Temporal horizon**:  inspired by psychology.  **Short‑term memory** (working context), **episodic memory** (conversation and event history) and **semantic memory** (facts and knowledge).  Some approaches add **procedural memory** (patterns of actions or routines) and **meta‑memory** (memory about how to manage memory).
* **Access class**:  memories can be **transient** (only during the task) or **persistent** (with state shared across sessions).  Persistence implies strategies for updating, forgetting and reconciling versions.
* **Organisation**:  memories can be organised as **text lists**, **embedding vectors**, **knowledge graphs**, **notes and zettelkasten**, **hierarchical layers** or **ontologies**.  Each structure has implications for querying and performance.

---

## Memory Layers and Storage Schemes

Agent memories are often organised in layers or levels.  The following summarises recurring patterns:

### Working Memory (Short‑Term Memory)

Working memory serves as **immediate context**—what is “on the agent’s mind” during an interaction.  It contains current goals, recent messages, tool results, error states and important facts.  It must be small to fit into the model’s context and is usually managed with sliding windows, incremental summaries or compaction/archiving techniques.  Models like **MemGPT**, **Mem0** and **MemoryOS** implement working memory with compression and annotation processes.

### Long‑Term Memory (Episodic and Semantic Memory)

Long‑term memory stores everything that will not fit into context.  It holds past conversations, learned patterns, reference documents, intermediate results and summaries.  Retrieval‑augmented generation (RAG) tools and retrieval systems need to identify which parts to return to context when needed.  Frameworks like **A‑MEM**, **Memory Bank**, **MemGPT** and **Mem0** propose forgetting strategies (Ebbinghaus Forgetting Curve, importance scores) and re‑synthesis to keep memory relevant.

### Scratchpads and Intermediate Memories

Some systems use **scratchpads** or temporary notebooks to record intermediate reasoning.  Instead of polluting working memory with details, the scratchpad preserves calculations, hypotheses or lists that can be discarded later.  Frameworks like **LangChain** and **LangGraph** support scratchpads and explicit recursion.

### Semantic, Procedural and Meta‑Memory

In addition to episodic memories (sequence of events), advanced agents maintain **semantic memories** (facts, relations, business rules), **procedural memories** (macro actions that worked in past tasks) and **meta‑memories** (notes on how to manage memory).  These levels appear in implementations such as **ReasoningBank** (strategy memories), **Memory‑R1** (RL to add/update/delete), **Sentinel** (compression with proxies) and **Letta** (hierarchical memory with persistent blocks and shared memory).

---

## Frameworks, Libraries and Memory Platforms

This section introduces available solutions for implementing memory in agents.  We divide them into commercial/cloud platforms and open‑source frameworks, though many ideas overlap.

### Commercial and Cloud Platforms

**ChatGPT Memory (OpenAI)**:  ChatGPT offers a mode with persistent memories.  Users can ask the model to “remember” something and manage memories via settings.  Memory is optional, can be disabled and the remembrances are governed by privacy and security policies.  It is aimed at general UX and does not expose customisable APIs.

**Claude Memory & Memory Tool (Anthropic)**:  Anthropic launched memory in Claude initially for teams and enterprises.  The feature is opt‑in, with incognito mode and project boundaries to avoid leaks between departments.  Developers can use the **Memory Tool** and **Context Editing** on the developer platform to store information in files (`CLAUDE.md`) and free space in context.  The system is based on persistent files, structured notes and project separation.

**Memory Bank (Google Cloud)**:  Google’s Memory Bank allows creation of agents with long‑term memory.  It extracts facts from conversations using Gemini models, stores and updates those facts in a persistent bank, resolves contradictions and provides semantic and similarity search.  The API offers simple lookup and embedding queries and integrates with Vertex AI.

**Mindset Agent Memory**:  Mindset AI proposes an enterprise memory layer with **three levels of control**:  organisation policies (define what should be memorised), agent permissions (which memories each agent can read or write) and end‑user controls (who may review and edit their data).  The solution was built for compliance with GDPR, CCPA and emerging regulations and applies to customer support, HR, sales and other areas.

**Zep (GetZep)**:  Zep offers a context engineering platform with three components: **Agent Memory** (user memory with extraction of facts and preferences), **Graph RAG** (RAG over a temporal graph with dynamic data) and **Context Assembly** (automatic orchestration of context at each turn).  The graph is temporal and versioned and the platform includes recency policies and context cleaning.

**mem0**:  mem0 sells a universal memory layer with a multi‑level architecture (user, session and agent state) that speeds responses and reduces tokens.  It boasts performance superior to ChatGPT’s Memory and supports personalisation.  It has SDKs for Python and Node and offers a self‑hosted version.

**MemoryOS (BAI‑LAB)**:  A memory operating system that injects long‑term capabilities into agents.  It uses modules for storage, updating, retrieval and generation in a hierarchy inspired by operating systems.  It can be plug‑and‑play with any LLM and shows substantial gains in benchmarks.

### Open‑Source Frameworks and Libraries

**memori (GibsonAI)**:  A SQL‑native memory engine that supports two modes: **conscious** (ingests short memories and promotes the most important) and **auto** (intelligent search across the entire history).  It performs entity extraction and validation via Pydantic, defines priorities (identity, preferences, skills, projects, relationships) and exposes APIs for recording, querying and managing memories.  It can be integrated with frameworks like LangChain, AutoGen and LangGraph.

**ReMe (Modelscope)**:  A system that separates **task memory** (summarises successful actions and errors for reuse) and **personal memory** (records preferences, styles and user context).  It offers HTTP APIs to record and retrieve memories, identifying success/failure patterns and adapting to user behaviour.  It includes code examples for summarising and retrieving memories.

**memonto**:  Combines memory and ontologies.  It allows one to define a schema (RDF/OWL), extract information and store it in triple stores or vector stores.  It shows how to create instances in transient or persistent modes and provides operations to retain, recall and forget memories.  It supports SPARQL queries and summarisation.

**memary**:  A memory layer inspired by human memory, with agents (“ChatAgents”) that use memory streams, knowledge storage and personas.  It allows the creation of multi‑locale memories with persistent graphs and the passing of memories between agents.  The framework includes mechanisms for memory generation and editing, automatic extraction, recursive retrieval and multi‑hop reasoning over knowledge graphs.

**Cognee**:  Proposes a memory layer that combines graphs and vectors to replace RAG systems.  It interconnects documents (conversations, files, images, transcripts) and offers ingestion pipelines for more than 30 sources.  It can run locally with on‑device storage or be hosted in the cloud, reducing costs and simplifying development.

**Letta**:  An open‑source platform built by the creators of MemGPT for agents with **hierarchical memory**.  It introduces persistent memory blocks that can be edited or shared between agents, context engineering techniques in which the agent controls its own context (editing, deleting or searching blocks) and “sleeping” agents that run in the background to reorganise or improve memories.  It supports implementations in Python and TypeScript.

**Graphiti**:  A framework for building real‑time temporal knowledge graphs.  It integrates user interactions and enterprise data, sustains state‑based reasoning and task automation and allows complex queries via semantic search, keyword search and neighbourhood search.  It serves as the basis for Zep.

**GraphRAG and MemoRAG**:  Projects that explore graph‑structured RAG.  **GraphRAG** (Microsoft) provides a pipeline to transform text into graphs and query them with LLMs.  **MemoRAG** adds a global memory layer capable of processing up to millions of tokens, generating “clues” from the global memory to improve recall and optimising performance via cache.

**A‑MEM, MemGPT and Mem0**:  Academic research proposes dynamic, multi‑level memories.  **A‑MEM** uses zettelkasten principles to create structured notes, index them and update connections continuously.  **MemGPT** manages context with a memory hierarchy inspired by operating systems, bringing and removing segments from external memory on demand.  **Mem0** combines extraction, consolidation and dynamic retrieval, offering a graph‑memory version and showing a 26 % gain over proprietary memories.

**Sentinel**:  A context compression framework that uses a small proxy model to probe attention and select relevant sentences before building the context.  It allows up to 5× compression while maintaining comparable performance on QA tasks.  It can be attached to any RAG or agent pipeline with memory.

**Memory‑R1 and ReasoningBank**:  **Memory‑R1** employs reinforcement‑learning agents to manage memory (adding, updating, deleting or ignoring entries) and improves answers on benchmarks.  **ReasoningBank** converts interaction traces into high‑level memories (strategies of success and failure) that are retrieved to guide reasoning; coupled with test‑time scaling (MaTTS) it yields significant efficiency gains.

---

## Context Engineering: Concepts, Techniques and Patterns

Context engineering is about the dynamic orchestration of everything that enters the model’s window.  It addresses not only prompts but the **assembly** of instructions, memories, retrieved knowledge, tools, states and constraints.

### Components of Context

1. **Instructions and system prompts**:  guidelines defining agent behaviour (including persona, style and business rules).
2. **User input**:  the current prompt, possibly with metadata (e.g., preferred language, support channel).
3. **Short‑term memory**:  recent messages, ongoing objectives, tool states.
4. **Long‑term memory**:  summaries of past conversations, facts about the user, preferences, action history.
5. **Retrieved knowledge**:  documents, articles, APIs, business data or responses from RAG bases.
6. **Tools and definitions**:  schemas and instructions for how to call each function, actions available to the agent.
7. **Tool outputs**:  responses from APIs, database results, outputs of other functions.
8. **Global state**:  persistent variables of the agent (attempt counts, completed steps) and environment data.

Building contexts involves combining these blocks to fit the window and preserve coherence.  Platforms like Zep and Letta automate much of this selection and assembly.

### Classification and Variants of RAG

The acronym **RAG (Retrieval Augmented Generation)** refers to the use of information retrieval to provide additional context to the model.  In recent years many variants have emerged.  Below are some RAG classifications useful for agents:

* **Simple RAG**:  search a database (vector or textual) and concatenate the result with the user prompt.  Useful for factual questions.
* **RAG with memory**:  in addition to searching documents, retrieves past memories and combines them into the context.  Helps maintain consistency in dialogues.
* **Branched RAG**:  decides which source (documents, FAQs, logs) to query based on the input.
* **HyDe (Hypothetical Document Embedding)**:  the model generates a “hypothetical document” based on the question and uses that text as a query to retrieve relevant passages.
* **Adaptive RAG**:  adjusts the number and sources of documents depending on the complexity of the question or stage of the conversation.
* **CRAG (Corrective RAG)**:  the model critically evaluates retrieved documents and filters them before responding.
* **Self‑RAG**:  during generation the model issues sub‑queries to refine the answer.
* **Agentic RAG**:  involves autonomous agents (document agents, meta agents) that cooperate in multiple steps to plan, search, evaluate and answer.  Examples include Chain‑of‑Agents, LangGraph with multi‑agents and ReasoningBank.
* **Graph RAG**:  uses a knowledge graph (nodes and edges) instead of text chunks.  It allows traversing relationships and answering multi‑hop questions.  Tools such as Graphiti, GraphRAG and Memary explore this approach.
* **MemoRAG**:  integrates RAG with global memory; produces “clues” derived from memory to improve the query and reuses contexts via caching.

These categories can be combined.  For example, an agentic RAG can employ graph RAG and persistent memories simultaneously.

### Compression, Compaction and Structured Notes

Because the context window is limited and storage costs tokens, **compression** and **compaction** techniques become essential.  Key techniques include:

* **Incremental summaries**:  at each step produce short summaries that replace long segments in context.
* **Auto‑compression**:  use smaller models (proxy models) to select relevant sentences (as in Sentinel) or apply attention algorithms over the full context to filter important passages.
* **Structured notes (agentic notes)**:  store memories as notes with fields (description, tags, links) instead of unstructured text snippets.  This strategy is common in A‑MEM, Letta and Zep; it facilitates re‑indexing and creation of relations.
* **Compaction via scripts**:  on platforms like Claude, the model can “clean” the context by removing old tool call results after the next step, freeing space for new information.

### Isolation of Contexts and Multi‑Agents

Complex systems often divide tasks into specialised sub‑agents, each with its own context and objective.  **Isolating contexts** prevents one agent from bringing irrelevant information or polluting the global memory.  Frameworks like **LangGraph** and **Chain‑of‑Agents** allow you to create pipelines where sub‑agents conduct deep explorations, return summaries to a manager and discard their private contexts.  **Zep** implements “projects” that separate professional memories.

### Auditing, Privacy Controls and Governance

When storing sensitive data, it is critical to maintain audit trails, comply with laws (GDPR, CCPA, AI Act) and allow users to review or delete their memories.  Enterprise solutions (Mindset AI, Zep) implement authorisation layers, versioning and access logs.  The **Memory Tool** of Claude offers an incognito mode, and ChatGPT provides a screen to manage memories.  Open‑source frameworks like memori provide database export in SQL for external inspection.

---

## Advanced Patterns and Cutting‑Edge Research

This section addresses concepts at the forefront of memory for agents and context engineering.  Many of these topics are ongoing in 2025 and represent boundaries for research and products.

### RL for Memory Management

Projects like **Memory‑R1** train a **Memory Manager** through reinforcement learning to decide when to add, update, delete or not touch a memory entry.  Another agent (“Answer Agent”) consumes the selected memories to answer questions.  Experiments show gains in Q&A benchmarks.  Similar strategies could be applied to enterprise knowledge bases.

### Reasoning About Strategies of Success (ReasoningBank)

**ReasoningBank** stores not only facts but **strategies** derived from past executions (both successes and failures).  Each memory item contains a title, description and content with heuristics.  A retrieval mechanism injects relevant strategies during execution, improving performance on complex tasks.  The framework uses test‑time scaling techniques (MaTTS) to leverage multiple executions.

### Agentic RAG and Cooperative Multi‑Agents

**Agentic RAG** combines several ideas:  agents capable of reflection, planning and iterative searches; specialised sub‑agents (e.g., document agents, tool agents); and a coordinating meta‑agent.  Google research (Chain‑of‑Agents) demonstrates that dividing reading tasks into sections and using messages between agents reduces the quadratic cost of processing long contexts and improves quality.  Other work classifies agentic RAG into single‑agent, multi‑agent and hierarchical categories.

### Dynamic and Temporal Graph RAG

**Graph RAG** applies RAG to knowledge graphs, allowing multi‑hop reasoning and queries over entities and relationships.  Zep uses **temporal graphs** (with start and end validity) to manage business data and user preferences over time.  Tools such as **Graphiti**, **Memary** and **GraphRAG** show how to extract graphs from text, index them and retrieve relevant paths.

### Compression with Proxy Models (Sentinel)

**Sentinel** proposes using a small model (0.5 B parameters) to probe attention over the context and determine which sentences should be kept.  After classification, the chosen sentences are concatenated and passed to the larger model.  This technique reduces context by up to five times while maintaining performance on QA tasks.

### Ontologies, Triples and Structured Contexts

Frameworks such as **memonto** and emerging research suggest that memories based on ontologies (triples `subject–predicate–object`) can improve interpretability and querying.  By storing facts with a formal schema, the agent can use languages like SPARQL or Cypher to retrieve information and then convert the response into free text.  Mixing this approach with embeddings (vector store) improves recall.

### Multi‑Modal and Multi‑Agent Shared Memory

Solutions such as **Letta** support memory shared between agents, including multiple modalities (text, images, audio).  This allows teams of agents to cooperatively solve tasks, such as retrieving spreadsheet data, generating multimodal reports or orchestrating development workflows.

---

## Practical Examples and Python Implementations

This section provides simplified code snippets that demonstrate memory and context engineering concepts.  They are not substitutes for complete solutions but help illustrate how things work.

### Example 1 – Local prototype with `memori`

`memori` is a SQL‑native memory engine.  The following example records a user’s preferences, retrieves relevant context and assembles a prompt for an LLM (such as GPT‑4o‑mini).

```python
from memori import Memori
from openai import OpenAI

# initialise Memori and the LLM
memori = Memori(conscious_ingest=True)
client = OpenAI()

# record user messages
memori.record_message("user123", "I prefer VS Code and I code in Python.")
memori.record_message("user123", "I'm migrating my backend to FastAPI.")

# retrieve relevant context (prioritises facts, preferences, skills, projects)
context = memori.retrieve_context("Which editor does the user use?")

# build a prompt using the context
def assemble_prompt(user_query, ctx):
    bullets = "\n".join(f"- {c}" for c in ctx)
    system = (
        "You are a development assistant. Take into account the user's preferences listed below.\n"
        f"Preferences/Facts:\n{bullets}\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_query},
    ]

messages = assemble_prompt("Help me set up automated tests.", context)
resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
print(resp.choices[0].message.content)
```

This example shows how to combine memory recording, retrieval and context assembly to improve personalisation.  `memori` provides additional APIs for management (listing, deleting, summarising memories) and integrations with agent frameworks.

### Example 2 – Simplified Temporal Graph

To illustrate the idea of temporal graphs, the following example uses `networkx` to record facts and query the graph for recency.

```python
import networkx as nx
from datetime import datetime

G = nx.DiGraph()

# add a user and facts with timestamps
G.add_node("user123", type="user")

def add_fact(user, predicate, obj, t=None):
    t = t or datetime.utcnow().isoformat()
    node_id = f"{user}:{predicate}:{obj}:{t}"
    G.add_node(node_id, user=user, pred=predicate, obj=obj, t=t, type="fact")
    G.add_edge(user, node_id, rel="has_fact")

add_fact("user123", "prefers", "VS Code")
add_fact("user123", "language", "Python")

def recall_facts(user, predicates=("prefers", "language")):
    facts = []
    for nbr in G.neighbors(user):
        data = G.nodes[nbr]
        if data.get("pred") in predicates:
            facts.append(f"{data['pred']} {data['obj']} ({data['t']})")
    return sorted(facts, reverse=True)

print(recall_facts("user123"))
```

### Example 3 – Context Assembly

This function assembles a context with blocks of memories, business facts and tool definitions:

```python
def context_assembly(user_query: str,
                     user_memories: list[str],
                     business_facts: list[str],
                     tool_schemas: list[dict]) -> list[dict]:
    m_block = "\n".join(f"- {m}" for m in user_memories[:5])
    b_block = "\n".join(f"- {b}" for b in business_facts[:8])
    system = (
        "You are a support agent. "
        "Take into account the user's preferences and history (below) and the latest business data.\n\n"
        f"[User memories]\n{m_block}\n\n"
        f"[Business facts]\n{b_block}\n"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_query},
    ]
    return messages
```

---

## Trends, Challenges and Future Possibilities

The field of memory for agents and context engineering is evolving rapidly.  Some trends identified up to October 2025 include:

* **Integration of graphs and embeddings**:  models combine knowledge graphs and vectors to improve recall and precision.  Tools such as Memary and Graphiti show that mixing explicit and semantic relations yields more robust answers.
* **Federated and distributed memory**:  to meet data sovereignty requirements and reduce latency, proposals emerge for federated storage, where memories remain close to the user and are aggregated on demand.
* **Context Operating Systems**:  frameworks like MemoryOS and ReMe point to the creation of “memory operating systems,” with standardised storage, policy and interface layers, dynamic allocation and multiple applications.
* **Continuous learning and adaptation**:  memories can evolve automatically based on user interaction; RL frameworks like Memory‑R1 allow the system to learn which memories to keep or discard based on feedback.
* **Compliance and controls**:  with laws such as GDPR and the AI Act, the ability to audit and manage personal data becomes a priority.  Corporate tools include deletion, anonymisation and versioning mechanisms.

---

## References and Further Reading

This section lists articles, papers, repositories and blog posts that support this guide.  They cover definitions of memory and context engineering as well as implementation frameworks and recent research.  Inline citations have been removed from the body to make the reading more fluid; consult the references to explore the details.

---

## FULL LINKS

Below are complete links for the main sources used in this guide (not exhaustive):

1. **Sundeep Teki – “Context Engineering: A Framework for Robust Generative AI Systems”** – <https://www.sundeepteki.org/blog/context-engineering-a-framework-for-robust-generative-ai-systems>
2. **Galileo AI – “Deep Dive into Context Engineering for Agents”** – <https://www.galileo-ai.com/blog/deep-dive-into-context-engineering-for-agents>
3. **Anthropic – “Effective Context Engineering for AI Agents”** – <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
4. **Anthropic – “Bringing Memory to Teams at Work”** – <https://www.anthropic.com/news/memory>
5. **Anthropic Developer Platform – “Context Editing and Memory Tool”** – <https://www.anthropic.com/developer-tools/context-editing-memory-tool>
6. **Simon Willison – “Claude Memory vs ChatGPT Memory”** – <https://simonwillison.net/2025/sep/claude-memory>
7. **Skywork AI – “Claude Memory: A Deep Dive into Anthropic’s Persistent Context Solution”** – <https://skywork.ai/blog/claude-memory-a-deep-dive-into-anthropics-persistent-context-solution>
8. **Fylle AI – “Context Engineering: The Foundation Your AI Team Actually Needs”** – <https://www.fylle.ai/blog/context-engineering-the-foundation-your-ai-team-needs>
9. **LlamaIndex – “Context Engineering: What it is, and Techniques to Consider”** – <https://www.llamaindex.ai/blog/context-engineering-techniques>
10. **Tribe AI – “Beyond the Bubble: How Context‑Aware Memory Systems Are Changing the Game in 2025”** – <https://www.tribe.ai/blog/context-aware-memory-systems>
11. **Mindset AI – “AI Agent Memory: Why Your AI Agents Keep Forgetting Everything”** – <https://www.mindset.ai/blog/ai-agent-memory-why-your-ai-agents-keep-forgetting-everything>
12. **Google Cloud – “Introducing Memory Bank: Building Stateful, Personalised AI Agents with Long‑Term Memory”** – <https://dr-arsanjani.medium.com/introducing-memory-bank-building-stateful-personalized-ai-agents-with-long-term-memory-f714629ab601>
13. **Google Research Blog – “Chain of Agents: Large Language Models Collaborating on Long Context Tasks”** – <https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/>
14. **Meilisearch – “14 Types of RAG Architectures Explained”** – <https://www.meilisearch.com/blog/14-types-of-rag-architectures>
15. **Humanloop – “8 Retrieval Augmented Generation Architectures You Should Know in 2025”** – <https://humanloop.com/blog/8-rag-architectures-in-2025>
16. **Firecrawl – “Best Open‑Source RAG Frameworks”** – <https://www.firecrawl.dev/blog/best-open-source-rag-frameworks>
17. **A‑MEM: Agentic Memory for LLM Agents (Paper)** – <https://arxiv.org/abs/2502.12110>
18. **MemGPT: Virtual Context Management for LLMs (Paper)** – <https://arxiv.org/abs/2310.08560>
19. **Self‑Controlled Memory (SCM) – Enhancing LLMs with Self‑Controlled Memory (Paper)** – <https://arxiv.org/abs/2304.13343>
20. **MemoryBank: Enhancing LLMs with Long‑Term Memory (Paper)** – <https://arxiv.org/abs/2305.10250>
21. **Mem0: Building Production‑Ready AI Agents with Scalable Long‑Term Memory (Paper)** – <https://arxiv.org/abs/2404.07747>
22. **MemoChat – Tuning LLMs to Use Memos for Consistent Long‑Range Open‑Domain Conversation (Paper)** – <https://arxiv.org/abs/2308.07938>
23. **Memory‑R1: Reinforcement‑Learning for Memory Management (Paper)** – <https://arxiv.org/abs/2508.19828>
24. **ReasoningBank: A Memory Framework for Strategy‑Level Experiences (Paper)** – <https://arxiv.org/abs/2509.25140>
25. **From Human Memory to AI Memory: A Survey on Memory Mechanisms in the Era of LLMs** – <https://arxiv.org/abs/2404.14986>
26. **A Survey of Context Engineering for Large Language Models** – <https://arxiv.org/abs/2407.06643>
27. **Sentinel: Attention Probing of Proxy Models for LLM Context Compression (Paper)** – <https://arxiv.org/abs/2405.08019>
28. **Memory‑OS – Universal Memory Operating System (GitHub)** – <https://github.com/BAI-LAB/MemoryOS>
29. **memori (GibsonAI) – Memory Engine (GitHub)** – <https://github.com/GibsonAI/memori>
30. **ReMe – Memory Management Framework (GitHub)** – <https://github.com/modelscope/ReMe>
31. **memonto – Memory + Ontology (GitHub)** – <https://github.com/shihanwan/memonto>
32. **memary – Long‑Term Memory Layer (GitHub)** – <https://github.com/kingjulio8238/Memary>
33. **Cognee – Graph and Vector Memory Layer (GitHub)** – <https://github.com/topoteretes/cognee>
34. **Graphiti – Temporal Knowledge Graph Framework (GitHub)** – <https://github.com/getzep/graphiti>
35. **mem0 – Universal Memory Layer (GitHub)** – <https://github.com/mem0ai/mem0>
36. **Letta – Stateful Agents with Hierarchical Memory (GitHub)** – <https://github.com/letta-ai/letta>
37. **MemoRAG – RAG with Global Memory (GitHub)** – <https://github.com/qhjqhj00/MemoRAG>
38. **GraphRAG – Graph‑Based Retrieval Augmented Generation (GitHub)** – <https://github.com/microsoft/graphrag>
39. **Context Engineering – Zero to Hero (GitHub)** – <https://github.com/davidkimai/Context-Engineering>
40. **Awesome Context Engineering (GitHub)** – <https://github.com/ak0x/awesome-context-engineering>
41. **Awesome AI Memory (GitHub)** – <https://github.com/topoteretes/awesome-ai-memory>
42. **Memory Bank Medium Article** – <https://medium.com/@dr-arsanjani/introducing-memory-bank-building-stateful-personalized-ai-agents-with-long-term-memory-f714629ab601>

---