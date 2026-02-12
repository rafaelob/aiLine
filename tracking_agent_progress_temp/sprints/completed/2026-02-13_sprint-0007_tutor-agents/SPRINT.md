# Sprint 0007 — Tutor Agents

**Status:** planned | **Date:** 2026-02-13
**Goal:** Complete Socratic tutor system with RAG integration, accessibility
playbooks, structured multi-turn chat, LangGraph workflow with Postgres
checkpointer for memory, and accessible chat frontend.

---

## Architecture Decisions (from Gemini-3-Pro-Preview + Codex consultation)

- **Memory management**: LangGraph's built-in Postgres checkpointer for session
  state persistence. No custom summarization needed for hackathon scope --
  sliding window of last 20 messages with full checkpoint.
- **RAG integration**: Retrieve context on first message and when student asks
  about specific material. Heuristic: trigger RAG when message contains question
  keywords or references material.
- **Session isolation**: Each tutor session has unique `thread_id` in LangGraph,
  mapped to `tutor_sessions.id` in DB. Checkpointer stores state per thread.
- **Multi-LLM**: Tutor uses Claude Opus 4.6 by default (best for Socratic
  pedagogy), with Gemini 2.5 Flash for quick follow-ups.
- **Accessibility playbooks**: System prompt is dynamically composed based on
  the `LearnerProfile.needs` field. Each need maps to a playbook section
  injected into the prompt (TEA, TDAH, dyslexia, visual impairment, etc.).
- **Structured output**: LLM responds with `TutorTurnOutput` schema
  (answer_markdown, step_by_step, check_for_understanding, options_to_respond,
  self_regulation_prompt, citations, teacher_note, flags). This maps directly
  to the existing domain entity in `domain/entities/tutor.py`.
- **WebSocket for real-time chat**: SSE is used for plan pipeline (one-way
  stream), but tutor chat requires bidirectional communication, so WebSocket
  is the right transport (ADR-006). WebSocket is optional for Sprint 7 --
  HTTP POST fallback is the primary path; full streaming deferred to Sprint 10.
- **Tutor workflow topology**: StateGraph with adaptive conditional edges --
  `understand_intent` classifies the student's state (confused, progressing,
  off-topic) and routes accordingly: confused -> add scaffolding node;
  progressing -> advance to next concept; off-topic -> gentle redirect.
- **Embedding task type**: RAG queries MUST use `task_type=RETRIEVAL_QUERY`
  (not `RETRIEVAL_DOCUMENT`) when calling GeminiEmbeddingsAdapter from Sprint 3.
  Document embeddings at ingestion time use `RETRIEVAL_DOCUMENT`.
- **Hint progressive reveal**: Hints stored as ordered list in `TutorTurnOutput`;
  frontend reveals one at a time on student request, not all at once.

---

## Verified Library Versions

| Library | Version | Source |
|---------|---------|--------|
| langgraph | 0.3.x | pypi.org/project/langgraph |
| langgraph-checkpoint-postgres | 2.0.x | pypi.org/project/langgraph-checkpoint-postgres |
| asyncpg | 0.31.0 | pypi.org (already in project) |
| anthropic | latest | pypi.org/project/anthropic |
| google-genai | latest | pypi.org/project/google-genai |

---

## Stories

### S7-001: Tutor LangGraph Workflow

**Description:** Implement tutor chat as a LangGraph StateGraph with adaptive
routing, RAG retrieval, accessibility-aware system prompt, comprehension
checking, and Postgres checkpointer. The workflow defines the core
turn-by-turn logic with conditional branching based on student comprehension.

**Files:**
- `runtime/ailine_runtime/workflow/tutor_workflow.py` (new -- StateGraph definition)
- `runtime/ailine_runtime/workflow/__init__.py` (update -- re-export)

**Acceptance Criteria:**
- [ ] StateGraph with nodes: `understand_intent` -> `search_materials` ->
      `generate_response` -> `check_comprehension`
- [ ] `understand_intent` node: classifies student message into intent
      categories (asking_question, confused, progressing, off_topic,
      greeting, emotional) and determines if RAG retrieval is needed
- [ ] Conditional edges after `check_comprehension`:
      - Student confused -> route to scaffolding sub-path (simplify, add
        example, break into smaller steps)
      - Student progressing -> advance to next concept
      - Student off-topic -> gentle redirect back to subject
- [ ] `search_materials` node: embeds question via `EmbeddingPort` with
      `task_type=RETRIEVAL_QUERY` -> vector search via `VectorStorePort`
      -> injects top-5 chunks into context with scores and source citations
- [ ] `generate_response` node: LLM call with Socratic system prompt +
      accessibility playbook via `ChatLLM` port; system prompt includes
      "When using materials, always cite the source"
- [ ] `check_comprehension` node: analyzes student responses for
      understanding signals and decides next pedagogical action
- [ ] Postgres checkpointer (`AsyncPostgresSaver` from
      `langgraph-checkpoint-postgres`) wired at graph compile time;
      requires `.setup()` on first use (called during app startup)
- [ ] Thread isolation via `session_id` (maps to `tutor_sessions.id`)
- [ ] Sliding window: last 20 messages from checkpoint history
- [ ] All Pydantic objects must use `.model_dump()` before placing in
      graph state to avoid serialization errors with AsyncPostgresSaver
- [ ] Graph state defined as TypedDict (`TutorGraphState`) with fields:
      `session_id`, `user_message`, `rag_context`, `rag_sources`,
      `system_prompt`, `messages`, `turn_output`, `needs_rag`,
      `student_intent`, `comprehension_level`, `agent_spec`

**Tutor System Prompt Pattern:**

```python
SOCRATIC_SYSTEM = """You are a Socratic tutor for {subject}. Your student is {learner_name}.

TEACHING METHOD:
- Never give answers directly. Ask guiding questions.
- Start by diagnosing current understanding.
- Build on what the student already knows.
- Use concrete examples before abstract concepts.
- Celebrate progress, normalize mistakes.

ACCESSIBILITY:
{accessibility_playbook}

MATERIALS CONTEXT:
{rag_context}

CITATION RULE:
When using materials, always cite the source. Include document title and
section in your citations field. If no relevant material was found, say so
honestly rather than fabricating references.

RULES:
- Keep responses under 150 words unless explaining a complex concept.
- Use simple, clear language (grade-appropriate).
- After 3 wrong attempts, provide a hint with the first step.
- If student is frustrated, acknowledge emotions and simplify.

OUTPUT FORMAT:
Respond as JSON matching TutorTurnOutput schema:
- answer_markdown: Your main response in Markdown.
- step_by_step: List of steps if explaining a process.
- check_for_understanding: 1-2 follow-up questions.
- options_to_respond: 2-3 suggested student replies.
- self_regulation_prompt: Optional prompt for breaks/breathing (if student needs it).
- citations: Material references used (if any), format: "Document Title, Section X".
"""
```

**Graph wiring pattern (updated with conditional comprehension routing):**

```python
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

class TutorGraphState(TypedDict, total=False):
    session_id: str
    user_message: str
    rag_context: str
    rag_sources: list[dict[str, Any]]  # [{title, section, score}]
    system_prompt: str
    messages: list[dict[str, str]]
    turn_output: dict[str, Any]
    needs_rag: bool
    student_intent: str  # asking_question | confused | progressing | off_topic | greeting | emotional
    comprehension_level: str  # confused | partial | solid
    agent_spec: dict[str, Any]

def route_after_comprehension(state: TutorGraphState) -> str:
    """Conditional edge: adapt next action based on student comprehension."""
    level = state.get("comprehension_level", "solid")
    if level == "confused":
        return "add_scaffolding"
    elif level == "partial":
        return "generate_response"  # re-explain with different angle
    return END  # solid -- advance naturally on next turn

def build_tutor_workflow(
    container: Container,
    checkpointer_conninfo: str,
) -> CompiledStateGraph:
    graph = StateGraph(TutorGraphState)
    graph.add_node("understand_intent", understand_intent_node)
    graph.add_node("search_materials", search_materials_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("check_comprehension", check_comprehension_node)
    graph.add_node("add_scaffolding", add_scaffolding_node)

    graph.set_entry_point("understand_intent")
    graph.add_conditional_edges("understand_intent", should_search, {
        True: "search_materials",
        False: "generate_response",
    })
    graph.add_edge("search_materials", "generate_response")
    graph.add_edge("generate_response", "check_comprehension")
    graph.add_conditional_edges("check_comprehension", route_after_comprehension, {
        "add_scaffolding": "add_scaffolding",
        "generate_response": "generate_response",
        END: END,
    })
    graph.add_edge("add_scaffolding", END)

    checkpointer = AsyncPostgresSaver.from_conninfo(checkpointer_conninfo)
    # IMPORTANT: call await checkpointer.setup() during app startup
    return graph.compile(checkpointer=checkpointer)
```

---

### S7-002: RAG-Enhanced Tutor Context

**Description:** Integrate vector search into the tutor workflow for
material-aware responses. Uses GeminiEmbeddingsAdapter from Sprint 3 with
correct task_type differentiation. On session start, pre-load subject context
from the teacher's materials. On each student question, embed the question
and search for relevant chunks to inject into the LLM context window.

**Files:**
- `runtime/ailine_runtime/app/services/tutor_rag.py` (new -- RAG retrieval service)

**Acceptance Criteria:**
- [ ] On session start: retrieve top-5 chunks from teacher's materials for the
      subject (via `VectorStorePort`)
- [ ] On student question: embed question via `EmbeddingPort` with
      `task_type=RETRIEVAL_QUERY` (NOT `RETRIEVAL_DOCUMENT` -- critical
      distinction for Gemini embeddings) -> search -> inject relevant chunks
      (max 5, deduplicated against session context)
- [ ] Return top-5 chunks with relevance scores AND source citations
      (document title, page/section reference, snippet of cited content)
- [ ] Context window management: if injected context exceeds 4000 tokens,
      drop oldest chunks (FIFO)
- [ ] Filtering: `teacher_id` + `subject` filter on vector search query
      (uses `TutorMaterialsScope.material_ids` when specified)
- [ ] Returns `TutorRAGResult` with fields: `chunks: list[str]`,
      `sources: list[TutorRAGSource]`, `relevance_scores: list[float]`
- [ ] `TutorRAGSource` dataclass: `title: str`, `section: str`,
      `page: int | None`, `snippet: str`
- [ ] Graceful degradation: if vector store is empty or unavailable, return
      empty context (tutor still works, just without material grounding)
- [ ] Tutor system prompt enforces: "When using materials, always cite the
      source" -- citations appear in `TutorTurnOutput.citations`

**Memory Strategy (from research synthesis):**
- **Summary + Buffer hybrid:** Keep last 6 raw messages as buffer for
  immediate conversational context. Maintain a running summary of older
  messages to preserve long-term session coherence without unbounded growth.
- **Intent-driven RAG:** RAG retrieval is triggered by an intent classifier,
  NOT on every turn. The classifier detects when the student is asking about
  specific material, requesting examples, or referencing content -- avoiding
  unnecessary retrieval overhead on conversational turns (greetings, emotional
  check-ins, follow-up confirmations).
- **Mandatory citations:** Every tutor response that uses RAG-retrieved
  content must include citations. This is critical for teacher trust
  (teachers can verify what material the tutor referenced) and educational
  value (students learn to trace claims to sources).

**RAG retrieval pattern (updated with task_type and source citations):**

```python
@dataclass
class TutorRAGSource:
    title: str
    section: str
    page: int | None
    snippet: str

@dataclass
class TutorRAGResult:
    chunks: list[str]
    sources: list[TutorRAGSource]
    relevance_scores: list[float]

class TutorRAGService:
    def __init__(self, embeddings: Embeddings, vectorstore: VectorStore):
        self._embeddings = embeddings
        self._vectorstore = vectorstore

    async def retrieve_for_question(
        self,
        question: str,
        scope: TutorMaterialsScope,
        *,
        top_k: int = 5,
    ) -> TutorRAGResult:
        # CRITICAL: use RETRIEVAL_QUERY for search queries, not RETRIEVAL_DOCUMENT
        embedding = await self._embeddings.embed(
            question,
            task_type="RETRIEVAL_QUERY",
        )
        results = await self._vectorstore.search(
            embedding,
            top_k=top_k,
            filter={"teacher_id": scope.teacher_id, "subject": scope.subject},
        )
        return TutorRAGResult(
            chunks=[r.text for r in results],
            sources=[
                TutorRAGSource(
                    title=r.metadata.get("title", ""),
                    section=r.metadata.get("section", ""),
                    page=r.metadata.get("page"),
                    snippet=r.text[:200],
                )
                for r in results
            ],
            relevance_scores=[r.score for r in results],
        )
```

---

### S7-003: Tutor Chat API Endpoints

**Description:** REST API for tutor session management with HTTP POST as the
primary chat path. WebSocket streaming is deferred to Sprint 10 as optional
enhancement. Updates the existing `tutors.py` router with new session-centric
endpoints that work with the LangGraph tutor workflow.

**Files:**
- `runtime/ailine_runtime/api/routers/tutors.py` (update -- new session/message endpoints)

**Acceptance Criteria:**
- [ ] `POST /tutors/sessions` -- Create new session
      - Request: `{ teacher_id, learner_name, subject, grade, standard,
        style, accessibility_needs, material_ids }`
      - Response: `{ session_id, tutor_id, created_at }`
      - Creates `tutor_sessions` DB row + LangGraph thread
- [ ] `GET /tutors/sessions/{id}` -- Get session with message history
      - Response: `{ session_id, tutor_id, learner_name, messages[], created_at }`
      - Messages loaded from LangGraph checkpoint
- [ ] AsyncPostgresSaver checkpointer requires `.setup()` on first use
      (call during app startup or first session creation). All state values
      must be JSON-serializable -- use `.model_dump()` on Pydantic objects
      before storing in graph state to avoid serialization errors.
- [ ] `POST /tutors/sessions/{id}/messages` -- Send message, get tutor response
      - Request: `{ content, content_type: "text" | "voice_transcript" }`
      - Response: `TutorTurnOutput` JSON (structured with all sections)
      - Invokes LangGraph workflow with `session_id` as thread_id
- [ ] Response includes: `tutor_message`, `suggested_followups`,
      `confidence_score` (derived from RAG relevance)
- [ ] Input validation: max 2000 chars per message, rate limit 30 msg/min
      per session

**WebSocket (Sprint 10 -- optional enhancement):**
- [ ] `WS ws://localhost:8000/ws/tutors/{tutor_id}/chat` -- real-time streaming
      - Client sends: `{ type: "message", content: "..." }`
      - Server streams: `{ type: "token", data: "..." }` during generation,
        then `{ type: "turn_complete", data: TutorTurnOutput }`
      - Token-by-token streaming for tutor responses
      - Fallback to HTTP POST if WebSocket unavailable
      - Deferred to Sprint 10 to keep Sprint 7 scope focused

**HTTP POST handler pattern (Sprint 7 primary path):**

```python
class TutorMessageIn(BaseModel):
    content: str = Field(..., max_length=2000)
    content_type: Literal["text", "voice_transcript"] = "text"

@router.post("/sessions/{session_id}/messages")
async def tutor_send_message(session_id: str, body: TutorMessageIn):
    """Send message and get structured tutor response via LangGraph."""
    result = await workflow.ainvoke(
        {"user_message": body.content},
        config={"configurable": {"thread_id": session_id}},
    )
    return result["turn_output"]
```

**WebSocket handler pattern (Sprint 10):**

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/sessions/{session_id}/ws")
async def tutor_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                async for event in workflow.astream(
                    {"user_message": data["content"]},
                    config={"configurable": {"thread_id": session_id}},
                ):
                    await websocket.send_json({
                        "type": "token",
                        "data": event,
                    })
    except WebSocketDisconnect:
        pass
```

---

### S7-004: Tutor Chat Frontend

**Description:** Accessible chat UI with structured response rendering,
streaming indicators, input method selection, and accessibility adaptations.
The chat panel is the primary student-facing interface for interacting with
the Socratic tutor agent.

**Files:**
- `frontend/components/tutor/chat-panel.tsx` (new -- main chat container)
- `frontend/components/tutor/message-bubble.tsx` (new -- individual message)
- `frontend/components/tutor/structured-response.tsx` (new -- collapsible sections renderer)
- `frontend/components/tutor/input-bar.tsx` (new -- text/voice/sign input selector)
- `frontend/hooks/use-tutor-chat.ts` (new -- HTTP chat hook, WS hook deferred)

**Acceptance Criteria:**

**Message Layout:**
- [ ] Message bubbles: student messages right-aligned (blue), tutor messages
      left-aligned (gray) -- clear visual distinction
- [ ] Tutor avatar with persona indicator (style badge: Socratic/Coach/Direct)
- [ ] Message timestamps in user's locale (via `next-intl`)
- [ ] Auto-scroll to latest message (with "scroll to bottom" button when user
      scrolls up)

**Structured Response Rendering (TutorTurnOutput sections):**
- [ ] **Main response** (`answer_markdown`): rendered as Markdown with math
      support via KaTeX for formulas like `$x^2 + 3x = 0$`
- [ ] **Step-by-step section** (`step_by_step`): collapsible accordion;
      collapsed by default, expands on click/tap; numbered steps with optional
      sub-steps
- [ ] **Comprehension check** (`check_for_understanding` + `options_to_respond`):
      rendered as multiple-choice options the student can click to respond
- [ ] **Hint system**: progressive reveal -- first hint shown on student
      request, second hint after wrong answer, full explanation after third
      attempt. Hints revealed one at a time, not all at once.
- [ ] **Material citations** (`citations`): expandable source cards showing
      document title, page/section reference, and a snippet of the cited
      content
- [ ] Each section rendered as collapsible in chat UI (expand/collapse toggle)

**Typing and Streaming:**
- [ ] Typing indicator with animated dots during response generation
      (respects `prefers-reduced-motion`)

**Input Methods:**
- [ ] Input method selector bar: `[Text] [Voice] [Sign Language]` toggle
- [ ] Text: Enter to send, Shift+Enter for newline
- [ ] Voice input button (triggers Whisper STT -- Sprint 9 integration point)
- [ ] Sign Language input (triggers MediaPipe -- Sprint 8 integration point)

**VLibras Integration:**
- [ ] "Show in Libras" button per tutor message -- triggers VLibras
      translation of the tutor response (integration point for Sprint 8)

**Accessibility:**
- [ ] "Read aloud" button on tutor messages (triggers TTS -- Sprint 9
      integration point)
- [ ] ARIA live regions for new messages (`role="log"`,
      `aria-live="polite"`)
- [ ] Keyboard navigation: Enter to send, Shift+Enter for newline
- [ ] Empty state with welcome message and suggested first questions
- [ ] Touch targets 48px+ on all interactive elements

**Chat hook pattern (HTTP POST for Sprint 7):**

```typescript
export function useTutorChat(sessionId: string) {
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const send = async (content: string) => {
    setMessages((prev) => [
      ...prev,
      { role: "user", content, createdAt: new Date() },
    ]);
    setIsLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/tutors/sessions/${sessionId}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content, content_type: "text" }),
        },
      );
      const turnOutput: TutorTurnOutput = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: turnOutput.answer_markdown,
          structured: turnOutput,
          createdAt: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, send };
}
```

**WebSocket hook pattern (Sprint 10 -- deferred):**

```typescript
export function useTutorWs(sessionId: string) {
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/tutors/sessions/${sessionId}/ws`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "token") {
        setIsStreaming(true);
        // Append token to current assistant message
      } else if (data.type === "turn_complete") {
        setIsStreaming(false);
        // Replace streaming message with final TutorTurnOutput
      }
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [sessionId]);

  const send = (content: string) => {
    wsRef.current?.send(JSON.stringify({ type: "message", content }));
    setMessages((prev) => [...prev, { role: "user", content, createdAt: new Date() }]);
  };

  return { messages, isStreaming, send };
}
```

---

### S7-005: Tutor Accessibility Playbooks UI

**Description:** In-chat accessibility adaptations based on learner profile.
These are visual and behavioral modifications to the chat panel that activate
automatically when the learner's `LearnerProfile.needs` includes specific
accessibility needs. Updated with detailed per-persona UX behaviors.

**Files:**
- `frontend/components/tutor/a11y-adaptations.tsx` (new -- adaptation layer)
- `frontend/lib/tutor/playbooks.ts` (new -- playbook definitions)

**Acceptance Criteria:**

**TEA (Autism Spectrum):**
- [ ] Predictable layout with no surprises -- tutor always follows the same
      visual structure and response pattern in every turn
- [ ] Visual schedule of conversation flow -- sidebar or header strip showing
      "Greeting -> Question -> Explanation -> Practice -> Check" so the
      student knows what comes next
- [ ] Clear turn-taking indicators -- explicit "Your turn" / "Tutor is
      thinking" labels, not just a typing animation
- [ ] Step-by-step breakdown in numbered list format
- [ ] Minimal use of idioms or figurative language (enforced in system prompt)
- [ ] Visual timer for conversation duration

**TDAH (ADHD):**
- [ ] Short messages: max 80 words per bubble (enforced via playbook config)
- [ ] Chunked steps: each step is a separate bubble or clearly separated
      block within the bubble
- [ ] Progress indicator: visual progress bar or step counter showing how
      far through the current topic ("Step 2 of 5")
- [ ] Check-in prompts every 5 messages ("Still with me?")
- [ ] Timer for focus sessions: optional Pomodoro-style timer (configurable
      duration, default 15 min) with gentle break reminders
- [ ] Movement break suggestions every 10 minutes
- [ ] Key points highlighted with bold

**Dyslexia:**
- [ ] Atkinson Hyperlegible font in chat (primary), OpenDyslexic as option
- [ ] Larger text: 20px minimum
- [ ] Increased line spacing: 1.8
- [ ] Simpler vocabulary (enforced in system prompt)
- [ ] Read-aloud auto-trigger on tutor messages
- [ ] Color-coded sections (step-by-step in one color, comprehension check
      in another) for visual differentiation

**Low Vision / Visual Impairment:**
- [ ] Large text in bubbles: minimum 24px font size for all message text
- [ ] High contrast: forced high-contrast mode with WCAG AAA contrast ratios
- [ ] TTS button per message: prominently placed "Read aloud" button on every
      tutor message, larger than standard touch target (56px+)
- [ ] Screen reader optimized: all decorative elements marked `aria-hidden`

**Hearing Impairment:**
- [ ] Text-only mode as default (no audio-dependent features)
- [ ] Visual notifications for new messages (flash border instead of sound)
- [ ] VLibras "Show in Libras" button per tutor message (Sprint 8 integration)

**General:**
- [ ] Adaptation indicator badge on chat panel header showing active
      adaptations (e.g., "TEA + TDAH adaptations active")
- [ ] Teacher can configure adaptations per student in agent builder (S7-006)
- [ ] Adaptations composable: multiple needs stack without conflict
      (e.g., TEA + dyslexia = numbered lists + larger text + read-aloud);
      conflict resolution: "most accommodating wins" (largest font, most
      spacing, etc.)

**Playbook definition pattern (updated with Atkinson font + color coding):**

```typescript
interface AccessibilityPlaybook {
  id: string;
  label: string;
  fontSizeMin: number;
  maxWordsPerBubble: number | null;
  fontFamily: string | null;
  lineHeight: number;
  autoReadAloud: boolean;
  showVisualTimer: boolean;
  showConversationSchedule: boolean;  // TEA: visual flow indicator
  showProgressIndicator: boolean;     // TDAH: step counter
  checkInInterval: number | null;     // messages between check-ins
  breakInterval: number | null;       // minutes between break suggestions
  highContrast: boolean;
  colorCodedSections: boolean;        // Dyslexia: color differentiation
  showLibrasButton: boolean;          // Hearing: VLibras per message
  visualNotifications: boolean;       // Hearing: flash instead of sound
}

const PLAYBOOKS: Record<string, AccessibilityPlaybook> = {
  tea: {
    id: "tea",
    label: "TEA",
    fontSizeMin: 18,
    maxWordsPerBubble: null,
    fontFamily: null,
    lineHeight: 1.6,
    autoReadAloud: false,
    showVisualTimer: true,
    showConversationSchedule: true,
    showProgressIndicator: false,
    checkInInterval: null,
    breakInterval: null,
    highContrast: false,
    colorCodedSections: false,
    showLibrasButton: false,
    visualNotifications: false,
  },
  tdah: {
    id: "tdah",
    label: "TDAH",
    fontSizeMin: 18,
    maxWordsPerBubble: 80,
    fontFamily: null,
    lineHeight: 1.5,
    autoReadAloud: false,
    showVisualTimer: false,
    showConversationSchedule: false,
    showProgressIndicator: true,
    checkInInterval: 5,
    breakInterval: 10,
    highContrast: false,
    colorCodedSections: false,
    showLibrasButton: false,
    visualNotifications: false,
  },
  dyslexia: {
    id: "dyslexia",
    label: "Dislexia",
    fontSizeMin: 20,
    maxWordsPerBubble: null,
    fontFamily: "'Atkinson Hyperlegible', 'OpenDyslexic', sans-serif",
    lineHeight: 1.8,
    autoReadAloud: true,
    showVisualTimer: false,
    showConversationSchedule: false,
    showProgressIndicator: false,
    checkInInterval: null,
    breakInterval: null,
    highContrast: false,
    colorCodedSections: true,
    showLibrasButton: false,
    visualNotifications: false,
  },
  low_vision: {
    id: "low_vision",
    label: "Baixa Visao",
    fontSizeMin: 24,
    maxWordsPerBubble: null,
    fontFamily: null,
    lineHeight: 1.8,
    autoReadAloud: false,
    showVisualTimer: false,
    showConversationSchedule: false,
    showProgressIndicator: false,
    checkInInterval: null,
    breakInterval: null,
    highContrast: true,
    colorCodedSections: false,
    showLibrasButton: false,
    visualNotifications: false,
  },
  hearing: {
    id: "hearing",
    label: "Deficiencia Auditiva",
    fontSizeMin: 18,
    maxWordsPerBubble: null,
    fontFamily: null,
    lineHeight: 1.6,
    autoReadAloud: false,
    showVisualTimer: false,
    showConversationSchedule: false,
    showProgressIndicator: false,
    checkInInterval: null,
    breakInterval: null,
    highContrast: false,
    colorCodedSections: false,
    showLibrasButton: true,
    visualNotifications: true,
  },
};
```

---

### S7-006: Tutor Agent Builder

**Description:** UI for teachers to configure tutor agents per student or
group. The builder produces a `TutorAgentSpec` that is persisted as JSONB in
the `tutor_sessions.agent_spec` column and used at runtime to drive the
LangGraph tutor workflow.

**Files:**
- `frontend/components/tutor/agent-builder.tsx` (new -- builder form)
- `frontend/components/tutor/agent-builder-preview.tsx` (new -- prompt preview)

**Acceptance Criteria:**
- [ ] Form fields: student name, subject (dropdown), grade (dropdown),
      curriculum standard (BNCC/CCSS/NGSS)
- [ ] Accessibility needs: checkbox group (TEA, TDAH, dyslexia, visual
      impairment, hearing impairment, motor impairment, learning difficulty)
- [ ] Material selection: multi-select of teacher's uploaded materials to
      include in RAG scope (fetched via `GET /materials?teacher_id=...`)
- [ ] Personality slider: formal (0) <-> friendly (1), mapped to `tone`
      field in `TutorAgentSpec`
- [ ] Style selector: Socratic / Coach / Direct / Explainer (maps to
      `style` field)
- [ ] Preview panel: shows generated system prompt (read-only textarea)
      that updates live as form fields change
- [ ] Save button: `POST /tutors/sessions` with form data, creates
      `tutor_sessions` entry with `agent_spec` JSONB
- [ ] Form validation: student name required, subject required, at least
      one material selected (warning, not blocking)
- [ ] Responsive layout: single column on mobile, two columns (form +
      preview) on desktop

---

## Dependencies

**Requires:**
- Sprint 1 (clean architecture): domain entities (`TutorAgentSpec`,
  `TutorTurnOutput`, `TutorSession`, `LearnerProfile`), port protocols
  (`ChatLLM`, `Embeddings`, `VectorStore`), DI container, config
- Sprint 2 (database): `tutor_sessions` and `tutor_messages` tables, UoW,
  session factory, Postgres running in Docker
- Sprint 3 (embeddings/vector store): GeminiEmbeddingsAdapter + pgvector
  store for RAG retrieval; must use `task_type=RETRIEVAL_QUERY` for search
  queries
- Sprint 5 (frontend): Next.js scaffold, design system, shadcn/ui
  components, i18n setup

**Produces for:**
- Sprint 9 (STT/TTS): voice input/output hooks on chat panel (S9-006 Voice
  Input, S9-005 Read To Me button)
- Sprint 8 (sign language): VLibras integration point on tutor messages,
  "Show in Libras" button
- Sprint 10 (WebSocket streaming): WS endpoint + `useTutorWs` hook for
  token-by-token streaming

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LangGraph Postgres checkpointer compatibility with asyncpg | Medium | langgraph-checkpoint-postgres 2.0.x verified on PyPI; uses its own connection pool (conninfo string, not SQLAlchemy engine); requires `.setup()` on first use |
| Structured output parsing failures (LLM returns invalid JSON) | Medium | `generate_response` node uses Pydantic `model_validate_json` with fallback: if parse fails, wrap raw text as `answer_markdown` |
| RAG context too large for context window | Low | Hard cap at 4000 tokens for injected chunks; FIFO eviction of oldest chunks |
| Wrong embedding task_type degrades RAG quality | High | Enforce `task_type=RETRIEVAL_QUERY` for search queries; unit test verifies correct task_type is passed to GeminiEmbeddingsAdapter |
| WebSocket connection drops on mobile networks | Medium | Sprint 7 uses HTTP POST (no WS needed); Sprint 10 adds WS with reconnection logic + exponential backoff (1s, 2s, 4s, max 30s) |
| Multiple accessibility playbooks conflicting | Low | Playbooks are composable by design; conflicting settings resolved with "most accommodating wins" (e.g., largest font size, most line spacing) |
| Tutor hallucination despite RAG | High | Citation requirement on every RAG-grounded response + confidence threshold on relevance scores + explicit "I'm not sure about this" fallback when no chunks score above threshold |
| AsyncPostgresSaver serialization errors | Medium | Call `.model_dump()` on all Pydantic objects before placing in graph state; use `exclude_types` parameter in `astream_events` to filter non-serializable event types |
| Progressive hint reveal state management | Low | Hints stored as ordered list in TutorTurnOutput; frontend tracks reveal index per message in local component state |
| Comprehension routing infinite loop | Medium | Max 2 scaffolding iterations per turn; after second scaffolding, advance to END regardless of comprehension level |

---

## Testing Plan

- **Unit tests:** Tutor workflow node functions (understand_intent,
  search_materials, generate_response, check_comprehension,
  add_scaffolding) with mock ports; playbook merging logic; system prompt
  generation; conditional routing logic (confused/partial/solid paths)
- **Integration tests (Docker Postgres):** LangGraph checkpointer round-trip
  (write checkpoint -> read checkpoint -> verify state);
  AsyncPostgresSaver `.setup()` idempotency; RAG retrieval with real pgvector
  using `task_type=RETRIEVAL_QUERY`; session CRUD via API endpoints
- **API tests:** HTTP POST `/sessions/{id}/messages` returns valid
  `TutorTurnOutput`; input validation (2000 char limit); rate limiting
- **Frontend tests:** Chat panel rendering with React Testing Library;
  structured response collapsible sections; hint progressive reveal (1 at
  a time); input method selector toggle; accessibility audit (axe-core)
  on chat components; playbook adaptation visual regression tests;
  VLibras button rendering per tutor message
