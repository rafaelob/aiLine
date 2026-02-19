# Sprint 0010 — SSE Streaming Pipeline

**Status:** completed | **Date:** 2026-02-14
**Goal:** Real-time pipeline progress via Server-Sent Events (SSE), WebSocket for
tutor chat, and event-driven architecture for stage transitions.

---

## Scope & Acceptance Criteria

The plan generation pipeline must stream real-time progress to the frontend via SSE.
The tutor chat must use WebSocket for bidirectional real-time messaging with
token-by-token LLM output. An internal EventBus (InMemoryEventBus or Redis PubSub)
bridges pipeline workflow nodes to SSE/WS endpoints. All connections must handle
client disconnects gracefully, send periodic heartbeats, and support auto-reconnect
on the frontend.

---

## Architecture

- **SSE** for plan generation pipeline: unidirectional server-to-client events
  covering the full lifecycle (Planner -> Validate -> Refine -> Execute -> Export -> Done).
- **WebSocket** for tutor chat: bidirectional real-time messaging with streaming
  token output from the LLM.
- **sse-starlette 3.2.0** wraps FastAPI's StreamingResponse with proper SSE
  framing, Last-Event-ID support, and connection lifecycle management.
- **EventBus** (`InMemoryEventBus` already in
  `adapters/events/inmemory_bus.py`) publishes pipeline events from workflow nodes;
  the SSE endpoint subscribes to a run-specific channel and yields events to the
  client. Redis PubSub adapter is an optional upgrade for multi-process deployments.

### LangGraph Static Fan-Out Topology (Reference Pattern from GPT-5.2/Codex)

The plan generation pipeline uses LangGraph's static fan-out with branch envelopes
for parallel execution of independent stages and conditional routing for the
quality-gate/refine loop. This is the exact pattern to follow during implementation.

```python
from langgraph.graph import StateGraph, START, END

async def safe_branch(fn, *args, **kwargs):
    """Branch error envelope: wraps a node so one failing branch does not
    kill the entire fan-out.  The downstream fan-in node inspects `ok` and
    proceeds if at least one branch succeeded (ADR-023)."""
    try:
        return {"ok": True, "payload": await fn(*args, **kwargs), "error": None}
    except Exception as e:
        return {"ok": False, "payload": None, "error": str(e)}

# Graph topology -- static edges for parallelism, conditional for quality loop
graph = StateGraph(PipelineState)
graph.add_node("rag_search", rag_search_node)
graph.add_node("profile_analysis", profile_analysis_node)
graph.add_node("planner", planner_node)
graph.add_node("quality_gate", quality_gate_node)
graph.add_node("refine", refine_node)
graph.add_node("executor", executor_node)

# Parallel fan-out from START to both RAG and Profile nodes
graph.add_edge(START, "rag_search")
graph.add_edge(START, "profile_analysis")

# Fan-in: both must complete before Planner runs
graph.add_edge(["rag_search", "profile_analysis"], "planner")

# Sequential: Planner -> Quality Gate
graph.add_edge("planner", "quality_gate")

# Conditional routing after quality gate
def route_after_gate(state):
    if state["quality_score"] >= 80 or state["refine_count"] >= 2:
        return "executor"
    return "refine"

graph.add_conditional_edges("quality_gate", route_after_gate, ["executor", "refine"])
graph.add_edge("refine", "quality_gate")  # Loop back for re-evaluation
graph.add_edge("executor", END)
```

Key topology details:
- `START -> [rag_search, profile_analysis]` runs both nodes concurrently (static
  fan-out via two edges from START).
- The list-based `add_edge(["rag_search", "profile_analysis"], "planner")` creates
  a fan-in barrier: Planner only executes after both branches complete.
- `safe_branch()` wraps each fan-out node so that if one fails the other's results
  still flow to the Planner (ADR-023 branch error envelopes).
- `route_after_gate()` implements the quality loop: score >= 80 or 2 refine
  iterations reached means proceed to executor; otherwise loop back through refine.

**Data flow (SSE):**
```
LangGraph node (planner/validate/execute)
  -> EventBus.publish("run:{run_id}", event)
     -> SSE endpoint subscription
        -> format_sse_event(type, data)
           -> StreamingResponse to client
```

**Data flow (WebSocket):**
```
Client WS message {type: "message", content: "..."}
  -> FastAPI WebSocket endpoint
     -> TutorUseCase (LangGraph tutor graph)
        -> LLM streaming (token-by-token)
           -> WS send {type: "token", content: "..."}
              -> WS send {type: "complete", message: {...}}
```

---

## Stories

### S10-001: FastAPI SSE Endpoint /plans/generate/stream

**Description:** SSE endpoint that streams pipeline stage transitions, progress
updates, validation results, export readiness, and final completion to the client.
The endpoint accepts a plan generation request via POST, starts the pipeline in a
background task, publishes events through the EventBus, and yields them as SSE to
the connected client.

**Files:**
- `runtime/ailine_runtime/api/routers/plans.py` (add `POST /generate/stream`)
- `runtime/ailine_runtime/api/streaming/sse.py` (extend with `SSEChannel`,
  `merge_generators`, connection lifecycle helpers)
- `runtime/ailine_runtime/workflow/plan_workflow.py` (add EventBus publish calls
  in each node function: `planner_node`, `validate_node`, `bump_refine`,
  `executor_node`)
- `runtime/ailine_runtime/api/schemas/plans.py` (new: request/response schemas)

**Implementation details:**
- `POST /plans/generate/stream` accepts the same `PlanGenerateIn` body as the
  existing `/generate` endpoint.
- Returns `Content-Type: text/event-stream` via `sse-starlette`'s
  `EventSourceResponse`.
- Creates an `asyncio.Queue` per run, subscribes it to the EventBus channel
  `run:{run_id}`, starts the pipeline via `asyncio.create_task`.
- The SSE generator reads from the queue and yields formatted events.
- A heartbeat coroutine sends `event: heartbeat` every 15 seconds.
- On client disconnect (`asyncio.CancelledError`), the background task is
  cancelled and the queue subscription removed.
- On pipeline error, an `event: error` is sent before closing the stream.

**SSE Event Format:**
```
event: stage_change
data: {"stage": "planner", "status": "active", "run_id": "01JKXYZ...", "timestamp": "2026-02-14T10:00:00Z"}

event: progress
data: {"stage": "planner", "message": "Generating study plan draft...", "percent": 30}

event: validation_result
data: {"stage": "validate", "score": 82, "status": "pass", "errors": [], "warnings": ["Missing visual schedule notes"]}

event: stage_change
data: {"stage": "executor", "status": "active"}

event: export_ready
data: {"variant": "standard_html", "preview_url": "/exports/01JKXYZ.../standard_html"}

event: complete
data: {"run_id": "01JKXYZ...", "plan_id": "01JKABC...", "score": 85, "exports_count": 9}
```

**Typed Event Contract (from Codex/GPT-5.2 architecture review):**

14 canonical event types:
`run.started`, `stage.started`, `stage.progress`, `quality.scored`,
`quality.decision`, `refinement.started`, `refinement.completed`,
`tool.started`, `tool.completed`, `stage.completed`, `stage.failed`,
`run.completed`, `run.failed`, `heartbeat`

Event envelope format:
```python
{
    "run_id": str,       # UUID v7 identifying the pipeline run
    "seq": int,          # Monotonically increasing per run (1, 2, 3, ...)
    "ts": str,           # ISO 8601 UTC timestamp (e.g. "2026-02-14T10:00:00.123Z")
    "type": str,         # One of the 14 canonical event types
    "stage": str | None, # Current stage name, or None for run-level events
    "payload": dict,     # Event-type-specific data
}
```

**SSE Event Mapper (Reference Implementation from GPT-5.2/Codex):**

This is the exact pattern that maps LangGraph `astream_events(version="v2")`
output into the typed SSE event contract. The SSE endpoint generator function
should follow this structure.

```python
async def sse_stream(request, graph, input_data):
    """Generator that maps LangGraph astream_events into typed SSE events.

    Yields dicts matching the event envelope schema. The caller (SSE endpoint)
    serialises each dict as `event: {type}\ndata: {json}\n\n`.
    """
    run_id = str(new_uuid7())
    seq = 0

    def make_event(event_type, stage=None, payload=None):
        nonlocal seq
        seq += 1
        return {
            "run_id": run_id,
            "seq": seq,
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "stage": stage,
            "payload": payload or {}
        }

    try:
        yield make_event("run.started")

        async for event in graph.astream_events(input_data, version="v2"):
            kind = event["event"]
            if kind == "on_chain_start":
                yield make_event("stage.started", stage=event["name"])
            elif kind == "on_chain_end":
                yield make_event(
                    "stage.completed",
                    stage=event["name"],
                    payload={"summary": str(event.get("data", {}))[:200]}
                )
            elif kind == "on_chat_model_stream":
                yield make_event(
                    "stage.progress",
                    stage=event["name"],
                    payload={"token": event["data"]["chunk"].content}
                )

        yield make_event("run.completed")
    except Exception as e:
        yield make_event("run.failed", payload={"error": str(e)})
    finally:
        # Terminal safety: ALWAYS emit a final event.
        # The try/except above already covers run.completed and run.failed,
        # so `finally` is reserved for cleanup (unsubscribe queue, cancel
        # heartbeat task).  If neither run.completed nor run.failed was
        # emitted (e.g. CancelledError), emit run.failed here.
        pass
```

Implementation notes for the mapper:
- `graph.astream_events(input_data, version="v2")` is the LangGraph streaming API
  that yields structured events for every node/chain/model step.
- `on_chain_start` and `on_chain_end` correspond to node entry/exit and map
  directly to `stage.started` / `stage.completed`.
- `on_chat_model_stream` captures individual LLM tokens and maps to
  `stage.progress` (subject to 250ms throttle).
- Quality-gate events (`quality.scored`, `quality.decision`) and refinement events
  (`refinement.started`, `refinement.completed`) are emitted explicitly by their
  respective nodes via EventBus rather than inferred from astream_events, because
  they carry domain-specific payloads (score, decision reason, iteration count).
- Tool events (`tool.started`, `tool.completed`) map from `on_tool_start` /
  `on_tool_end` in the astream_events v2 stream.

Contract constraints:
- **Terminal safety:** ALWAYS emit `run.completed` or `run.failed` in a `finally`
  block so the client never hangs waiting for a terminal event.
- **Monotonic `seq` per run:** Every event carries a monotonically increasing
  sequence number scoped to the run; clients use this for ordering and gap
  detection.
- **`Last-Event-ID` support:** On reconnect the server replays events with
  `seq > last_event_id` from the in-memory buffer (last 50 events per run).
- **Throttle progress events:** Minimum 250 ms between consecutive
  `stage.progress` events to prevent event flood on the client.
- **Batch token events:** Aggregate individual token yields into batched SSE
  messages to reduce total SSE message count and parsing overhead.
- **Heartbeat:** Every 15 seconds via `asyncio.create_task` running a loop that
  yields `make_event("heartbeat")` into the SSE queue. The heartbeat task must
  be cancelled in the `finally` block.

**Acceptance Criteria:**
- [ ] `POST /plans/generate/stream` accepts plan generation request body
- [ ] Returns SSE stream with `Content-Type: text/event-stream`
- [ ] Event types emitted match the typed contract: `run.started`,
      `stage.started`, `stage.progress`, `quality.scored`, `quality.decision`,
      `refinement.started`, `refinement.completed`, `tool.started`,
      `tool.completed`, `stage.completed`, `stage.failed`, `run.completed`,
      `run.failed`, `heartbeat`
- [ ] Event envelope follows `make_event` format with `run_id`, `seq`, `ts`,
      `type`, `stage`, `payload`
- [ ] Monotonic `seq` per run for client-side ordering and gap detection
- [ ] Terminal event (`run.completed` or `run.failed`) always emitted in `finally`
- [ ] `stage.progress` events throttled to 250 ms minimum interval
- [ ] Token events batched to reduce SSE message count
- [ ] Heartbeat `event: heartbeat` sent every 15 seconds via `asyncio.create_task`
- [ ] Proper SSE format: `event: <type>\ndata: <json>\n\n`
- [ ] Client disconnect triggers cleanup (cancel background task, unsubscribe queue)
- [ ] Pipeline runs in background task; events published via `EventBus`
- [ ] Workflow nodes (`planner_node`, `validate_node`, `bump_refine`,
      `executor_node`) publish events through the `EventBus` port
- [ ] `Last-Event-ID` support for resuming after disconnect (best-effort: replay
      from in-memory buffer of last 50 events per run)
- [ ] SSE event mapper uses `graph.astream_events(input_data, version="v2")` to
      translate LangGraph events into the typed event contract
- [ ] Quality-gate and refinement events emitted explicitly by their nodes (not
      inferred from astream_events) with domain-specific payloads
- [ ] Tool events (`tool.started`, `tool.completed`) mapped from `on_tool_start` /
      `on_tool_end` in astream_events v2

---

### S10-002: Frontend SSE Hook + Pipeline State

**Description:** React hook for consuming SSE events from the plan generation
endpoint and a Zustand store for managing pipeline viewer state. The hook handles
connection lifecycle (open, error, reconnect, close), parses events, and dispatches
them to the store. The store drives the PipelineRunViewer component from Sprint 5.

**Files:**
- `frontend/hooks/use-pipeline-sse.ts` (new: SSE hook)
- `frontend/stores/pipeline-store.ts` (new: Zustand store)
- `frontend/types/pipeline-events.ts` (new: TypeScript types for SSE events)
- `frontend/components/pipeline/pipeline-viewer.tsx` (update: wire to store)

**Implementation details:**
- `usePipelineSSE(runId: string, options?: { enabled: boolean })` returns
  `{ status, currentStage, stages, events, error, retry }`.
- Uses the native `EventSource` API with `POST` polyfill (via `fetch` +
  `ReadableStream` since `EventSource` only supports GET; alternatively use
  `@microsoft/fetch-event-source` for POST SSE).
- Zustand store shape:
  ```typescript
  interface PipelineState {
    runId: string | null;
    status: "idle" | "connecting" | "streaming" | "complete" | "error";
    currentStage: RunStage | null;
    stages: Record<RunStage, StageState>;
    events: PipelineEvent[];
    error: string | null;
    score: number | null;
    exportsReady: ExportVariant[];
    lastSeq: number;  // Track last received seq for gap detection
    // Actions
    reset: () => void;
    pushEvent: (event: PipelineEvent) => void;
    setStage: (stage: RunStage, state: StageState) => void;
    setComplete: (data: CompleteEventData) => void;
    setError: (message: string) => void;
  }
  ```
- Auto-reconnect on connection drop: max 3 retries with exponential backoff
  (1s, 2s, 4s).
- Optimistic UI: when `stage_change` received, immediately mark next stage as
  "active" in the store before server confirms progress.
- Screen reader announcements: use `aria-live="polite"` region that receives
  stage change text (e.g., "Now running validation stage").

**Frontend Last-Event-ID reconnection:**
- The `usePipelineSSE` hook tracks `lastSeq` from the most recent event.
- On reconnect, pass `lastSeq` as `Last-Event-ID` header (via
  `@microsoft/fetch-event-source` headers option).
- The server replays buffered events with `seq > last_event_id` so the client
  does not miss events during brief disconnections.

**Risk (from Gemini architecture review): Zustand store race conditions.**
Hydrating a Zustand store from complex SSE events (tokens, status, graph
transitions) often leads to race conditions when multiple events arrive in rapid
succession and trigger parallel state updates.

**Mitigation:** Use a single reducer function that processes events sequentially.
All incoming SSE events are dispatched through one synchronous reducer
(`processEvent(state, event) => state`) that applies changes atomically. Never
perform parallel or concurrent state updates from separate event handlers. This
ensures event ordering is preserved and intermediate states are consistent.

**Acceptance Criteria:**
- [ ] `usePipelineSSE(runId)` hook connects to SSE endpoint on mount
- [ ] Zustand store holds full pipeline state (stages, currentStage, events, error,
      score, exportsReady)
- [ ] All SSE events processed through a single sequential reducer function
      (`processEvent`) -- no parallel state updates
- [ ] Auto-reconnect on connection drop (max 3 retries, exponential backoff
      1s/2s/4s)
- [ ] Optimistic UI updates (show stage as active before server progress events)
- [ ] Native `EventSource` API (or `@microsoft/fetch-event-source` for POST) with
      proper error handling
- [ ] Cleanup: `EventSource.close()` on component unmount or hook disable
- [ ] Screen reader announcements for stage changes via `aria-live` region
- [ ] TypeScript types for all SSE event payloads (discriminated union on
      `event.type`)
- [ ] Events array capped at 200 entries (FIFO) to prevent memory growth
- [ ] `lastSeq` tracked in store; passed as `Last-Event-ID` on reconnect

---

### S10-003: WebSocket for Tutor Chat

**Description:** WebSocket endpoint for real-time tutor chat with token-by-token
streaming from the LLM. The endpoint handles bidirectional messaging: the client
sends user messages, the server streams back LLM tokens as they are generated,
followed by a completion event with the full message. Connection state is managed
via the LangGraph checkpointer so sessions survive reconnects.

**Files:**
- `runtime/ailine_runtime/api/routers/tutors.py` (add `WS /sessions/{id}/ws`)
- `runtime/ailine_runtime/api/schemas/tutor_ws.py` (new: WebSocket message schemas)
- `runtime/ailine_runtime/app/services/tutor_service.py` (new or update: streaming
  chat turn that yields tokens)
- `frontend/hooks/use-tutor-ws.ts` (new: WebSocket hook)
- `frontend/stores/tutor-store.ts` (new: Zustand store for chat state)

**Implementation details:**
- `WS /tutors/sessions/{session_id}/ws` accepts WebSocket upgrade.
- Authentication: session ID validated against stored sessions; reject with
  `4403` close code if invalid.
- Client message format:
  ```json
  {"type": "message", "content": "O que sao fracoes?"}
  {"type": "ping"}
  ```
- Server message format:
  ```json
  {"type": "token", "content": "Fra"}
  {"type": "token", "content": "coes"}
  {"type": "typing", "active": true}
  {"type": "complete", "message": {"role": "assistant", "content": "...", "id": "msg_01..."}}
  {"type": "pong"}
  {"type": "error", "code": "llm_timeout", "message": "..."}
  ```
- LLM streaming: the tutor service yields tokens from the LLM stream
  (via `ChatLLM.stream()` if available, or `ChatLLM.chat()` with streaming
  callback); each token is sent as a `{"type": "token"}` WS message.
- Connection heartbeat: server sends `{"type": "pong"}` in response to client
  `{"type": "ping"}` every 30 seconds. If no ping received within 60 seconds,
  server closes connection.
- Session state: LangGraph checkpointer persists conversation state; on
  reconnect, the client receives a `{"type": "history", "messages": [...]}` event
  with the last 20 messages.
- Frontend hook `useTutorWS(sessionId)` returns
  `{ messages, isConnected, isTyping, send, reconnect }`.
- Zustand store manages message history, typing indicators, and connection state.

**Acceptance Criteria:**
- [ ] `WS /tutors/sessions/{session_id}/ws` accepts WebSocket upgrade
- [ ] Session ID validated; invalid sessions rejected with close code 4403
- [ ] Client sends `{"type": "message", "content": "..."}` for user messages
- [ ] Server streams `{"type": "token", "content": "..."}` for each LLM token
- [ ] Server sends `{"type": "complete", "message": {...}}` when LLM finishes
- [ ] Server sends `{"type": "typing", "active": true/false}` indicators
- [ ] `{"type": "error", "code": "...", "message": "..."}` on failures
- [ ] Ping/pong heartbeat every 30 seconds; server closes after 60s idle
- [ ] On reconnect, server sends `{"type": "history", "messages": [...]}` with
      last 20 messages from LangGraph checkpointer
- [ ] Frontend `useTutorWS(sessionId)` hook with auto-reconnect (max 5 retries)
- [ ] Zustand store for chat state (messages, isConnected, isTyping, error)
- [ ] Token streaming does not block the event loop (uses `async for` on LLM
      stream)
- [ ] Graceful shutdown: pending messages flushed before connection close

---

## Dependencies

- **Sprint 0** (Foundation & API Fixes): API routers and workflow must be
  functional.
- **Sprint 1** (Clean Architecture): EventBus port, InMemoryEventBus adapter, SSE
  utilities, shared config.
- **Sprint 5** (Frontend MVP): PipelineRunViewer component and Zustand setup.

---

## Decisions

- **ADR-006 confirmed:** SSE for pipeline (unidirectional, simple, proxy-friendly),
  WebSocket for tutor chat (bidirectional, low-latency token streaming).
- **POST SSE:** Standard `EventSource` only supports GET. We use
  `@microsoft/fetch-event-source` on the frontend or a custom `fetch` +
  `ReadableStream` parser to support POST bodies. On the backend, `sse-starlette`
  handles SSE framing regardless of HTTP method.
- **Event buffer:** Last 50 events per run kept in memory for `Last-Event-ID`
  resume. Not persisted to DB (acceptable for hackathon scope).
- **Token streaming:** LLM adapters must expose an async iterator interface for
  streaming. If the adapter does not support streaming, fall back to yielding the
  complete response as a single token event.
- **astream_events v2:** The SSE endpoint uses `graph.astream_events(version="v2")`
  to capture all LangGraph node/chain/model events and map them to the 14 typed
  SSE event types. Domain-specific events (quality, refinement) are emitted
  explicitly by their nodes rather than inferred from the stream.
- **Branch envelopes (ADR-023):** Parallel fan-out branches use `safe_branch()`
  wrappers so that a failure in one branch (e.g., RAG search timeout) does not
  prevent the other branch's results from reaching the Planner.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| SSE connections dropped by reverse proxies / load balancers | 15s heartbeat; client auto-reconnect with `Last-Event-ID` |
| WebSocket not supported behind some corporate proxies | Fallback to HTTP polling for tutor (deferred to post-hackathon) |
| LLM adapter does not support streaming | Fallback: yield complete response as single token event |
| Memory growth from event buffers | Cap at 50 events per run; purge on run completion |
| Frontend EventSource only supports GET | Use `@microsoft/fetch-event-source` for POST SSE support |
| One parallel branch fails, killing entire pipeline | `safe_branch()` envelope lets surviving branch proceed (ADR-023) |
| Progress event flood overwhelms client | 250ms throttle between `stage.progress` events |
| Client misses events during brief disconnect | `Last-Event-ID` + server replay from 50-event buffer |

---

## Technical Notes

### Expert Consultation Source

The LangGraph static fan-out pattern, SSE event mapper, and 14-event typed
contract were validated via GPT-5.2/Codex expert consultation (2026-02-11).
Patterns are confirmed compatible with LangGraph 1.0.x `astream_events(v2)` and
`sse-starlette 3.2.0`.

### Existing code to extend

- `runtime/ailine_runtime/api/streaming/sse.py` already has `format_sse_event()`
  and `heartbeat_generator()` -- extend with `SSEChannel` class and
  `merge_generators()` utility.
- `runtime/ailine_runtime/adapters/events/inmemory_bus.py` already implements
  `EventBus` protocol -- add `subscribe_queue(channel, queue)` method for the SSE
  endpoint to consume events via `asyncio.Queue`.
- `runtime/ailine_runtime/workflow/plan_workflow.py` workflow nodes need
  `EventBus` injected via `RunState` or container; each node publishes events
  at entry (stage_change), during execution (progress), and at exit (complete).
- `runtime/ailine_runtime/domain/entities/run.py` already has `RunEvent` and
  `PipelineRun` entities for event payloads.
- `runtime/ailine_runtime/domain/entities/plan.py` has `RunStage` enum
  (PLANNER, VALIDATE, REFINE, EXECUTOR, DONE, FAILED) used in SSE events.

### Operational parameters (from expert consultation)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Heartbeat interval | 15 seconds | Keeps SSE alive through proxies/LBs |
| Progress throttle | 250 ms min | Prevents client event flood |
| Event buffer size | 50 events/run | `Last-Event-ID` replay window |
| `seq` scope | Per run, monotonic | Client ordering + gap detection |
| Terminal guarantee | `finally` block | Client never hangs on missing terminal |
| Heartbeat mechanism | `asyncio.create_task` | Non-blocking, cancelled in `finally` |

### New dependency

- `sse-starlette==3.2.0` (PyPI) -- SSE response wrapper for Starlette/FastAPI.
- `@microsoft/fetch-event-source` (npm) -- POST-capable EventSource for frontend.
