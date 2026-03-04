# Google Best Guide for AI AGENTS

# 1) Minimal Agent Architecture (the 1→4 flow you showed)

```text
[User]
  │ (1) Goal / prompt
  ▼
┌─────────────┐
│   AGENT     │  decides plan (ReAct), chooses tools, manages state
└─────────────┘
  │ (2) Select Tool B + build structured call (function-calling)
  ▼
┌─────────────┐
│   MODEL     │  interprets instructions + tool schema; returns call args
└─────────────┘
  │ (3) Runtime invokes Tool B {args}
  ▼
┌───────────────────────┐
│  TOOLS: A | B | C     │  side effects, data access, retrieval
└───────────────────────┘
  │ (4) Tool output → observation
  ▼
┌─────────────┐
│   AGENT     │  integrates observation; composes final answer
└─────────────┘
```

**Design tenets**

* Separate concerns: **model** (reason), **agent** (decide/orchestrate), **tools** (act), **runtime** (scale/observe), **memory** (state).
* Treat tools as **APIs for a model**: clear name, typed params, “when to use”, structured return.
* Log **thought → action → observation** per step for debuggability.

# 2) ReAct Loop (reason → act → observe)

```text
User → Agent
Agent → Model: think with current state
Model → Agent: intent + tool choice (or direct answer)
Agent → Tool_k: call(args)
Tool_k → Agent: observation
Agent → Model: updated context (state + observation)
... repeat until {goal met ∨ max steps ∨ budget hit ∨ non-recoverable error}
Agent → User: final answer (+ evidence if applicable)
```

**Good practice**

* Explicit stop criteria; cap step count and token/latency budget.
* Penalize “no-progress” loops; surface stop reason.
* Timeouts, retries with jitter, circuit breakers around tools.

# 3) Orchestration Patterns

## 3.1 Sequential (fixed pipeline)

```text
Input → [Agent A] → [Agent B] → [Agent C] → Output
```

Deterministic stages with dependencies (crawl → extract → validate → summarize).

## 3.2 Parallel (fan-out / fan-in)

```text
           ┌→ [Agent B1]
Input → A ─┼→ [Agent B2]  ──► merge/aggregate → Output
           └→ [Agent B3]
```

Independent subtasks (multi-source retrieval, heavy computations). Aggregate at the end.

## 3.3 Iterative loop (refine / reflect)

```text
Seed draft → [Agent(s)] ↺ refine until {quality ≥ threshold ∨ N iters ∨ no-improvement}
```

Common for code review, editing, planning. Add “reflection” and “deliberate self-check”.

## 3.4 Agent-as-a-Tool (hierarchical delegation)

```text
[Orchestrator] ──(calls as a tool)──► [Specialist Agent]
```

Keeps control while delegating complex sub-skills.

## 3.5 Planner–Executor

```text
[Planner Agent] → plan {steps, tools, success criteria}
[Executor Agents] → execute plan step-by-step with feedback
[Validator/Reviewer] → gate high-risk outputs
```

## 3.6 Debate / Committee (for hard judgments)

Parallel agents propose → critique → vote/rank → arbiter composes final.

## 3.7 Human-in-the-Loop (HITL)

Gate actions with material risk (payments, PII changes, provisioning) via approval tasks.

# 4) Grounding & RAG (basic → graph → agentic)

## 4.1 Ingestion pipeline

```text
Raw sources (PDF/HTML/DB/Audio/Image)
 → parse/clean
 → chunk (semantic/structure-aware, with overlap)
 → enrich with metadata (title, section, date, perms)
 → embed (text / image / audio as needed)
 → index (vector DB) + optional symbolic KB (graph)
```

## 4.2 Retrieval pipeline (two-stage)

```text
Query → embed → High-recall ANN (topK)
        → Re-rank (LLM or specialized ranker) for precision
        → Context compression (focused summaries, citation map)
        → Answer generation tied to evidence
```

Key rules: always re-rank; compress context; include **attributions**; reject low-confidence.

## 4.3 GraphRAG

Model entities/relations (graph) to support multi-hop questions, narrative paths, and explainability.

## 4.4 Agentic RAG (the agent “plans to retrieve”)

```text
Goal → plan sub-queries → retrieve & expand iteratively
     → check gaps → reformulate queries
     → consolidate evidence (with citations)
     → (optional) call transactional tools
     → answer
```

## 4.5 Quality controls

Faithfulness checks, contradiction detection, date/version sanity, deduping, and coverage thresholds.

# 5) Memory & State (layered)

```text
┌─────────────────────────────────────────────┐
│ Long-term KB / Vector store (grounding)    │  versioned knowledge, distilled facts
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Working memory / Session cache              │  low-latency context for the active task
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Transactional ledger (ACID, audit trail)   │  durable record of real-world actions
└─────────────────────────────────────────────┘
```

* Distill conversational history into **facts** (not raw logs).
* Use **idempotency keys** and compensation (sagas) for actions.
* Keep ephemeral vs. durable state separate.

# 6) Tool Design (contracts for models)

**Contract shape**

* **Name & scope**: short, unique, imperative (avoid overlapping semantics).
* **Typed parameters**: enums/ranges/regex; defaults documented.
* **Docstring**: when to use, what it returns, what it does **not** do; 1–2 mini examples.
* **Return**: `{"status": "success|error", "data": {...}, "error": {...}}`.
* **Access**: tool context can read/write session state through a narrow interface.
* **Resilience**: timeouts, retry with backoff+jitter, circuit breaker, backpressure limits.
* **Security**: strict input validation, allow-lists, redaction of secrets, least privilege.
* **Determinism**: keep tool behavior testable without the LLM.

**Composition patterns**

* **Toolsets** (bundle related capabilities).
* **Agent-as-Tool** (delegate expertise behind a single schema).
* **Open interop** (expose/consume tools and agents via standard schemas & auth).

# 7) Runtime & Systems Engineering

```text
Client / API Gateway
  → AuthN/Z + Quotas/Rate Limits
  → (Async) Queue & Workers OR (Sync) Service
  → Agent Service (state, planning, model routing)
  → Model API(s)
  → Tooling layer (internal APIs, DBs, external services)
  → Observability (traces, logs, metrics, events)
  → Transaction Ledger (for side effects)
  → Caches (LLM results, retrieval, API responses)
```

**Operational patterns**

* Autoscaling; bulkheads to isolate noisy dependencies.
* Hedged requests for flaky paths; dead-letter queues for poison jobs.
* Per-tool rate limits and concurrency pools.
* Streaming responses; partial results with graceful degradation.
* Strict **idempotency** for all side-effectful calls.

# 8) AgentOps: Testing, Evaluation, Monitoring

**Four layers**

1. **Unit** — deterministic components (tools, parsing, adapters).
2. **Trajectory** — verify step sequence: tool choice + args + observations (golden traces).
3. **Outcome** — semantic quality: faithfulness, completeness, format; LLM-as-judge + human rubrics.
4. **Production** — latency, cost (tokens/calls), error rates, loop count, drift detection.

**CI/CD quality gates**

* Pin model & prompt versions; run golden trajectories; measure outcomes on curated datasets.
* Canary releases; rollback on KPI regression.
* Trace every step (OpenTelemetry-style), link to inputs/outputs (hashes for PII safety).

**Key metrics**

* Step count per session; tool selection accuracy; tool failure rate; % grounded answers; coverage; abandonments; cost/req; p95 latency.

# 9) Security, Privacy, Governance

* **Least privilege** everywhere; rotate and scope secrets; never place secrets in prompts.
* **Defense-in-depth**: input validation (prompt-injection/exfil), output filtering, allow-lists, kill-switches.
* **HITL** for high-risk actions; dual control for irreversible effects.
* **Data governance**: classification, minimization, retention/SLA, encryption at rest/in transit, audit logs, PITR.
* **Compliance**: consent/notice in UX; bias/equity testing; red-teaming.
* **Grounding verification** for critical domains; require citations/evidence links.

# 10) Cost & Performance

* Route requests by **capacity × cost × latency** (right-sized models per subtask).
* Enforce **reasoning budgets** (tokens/latency) per step and per session.
* Cache expensive results (LLM completions, RAG contexts, API replies).
* Precompute embeddings and “guide” summaries for hot content.
* Use semantic chunking; always re-rank; compress context.
* Parallelize where safe; bound concurrency to protect dependencies.

# 11) Anti-Patterns (avoid)

* Swiss-army **tool**: ambiguous, overlapping responsibilities.
* Prompt soup: verbose, contradictory, or leaking internal secrets.
* Mixing ephemeral and transactional state.
* Evaluating only final text (ignoring the trajectory).
* Unbounded loops; missing stop criteria.
* RAG without re-rank/attribution; stale or unversioned indexes.
* Scaling without rate limits or isolation.

# 12) Copy-Paste Templates

## 12.1 Tool contract (skeleton)

```python
def get_order(order_id: str, *, ctx: ToolCtx) -> dict:
    """
    PURPOSE: Fetch order by ID for refund/eligibility decisions.
    WHEN_TO_USE: Missing purchase_date or status in context.
    ARGS:
      - order_id: external UUIDv4.
    RETURNS:
      {"status": "success|error",
       "data": {"purchase_date": "YYYY-MM-DD", "status": "PAID|REFUNDED|..."},
       "error": {"type": "...", "message": "..."}} 
    RUNTIME:
      timeout=1500ms; retries=2 (exponential+jitter); idempotency_key=order_id
    SECURITY:
      validate UUID; denylist dangerous patterns; scope DB to tenant in ctx
    """
    ...
```

## 12.2 ReAct stop criteria

```text
- Programmatic goal satisfied (validator passes).
- No progress in K iterations (same thoughts/tools).
- Token or latency budget exceeded.
- Non-recoverable error (dependency down; policy violation).
```

## 12.3 Trajectory test (spec)

```text
Given: prompt + fixed tool mocks + seed
Expect: sequence of steps (tool names + args), ≤ N iterations,
        and final answer that meets rubric X (format, grounding, completeness).
```

## 12.4 Minimal “Agent Card” (for inter-agent calls)

```json
{
  "name": "ContractsSummarizer",
  "capabilities": ["retrieve_citations", "summarize", "compare_versions"],
  "api": {"invoke_url": "...", "auth": "bearer", "schema_url": "..."},
  "ios": {"rate_limit_rps": 5, "max_concurrency": 10},
  "slo": {"p95_latency_ms": 1800, "error_budget_pct": 1.0}
}
```

---

## Executive TL;DR

1. Architect in **blocks**: Model (reason), Agent (decide), Tools (act), Memory (state layers), Runtime (scale/observe).
2. Orchestrate via **ReAct** plus **sequential/parallel/loop** and **agent-as-tool**.
3. Do **RAG right**: robust ingestion → retrieve → **re-rank** → compress → answer with evidence; consider GraphRAG and Agentic RAG.
4. Use **layered memory**: working/session, long-term KB, transactional ledger.
5. Practice **AgentOps**: unit/trajectory/outcome/production; CI gates; traces.
6. Build **security & governance** in: least privilege, validation, HITL, audits.
7. Optimize **cost/perf**: model routing, reasoning budgets, caching, parallelism with limits.
