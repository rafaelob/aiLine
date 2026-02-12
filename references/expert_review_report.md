# Expert Architecture Review Report -- AiLine Platform

**Date:** 2026-02-12
**Reviewers:** GPT-5.2 (backend/architecture), Gemini-3-Pro-Preview (frontend/accessibility/SSE/performance)
**Scope:** Full architecture review of hexagonal design, LangGraph pipeline, SSE system, DB schema, tenant safety, CI fakes, frontend accessibility, sign language, and performance.

---

## 1. Hexagonal Architecture (GPT-5.2)

### Correctly Implemented
- Domain isolation intent is clear -- ports as Protocols, adapters outside domain
- Adapters selected via Settings in Container.build(), consistent with Ports-and-Adapters
- Port protocols are well-defined (ChatLLM, Embeddings, VectorStore, etc.)

### Violations / Leaky Abstractions

**FINDING-01 (HIGH): Container fields typed as `Any` instead of port Protocols**
- File: `runtime/ailine_runtime/shared/container.py` lines 15-28
- All slots (llm, embeddings, vectorstore, event_bus, etc.) are `Any`
- Consequence: mypy/pyright cannot catch adapter-specific method calls from workflow code
- Fix: Type fields to port Protocols (import only port interfaces, not adapters)

**FINDING-02 (HIGH): Workflow bypasses Container injection, coupled to specific modules**
- File: `runtime/ailine_runtime/workflow/plan_workflow.py` lines 95-96
- `generate_draft_plan` from `planner_deepagents` and `finalize_plan_with_executor` from `executor_agent_sdk` are imported directly
- These are application services that may import vendor SDKs, not going through the ChatLLM port
- Fix: Route through port-based injection via Container, or at minimum ensure these modules only depend on ports

**FINDING-03 (MEDIUM): Repository/UoW ports are fully Any-typed**
- File: `runtime/ailine_runtime/domain/ports/db.py`
- `Repository.get()`, `list()`, `add()`, `update()`, `delete()` all use `Any`
- Cannot enforce tenant scoping or entity type contracts via types
- Fix: Consider generic Repository[T] pattern or entity-specific repo protocols

**FINDING-04 (MEDIUM): Tenant safety encoded as prompt instruction, not architectural boundary**
- File: `runtime/ailine_runtime/workflow/plan_workflow.py` lines 119-130
- RAG tenant scoping relies on prompt text telling the LLM to "pass teacher_id"
- Fix: Enforce tenant filtering in tool implementations and repositories, not in prompts

---

## 2. LangGraph Pipeline (GPT-5.2)

### Sound Design
- StateGraph topology matches ADRs: planner -> validate -> decision -> refine/execute
- Tiered quality gate (ADR-050) correctly implemented
- Refinement iteration cap respected via max_refinement_iters

### Issues

**FINDING-05 (HIGH): No terminal SSE event guarantee (run.completed / run.failed)**
- File: `runtime/ailine_runtime/workflow/plan_workflow.py`
- SYSTEM_DESIGN.md says "always emit run.completed or run.failed" but no central try/except/finally wrapper exists
- If any node throws, run terminates without emitting terminal events
- Frontend will hang waiting for completion
- Fix: Implement a run-level wrapper that guarantees terminal event emission

**FINDING-06 (MEDIUM): Routing logic duplicated in decision_node and should_execute**
- File: `runtime/ailine_runtime/workflow/plan_workflow.py` lines 204-229 and 256-271
- Same ADR-050 thresholds implemented twice -- SSE decision events could disagree with actual routing
- Fix: Extract into a single pure function used by both

**FINDING-07 (MEDIUM): No error handling inside nodes**
- validate_node and executor_node assume their callees never throw
- LangGraph exceptions terminate run abruptly without stage.failed events
- Fix: Wrap node bodies in try/except, emit stage.failed on error

**FINDING-08 (LOW): RunState TypedDict(total=False) is overly permissive**
- All fields optional, easy for nodes to return inconsistent partial state
- state["run_id"] in executor_node (line 243) will KeyError if not provided
- Fix: Define required vs produced fields, or validate at boundaries

**FINDING-09 (LOW): recursion_limit=25 defined but not verified as passed to compile()/invoke()**
- Constant defined at line 33 but not used in graph.compile() call at line 290
- Fix: Pass `recursion_limit=DEFAULT_RECURSION_LIMIT` to compile() or invoke() config

---

## 3. DI Container & Config (GPT-5.2)

**FINDING-10 (CRITICAL): vectorstore declared but never built**
- File: `runtime/ailine_runtime/shared/container.py` lines 19-21, 30-48
- Container has `vectorstore: Any = None` but build() never populates it
- Any code expecting RAG will get None and fail at runtime
- Fix: Add _build_vectorstore() function with FakeVectorStore fallback

**FINDING-11 (HIGH): Event bus always in-memory, ignores settings**
- File: `runtime/ailine_runtime/shared/container.py` lines 51-56
- SYSTEM_DESIGN.md lists Redis for pub/sub, but _build_event_bus() always returns InMemoryEventBus
- Fix: Select based on settings (in-memory for dev/test, Redis for prod)

**FINDING-12 (MEDIUM): No FakeEmbeddings fallback**
- File: `runtime/ailine_runtime/shared/container.py` lines 82-107
- LLM falls back to FakeChatLLM when no key, but embeddings returns None
- CI tests involving RAG/chunking/retrieval will fail nondeterministically
- Fix: Add FakeEmbeddings + FakeVectorStore for symmetry

**FINDING-13 (LOW): OpenRouter treated as OpenAI adapter without base_url differentiation**
- `_build_llm` uses same OpenAIChatLLM for both openai and openrouter providers
- May need different base_url/headers for OpenRouter
- Fix: Pass base_url parameter based on provider

---

## 4. DB Schema & Tenant Safety (GPT-5.2)

### Good
- Composite FK on lessons (ADR-053) is excellent
- Teacher-owned resources have teacher_id + indexes

### Gaps

**FINDING-14 (HIGH): Incomplete tenant anchoring across tables**
- `TutorSessionRow` references `tutor_agents.id` only, no teacher_id -- cross-tenant session possible
- `PipelineRunRow.lesson_id` points to lessons.id without composite (teacher_id, lesson_id) FK
- `ChunkRow` only references material_id, no teacher_id -- direct chunk queries bypass tenant scoping
- Fix: Apply ADR-053 composite FK pattern consistently to all user-addressable links

---

## 5. FakeLLM / CI Strategy (GPT-5.2)

### Good
- LLM fallback to FakeChatLLM, media fakes consistent

### Gaps

**FINDING-15 (MEDIUM): No FakeEmbeddings + FakeVectorStore**
- RAG pipeline untestable in CI without live API keys

**FINDING-16 (MEDIUM): FakeLLM needs scenario scripting**
- Need deterministic outputs per prompt/schema to test: refine loop thresholds, error branches, SmartRouter escalation
- Fix: Implement configurable response mapping in FakeChatLLM

**FINDING-17 (MEDIUM): Executor tool calling not faked**
- ADR-048 moved executor to direct Anthropic tool calling
- CI needs a tool dispatcher fake that records calls and returns fixed results
- Fix: Add FakeToolDispatcher for deterministic tool execution in tests

---

## 6. Frontend Accessibility (Gemini-3-Pro-Preview)

### Good
- 9 themes exceed standard WCAG AAA requirements
- Separation of UiPreferences from AccessibilityNeeds is excellent domain modeling
- data-theme attribute switching is standard and performant for CSS

### Issues

**FINDING-18 (HIGH): Recharts/Canvas won't re-render on CSS variable change**
- Recharts renders to SVG/Canvas with JS-side color hex props
- Changing data-theme on body won't automatically repaint Recharts components
- Fix: Create ThemeContext that observes data-theme changes (MutationObserver) and forces re-render of chart components with derived color values

**FINDING-19 (MEDIUM): reduce_motion should default from system preference, not static boolean**
- `profiles.py` UiPreferences.reduce_motion defaults to True
- Should check `window.matchMedia('(prefers-reduced-motion: reduce)')` on hydration
- Fix: Initialize in Zustand from media query, use stored profile as override only

**FINDING-20 (LOW): "Low Distraction" theme should remove DOM elements, not just CSS-hide**
- Truly reducing cognitive load requires removing decorative DOM elements, not just `display:none`
- Fix: Use React Activity component or conditional rendering for decorative elements in low-distraction mode

---

## 7. SSE Event System (Gemini-3-Pro-Preview)

### Good
- 14 events are well-defined and appropriate granularity
- Envelope with seq number enables ordering and gap detection

### Issues

**FINDING-21 (CRITICAL): No SSE resume/reconnection strategy**
- SSEEventEmitter resets seq to 0 on instantiation
- On client reconnect, server may start new run or reset sequence
- @microsoft/fetch-event-source sends Last-Event-ID but backend doesn't handle it
- Fix: Store last N events per run_id in Redis with TTL. On reconnect with Last-Event-ID, replay missed events before streaming live ones

**FINDING-22 (MEDIUM): Emitter not safe for parallel LangGraph branches**
- Thread-safety claim is "within a single asyncio task"
- SYSTEM_DESIGN.md describes parallel fan-out (RAG + Profile Analyzer)
- Fix: Each parallel node should emit to centralized Queue, or orchestrator emits after fan-in

---

## 8. Performance (Gemini-3-Pro-Preview)

**FINDING-23 (HIGH): DB pool size of 5 is dangerously small**
- 30 students logging in simultaneously will exhaust pool immediately (TimeoutError)
- Even a teacher generating 10 parallel plans will saturate the pool
- Fix: Increase pool_size to at least 20, or use PgBouncer in production
- Note: This contradicts ADR-052 which set pool_size=5 -- ADR needs revision for production workloads

**FINDING-24 (HIGH): TF.js + MediaPipe must run in Web Worker**
- WASM binaries are several MBs, will freeze main thread on load
- Violates WCAG "no timing" guidelines (laggy interactions)
- Fix: Create sign-recognizer.worker.ts, use OffscreenCanvas or ImageBitmap for frame transfer

**FINDING-25 (MEDIUM): SSE buffering needs reverse proxy config**
- compress:false in Next.js is correct, but Nginx/ALB may still buffer
- Fix: Ensure `proxy_buffering off;` on SSE endpoint path in reverse proxy config

---

## 9. Sign Language (Gemini-3-Pro-Preview)

### Sound for MVP
- MediaPipe + MLP for 3-4 navigation gestures is validated (97.4% accuracy, ICANN 2025)
- ADR-026 correctly scopes to navigation only

### Concerns

**FINDING-26 (MEDIUM): VLibras widget UX issues**
- 3D avatar creates focus traps and overlay issues
- Many deaf users prefer video of human signers
- Fix: Ensure VLibras container has aria-hidden="true" when inactive, doesn't block skip links

**FINDING-27 (LOW): No natural Libras sentence translation via MLP**
- MLP is limited to gesture classification, not sentence-level translation
- Correctly deferred to post-MVP (SPOTER transformer)
- No action needed for MVP

---

## Summary: Priority-Ordered Action Items

### P0 -- Critical (fix before next sprint)
| # | Finding | Impact |
|---|---------|--------|
| FINDING-10 | vectorstore never built in Container | RAG pipeline broken at runtime |
| FINDING-21 | No SSE resume strategy | Frontend hangs on reconnect |
| FINDING-05 | No terminal SSE event guarantee | Frontend hangs, audit trail incomplete |

### P1 -- High (fix during current sprint)
| # | Finding | Impact |
|---|---------|--------|
| FINDING-01 | Container fields Any-typed | No compile-time port enforcement |
| FINDING-02 | Workflow bypasses Container injection | Hexagonal boundary violated |
| FINDING-11 | Event bus always in-memory | Prod pub/sub broken |
| FINDING-14 | Incomplete tenant anchoring | Cross-tenant data access possible |
| FINDING-18 | Recharts ignores theme changes | Charts render wrong colors |
| FINDING-23 | DB pool size=5 too small | Pool exhaustion under load |
| FINDING-24 | TF.js/MediaPipe on main thread | UI freezes, WCAG violation |

### P2 -- Medium (fix before MVP)
| # | Finding | Impact |
|---|---------|--------|
| FINDING-03 | Repository Any-typed | Weak type safety |
| FINDING-04 | Tenant safety in prompts | Soft control, not architectural |
| FINDING-06 | Routing logic duplicated | Drift risk |
| FINDING-07 | No error handling in nodes | Silent failures |
| FINDING-12 | No FakeEmbeddings | RAG untestable in CI |
| FINDING-15 | No FakeVectorStore | Same |
| FINDING-16 | FakeLLM needs scenarios | Cannot test pipeline branches |
| FINDING-17 | Executor tools not faked | Cannot test tool execution |
| FINDING-19 | reduce_motion wrong default | Ignores system preference |
| FINDING-22 | Emitter unsafe for parallel | Seq collision risk |
| FINDING-25 | SSE proxy buffering | Events delayed |
| FINDING-26 | VLibras a11y issues | Focus traps |

### P3 -- Low (backlog)
| # | Finding | Impact |
|---|---------|--------|
| FINDING-08 | RunState too permissive | Occasional KeyError |
| FINDING-09 | recursion_limit not passed | Default may differ |
| FINDING-13 | OpenRouter base_url | Works now, may break |
| FINDING-20 | Low-distraction needs DOM removal | Cognitive load not fully reduced |
| FINDING-27 | No Libras sentence translation | Correctly deferred |

---

## Suggested ADRs to Create

1. **ADR-054: SSE event replay via Redis** -- Store last N events per run_id for reconnection
2. **ADR-055: Run-level wrapper for terminal SSE guarantee** -- try/finally emitting run.completed/failed
3. **ADR-056: DB pool sizing for production** -- Revise ADR-052 pool_size for multi-tenant classroom loads
4. **ADR-057: Web Worker for sign language ML** -- Offload TF.js/MediaPipe from main thread
5. **ADR-058: ThemeContext for JS-rendered components** -- MutationObserver bridge for Recharts/Canvas

---

## Open Questions for Team Lead

1. Where is `recursion_limit=25` actually enforced at runtime? (Defined but not passed to compile/invoke)
2. Do `generate_draft_plan` / `finalize_plan_with_executor` import vendor SDKs directly or go through ChatLLM port?
3. Are repositories already requiring teacher_id parameters everywhere, or is that aspirational?
4. Should ADR-052 pool_size=5 be revised upward for classroom-scale loads?

---

**Consultation Method:**
- GPT-5.2 via `mcp__zen__chat` (model: gpt-5.2, thinking: high) -- backend/architecture review
- Gemini-3-Pro-Preview via `mcp__zen__chat` (model: gemini-3-pro-preview, thinking: high) -- frontend/accessibility review
- Temperature: 1.0 for both (per CLAUDE.md policy)
- codex CLI via clink: timed out (700s limit) -- fallback to direct chat used
