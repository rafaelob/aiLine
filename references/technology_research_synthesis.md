# AiLine Technology Research Synthesis
**Date:** 2026-02-11 | **Sources:** Web research, Gemini-3-Pro-Preview, Codex/GPT, Official docs

## 1. Verified Library Versions

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| Python | 3.13 | Runtime | python.org |
| FastAPI | 0.128.7 | API framework | pypi.org |
| SQLAlchemy | 2.0.46 | Async ORM | pypi.org |
| Alembic | 1.18.4 | Migrations | pypi.org |
| asyncpg | 0.31.0 | Postgres driver | pypi.org |
| pgvector-python | 0.4.2 | Vector extension | pypi.org |
| LangGraph | 1.0.8 | Workflow orchestration | pypi.org |
| langgraph-checkpoint-postgres | 2.0.x | Session persistence | pypi.org |
| DeepAgents | 0.4.1 | Planner framework | pypi.org |
| Claude Agent SDK | 0.1.35 | Executor SDK | pypi.org |
| Anthropic SDK | 0.79.0 | Claude API | pypi.org |
| OpenAI SDK | 1.109.1 | GPT API | pypi.org |
| google-genai | 1.62.0 | Gemini API | pypi.org |
| sse-starlette | 3.2.0 | SSE for FastAPI | pypi.org |
| structlog | latest | Structured logging | pypi.org |
| pydantic | 2.12.5 | Validation | pypi.org |
| pydantic-settings | latest | Config management | pypi.org |
| faster-whisper | latest | STT (CTranslate2) | pypi.org |
| sentence-transformers | 3.4.1 | Local embeddings | pypi.org |
| Next.js | 16.x | Frontend framework | nextjs.org |
| React | 19.2.x | UI library | react.dev |
| Tailwind CSS | 4.x | Utility CSS | tailwindcss.com |
| @mediapipe/tasks-vision | 0.10.32 | Browser ML | npm |
| @tensorflow/tfjs | 4.x | Browser inference | npm |
| framer-motion | 12.x | Animations | npm |
| next-intl | 4.x | i18n | npm |
| Zustand | 5.x | State management | npm |
| uuid-utils | 0.14.0 | UUID v7 compat (Python 3.13) | pypi.org |
| Recharts | 2.15.x | Charts | npm |

## 2. Embedding Models (Verified)

### gemini-embedding-001 (PRIMARY)
- **Default dimensions:** 3072
- **Supported range:** 128-3072 (MRL/Matryoshka truncation)
- **Recommended:** 768, 1536, 3072
- **Max input tokens:** 2,048
- **Normalization:** L2 normalization REQUIRED for truncated dimensions
- **API:** `output_dimensionality` parameter in EmbedContentConfig
- **Source:** https://ai.google.dev/gemini-api/docs/embeddings

### text-embedding-3-large (FALLBACK)
- **Dimensions:** 3072 (truncatable via `dimensions` param)
- **MTEB Score:** 64.6
- **Cost:** $0.13/1M tokens

### BGE-M3 (LOCAL/OFFLINE)
- **Dimensions:** 1024
- **Languages:** 100+
- **MTEB Score:** 63.0
- **License:** MIT

### CRITICAL: Do NOT mix embedding providers in same vector space
Embeddings from different models exist in incompatible vector spaces. Cosine similarity across providers is meaningless. Pick ONE provider per collection.

**Decision:** Use gemini-embedding-001 at 1536d (MRL truncated) as primary. All vectors in the same collection must use the same model.

## 3. LangGraph Patterns (Verified via Codex + Docs)

### Parallel Fan-Out (Static)
```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_edge(START, "rag_search")      # Both run from START
graph.add_edge(START, "profile_analysis") # in parallel
graph.add_edge(["rag_search", "profile_analysis"], "planner")  # Fan-in
graph.add_edge("planner", "validate")
```

### Dynamic Fan-Out (Send)
```python
from langgraph.types import Send

def route(state):
    return [Send("worker", {"item": x}) for x in state["items"]]

graph.add_conditional_edges(START, route, ["worker"])
```

### Streaming via astream_events v2
```python
async for event in graph.astream_events(input_data, version="v2"):
    kind = event["event"]
    if kind == "on_chat_model_stream":
        yield f"data: {json.dumps({'type': 'token', 'content': event['data']['chunk'].content})}\n\n"
    elif kind == "on_node_enter":
        yield f"data: {json.dumps({'type': 'status', 'node': event['name']})}\n\n"
```

### Checkpointer Serialization Fix
- All state values must be JSON-serializable (use .model_dump() on Pydantic objects)
- Use `exclude_types=["llm", "tool"]` in astream_events if serialization errors persist
- AsyncPostgresSaver requires `.setup()` on first use

## 4. Sign Language Architecture (Verified)

### Browser-Side Pipeline (No WebRTC)
```
Webcam → MediaPipe Hands+Pose (JS) → 21+33 landmarks → TF.js MLP classifier → Gloss labels → WebSocket → Backend LLM → Sentence
```

### MediaPipe Tasks Vision JS
- Package: `@mediapipe/tasks-vision@0.10.32`
- HandLandmarker: 21 landmarks per hand (x, y, z)
- PoseLandmarker: 33 body landmarks
- Running mode: VIDEO (frame-by-frame)
- GPU delegate for performance

### Available Libras Datasets
| Dataset | Size | Type |
|---------|------|------|
| Brazilian-Sign-Language-Alphabet | 4,411 images, 15 letters | Static images |
| LSWH100 | 144,000 images, 100 handshapes | Synthetic (Blender) |
| LIBRAS-UFOP | 56 signs, RGB-D + skeleton | Kinect data |

### VLibras Widget
- 21,000+ signs vocabulary
- 3 avatars: Icaro, Hosana, Guga
- CDN: `https://vlibras.gov.br/app/vlibras-plugin.js`
- 40M daily accesses
- Position options: TL, T, TR, R, BR, B, BL, L

### Dedicated WebSocket (NOT reuse tutor WS)
- Endpoint: `ws://.../ws/accessibility/libras`
- Client sends raw glosses instantly
- Server buffers for 2s silence then sends corrected sentence
- Global (available on all pages via React Context)

## 5. STT/TTS Models (Verified)

### STT: Whisper Large V3 Turbo
- 809M params (vs 1.55B for V3)
- 6x faster than V3, ~98% accuracy
- faster-whisper with CTranslate2 for optimization
- Supports 99+ languages (PT-BR, EN, ES confirmed)

### TTS Options
| Model | Languages | License | Quality |
|-------|-----------|---------|---------|
| ElevenLabs API | 32+ | Commercial | Excellent (primary) |
| MeloTTS | 6 (EN/ES/FR/CN/JP/KR) | MIT | Good (fallback) |
| FishAudio S1-mini | Multi | Apache 2.0 | Good |
| XTTS-v2 (Coqui) | 17 | Non-commercial | Excellent |

## 6. Frontend Architecture (Gemini-3-Pro-Preview Recommendations)

### Theme Engine (9 Personas, No FOUC)
1. Store preference in cookie `ailine-theme`
2. Read cookie in `layout.tsx` (Server Component) via `next/headers`
3. Apply theme class on `<body>` tag
4. CSS variables in `globals.css` switch per `.theme-*` class
5. Tailwind v4 `@theme` directive references CSS vars

### SSE in Next.js 16
- Must be Client Components (Server Components can't hold connections)
- Headless `<PlanGeneratorListener>` component pattern
- Updates Zustand store from SSE events

### View Transitions API
- Built into React 19.2 via Next.js 16
- `startViewTransition()` for page navigations
- Respects `prefers-reduced-motion`

## 7. Database Architecture (Consensus)

### UUID v7 for PKs
- Time-ordered (better B-tree locality)
- Sortable, cursor-friendly pagination
- **CORRECTION:** `uuid.uuid7()` is Python 3.14+, NOT 3.13 — must use `uuid-utils` (0.14.0) as compatibility wrapper for Python 3.13
- Create `new_uuid7()` wrapper: try stdlib `uuid.uuid7()` first, fall back to `uuid_utils.uuid7()`

### JSONB + GIN Indexes
- `accessibility_pack`, `metadata`, `export_data` as JSONB
- GIN indexes for key lookups
- TOAST auto-compresses large values

### Separate plan_exports Table
```sql
CREATE TABLE plan_exports (
    id UUID PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES study_plans(id),
    variant VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### pgvector HNSW Index (100K docs, 1536d)
```sql
CREATE INDEX CONCURRENTLY idx_chunks_embedding_hnsw
ON material_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 128);
-- Query-time: SET hnsw.ef_search = 64;
```

### SQLAlchemy Async UoW Pattern
```python
engine = create_async_engine("postgresql+asyncpg://...", pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class UnitOfWork:
    async def __aenter__(self):
        self.session = SessionFactory()
        return self
    async def __aexit__(self, exc_type, exc, tb):
        try:
            await (self.session.rollback() if exc else self.session.commit())
        finally:
            await self.session.close()
```

## 8. Multi-LLM Strategy

### SmartRouterAdapter Pattern
```python
class SmartRouterAdapter:
    def __init__(self, primary: ChatLLM, cheap: ChatLLM, fallback: ChatLLM):
        self.primary = primary    # Claude Opus 4.6
        self.cheap = cheap        # Gemini 2.5 Flash
        self.fallback = fallback  # GPT-4o

    async def generate(self, messages, response_format=None, **kwargs):
        model = self.cheap if self._is_simple(messages) else self.primary
        try:
            return await model.generate(messages, response_format=response_format, **kwargs)
        except Exception:
            return await self.fallback.generate(messages, response_format=response_format, **kwargs)
```

### Structured Output per Provider
- **Claude:** tool_use blocks (Pydantic → JSON Schema → tool input_schema)
- **OpenAI:** response_format: {type: "json_schema", json_schema: {schema: ...}}
- **Gemini:** response_schema in GenerateContentConfig

## 9. FastAPI SSE Pattern (Verified)
```python
from sse_starlette import EventSourceResponse

@app.get("/events")
async def events(request: Request):
    async def stream():
        while not await request.is_disconnected():
            yield {"event": "tick", "data": json.dumps(payload)}
            await asyncio.sleep(1)
    return EventSourceResponse(stream(), ping=15)
```

## 10. Architecture Decision Updates

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-013 | Parallel LangGraph topology | RAG + Profile analysis parallel before Planner |
| ADR-014 | gemini-embedding-001 at 1536d (MRL) | Best multilingual, free tier, Matryoshka truncation |
| ADR-015 | Browser-side sign language (MediaPipe JS + TF.js) | No server latency, privacy, reduced infra |
| ADR-016 | Dedicated Libras WebSocket | Cross-cutting concern, not tutor-specific |
| ADR-017 | SmartRouterAdapter for multi-LLM | Fallback chain + cost-aware routing |
| ADR-018 | Separate plan_exports table (TEXT) | Keep plans table lightweight, TOAST compression |
| ADR-019 | Cookie-based theme for SSR (no FOUC) | Server Component reads cookie → body class |
| ADR-020 | Whisper V3 Turbo via faster-whisper | 6x speed, 98% accuracy, CTranslate2 optimization |
| ADR-021 | ElevenLabs primary TTS + MeloTTS fallback | Best quality for demo + MIT fallback |

## 11. Expert Consultation Synthesis (2026-02-11)

### Sources: Gemini-3-Pro-Preview + Codex (GPT-5.2 equivalent) via Zen MCP

### Architecture Assessment (Consensus)

**Overall verdict:** Architecture is technically impressive but over-engineered for hackathon. Since Sprint 0-1 are done, DON'T rewrite — the hexagonal "Ports" narrative impresses judges.

**Top 5 Strategic Recommendations:**
1. **Prioritize "Glass Box" AI pattern** — show LangGraph internal reasoning in UI (the #1 wow factor)
2. **Reduce sign language scope** — 3-4 navigation gestures + VLibras (text→sign), NOT full Libras recognition
3. **Persona Toggle is strongest value prop** — live CSS var morphing between 9 themes
4. **SmartRouter with visible badges** — show "⚡ Gemini Flash" vs "🧠 Claude Opus" in UI
5. **"Meet Ana" demo narrative** — hero's journey (simulate disability → toggle → pipeline → sign language)

### Backend Patterns (Codex/GPT-5.2)

**SmartRouterAdapter Hybrid Classifier (superseded by Round 2 normalized scoring — see Section 12):**
- Deterministic complexity scoring (NOT token-only)
- Factors: input_tokens, structured_output_required, tools_required, history_turns, intent_tags
- ~~Score >= 4: primary (Claude Opus), Score <= 1: cheap (Gemini Flash), Ambiguous: cheap_with_escalation~~ (replaced by 0-1 weighted score in Round 2)
- Escalation triggers: JSON parse fail, schema validation fail, low validator score
- Max one escalation per request, persist chosen model in run state

**SSE Typed Event Contract:**
- Events: run.started, stage.started, stage.progress, quality.scored, quality.decision, refinement.started, refinement.completed, tool.started, tool.completed, stage.completed, stage.failed, run.completed, run.failed, heartbeat
- Event envelope: {run_id, seq (monotonic), ts (ISO), type, stage, payload}
- Terminal safety: ALWAYS emit run.completed or run.failed in finally block
- Throttle progress events (250ms min), batch token events
- Last-Event-ID support for reconnection

**Branch Error Envelopes:**
```python
async def safe_branch(fn, *args, **kwargs):
    try:
        return {"ok": True, "payload": await fn(*args, **kwargs), "error": None}
    except Exception as e:
        return {"ok": False, "payload": None, "error": str(e)}
```
At fan-in: proceed if one branch succeeds; fail-fast only when both fail.

**Multi-Tenancy:**
- App-level tenancy with TenantContext dependency
- Derive teacher_id from auth context ONLY (never from request body)
- Repository signatures require teacher_id parameter
- Cross-tenant isolation tests mandatory

### Frontend/UX Patterns (Gemini-3-Pro-Preview)

**Theme System (Tailwind v4):**
```css
@theme {
  --color-canvas: var(--canvas);
  --color-surface: var(--surface);
  --color-text-body: var(--text-body);
  --color-primary: var(--primary);
  --font-reading: var(--font-reading);
}
```
Use `data-theme` attribute (not CSS class) for theme switching.
`document.body.setAttribute('data-theme', 'dyslexia')` — pure CSS, no React re-render.

**Score Gauge (framer-motion):**
- useMotionValue + useTransform for counter
- Color interpolation: [0,50,80,100] → ["#be123c","#f59e0b","#10b981","#047857"]
- SVG motion.circle with pathLength animation
- 1.5s circOut easing

**Persona Toggle:**
- layoutId="active-pill" for sliding pill animation
- Spring physics: stiffness=300, damping=30
- Content container with `<motion.div layout>` for smooth resize

**Simulate Disability (Empathy Bridge):**
- Frame as educational tool for teachers, NOT user feature
- CSS-only: radial-gradient for tunnel vision, SVG filters for color blindness
- React Portal overlay with pointer-events: none
- Dyslexia: letter shuffling script (swap inner letters)

**Sign Language Layout:**
- Split-panel: Left 60% (content), Right 40% (communication deck)
- Top half: VLibras Avatar (output)
- Bottom half: User Webcam (input)
- Keeps input/output loop visually connected

**Demo Narrative (3 min):**
1. (0:00-0:30) Hook: "Meet Ana" — simulate dyslexia on dense text
2. (0:30-1:15) Magic: toggle persona → font changes, text simplifies → "Explain in Libras"
3. (1:15-2:15) Engine: pipeline viewer → Quality Gate failure (45%) → "Fix with AI" → 95%
4. (2:15-3:00) Close: webcam gesture recognition → "Education that adapts to the student"

### Risk Matrix (Expert Consensus)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Sign language TF.js model not ready | High | Very High | Tier 1/2 split, VLibras alone is demo-worthy |
| SSE→Zustand race conditions | Medium | Medium | Single reducer, sequential event processing |
| LLM API down during demo | High | Low | Demo mode with cached responses |
| Pipeline stream hangs | High | Medium | Heartbeat + timeout + fallback response |
| Over-scoping kills delivery | Critical | High | Strict sprint ordering, optional sprints marked |

## 12. Expert Consultation — Round 2 (2026-02-11)

### Sources: GPT-5.2/Codex (Backend/Architecture) + Gemini-3-Pro-Preview (Frontend/UX) via Zen MCP

---

### Backend / Architecture Findings (GPT-5.2/Codex)

#### CRITICAL FIX: uuid.uuid7() is Python 3.14, NOT 3.13

- Python 3.13 does **NOT** have `uuid.uuid7()` — it is scheduled for and shipped in Python 3.14 (released October 2025).
- **Verified:** https://docs.python.org/3.13/library/uuid.html — no uuid7 listed.
- **Verified:** https://docs.python.org/3.14/library/uuid.html — uuid7 present.
- Must use `uuid-utils` package (v0.14.0, supports Python 3.9-3.14) as compatibility wrapper.
- **Implementation pattern:**
```python
def new_uuid7() -> uuid.UUID:
    """Generate a UUID v7. Uses stdlib (3.14+), falls back to uuid-utils."""
    try:
        return uuid.uuid7()  # Python 3.14+
    except AttributeError:
        import uuid_utils
        return uuid_utils.uuid7()
```

#### SmartRouterAdapter Exact Scoring (Normalized 0-1)

Replaces the integer-based scoring from Round 1 with a continuous 0-1 score:

| Factor | Weight | Description |
|--------|--------|-------------|
| tokens | 0.35 | Normalized input token count |
| structured_output | 0.20 | Whether structured output (JSON schema) is required |
| tools | 0.20 | Number/complexity of tools in request |
| history_depth | 0.15 | Conversation history length |
| intent_risk | 0.10 | Risk classification of the intent (e.g., grading vs. greeting) |

**Routing thresholds:**
- Score <= 0.30: **cheap** (Gemini Flash) — simple greetings, FAQ, short completions
- Score >= 0.65: **primary** (Claude Opus) — complex planning, multi-tool, high-risk
- 0.30 < score < 0.65: **cheap_with_escalation** — start cheap, escalate on failure

**Escalation triggers (max ONE escalation per request):**
1. JSON parse failure on structured output
2. Schema validation failure (Pydantic)
3. Low quality score from validator
4. Tool-call failure (malformed tool input)

**Decision caching:**
- Cache key: normalized request signature + schema hash + toolset hash
- TTL: 5 minutes
- Avoids re-scoring identical request patterns

#### Pool Configuration for Hackathon (SQLAlchemy Async)

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # 30 min — prevent stale connections
)
```

#### Chunking Recommendation Update

- **512 tokens** with **64 overlap** (corrected from 50 overlap in earlier references)
- Add semantic splitter fallback for heading/paragraph boundaries
- Semantic splitter detects `# Heading`, `## Subheading`, `\n\n` paragraph breaks and prefers splitting at those boundaries before falling back to token-count splitting

---

### Frontend / UX Findings (Gemini-3-Pro-Preview)

#### WCAG AAA Verified Contrast Ratios

| Pair | Ratio | Standard |
|------|-------|----------|
| Slate 900 on Slate 50 (text-body on canvas) | 19:1 | AAA all sizes |
| Slate 600 on White (text-muted) | 7:1 | AAA large text, AA normal |
| Blue 700 (#1D4ED8) on White | AAA compliant | AAA large text |

#### Dark Theme Elevation System

| Token | Color | Hex | Usage |
|-------|-------|-----|-------|
| canvas | Slate 950 | #020617 | Page background |
| surface-1 | Slate 900 | #0F172A | Cards, panels |
| surface-2 | Slate 800 | #1E293B | Hover states, modals |
| surface-3 | Slate 700 | #334155 | Borders, dividers |

Each elevation level is one step lighter in the Slate scale, creating visual depth without relying on box-shadow (which is invisible on dark backgrounds).

#### Persona Toggle Implementation (Pure CSS, No Re-render)

- Direct DOM manipulation: `document.body.setAttribute('data-theme', id)`
- **NO React state or re-render needed** for theme switching
- Pure CSS variable swap via `data-theme` attribute
- React state only tracks the current theme ID for UI indicator (the pill animation)
- Actual visual change is entirely CSS-driven

#### VLibras Integration Pattern (Next.js)

```tsx
// In layout.tsx or a dedicated VLibrasProvider
import Script from 'next/script';

<Script
  src="https://vlibras.gov.br/app/vlibras-plugin.js"
  strategy="lazyOnload"
  onLoad={() => {
    new (window as any).VLibras.Widget('https://vlibras.gov.br/app');
  }}
/>

{/* Required DOM structure */}
<div vw="true" className="enabled">
  <div vw-access-button="true" className="active" />
  <div vw-plugin-wrapper="true">
    <div className="vw-plugin-top-wrapper" />
  </div>
</div>
```

- `strategy="lazyOnload"` ensures it loads after page is interactive (no LCP impact)
- Widget auto-attaches to the DOM structure above
- Initialize with: `new window.VLibras.Widget('https://vlibras.gov.br/app')`

#### i18n Pattern Correction (next-intl v4)

- Uses `middleware.ts` with `createMiddleware` (NOT `proxy.ts` as previously assumed)
- `getRequestConfig` reads locale from cookie
- `localePrefix: 'as-needed'` — no `/en/` prefix for default locale
- Pattern:
```typescript
// middleware.ts
import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['pt-BR', 'en', 'es'],
  defaultLocale: 'pt-BR',
  localePrefix: 'as-needed',
});
```

---

### ADR Updates from Round 2

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-027 | uuid-utils wrapper for uuid7 | Python 3.13 lacks stdlib uuid7; wrapper enables forward-compat with 3.14 |
| ADR-028 | Normalized 0-1 SmartRouter scoring | Continuous score with weighted factors; cleaner thresholds than integer scoring |
| ADR-029 | Decision caching for SmartRouter (5 min TTL) | Avoid re-scoring identical request patterns |
| ADR-030 | Semantic splitter fallback for chunking | Heading/paragraph-aware splitting before token-count fallback |
| ADR-031 | Dark theme elevation via Slate scale | Surface depth without box-shadow; WCAG AAA compliant |
| ADR-032 | VLibras via next/Script lazyOnload | No LCP impact; gov CDN widget with required DOM structure |
| ADR-033 | next-intl v4 middleware pattern | createMiddleware in middleware.ts, locale from cookie, localePrefix as-needed |
