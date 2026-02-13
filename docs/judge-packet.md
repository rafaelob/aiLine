# AiLine -- Judge Packet

**Adaptive Inclusive Learning -- Individual Needs in Education**
Hackathon: "Built with Opus 4.6" | Feb 10-16, 2026

---

## At a Glance

| Metric | Value |
|--------|-------|
| Features shipped | 73 |
| Backend tests | 1,527+ (1,350 runtime + 177 agents) |
| Frontend tests | 331 (41 suites) |
| Live API integration tests | 65 (real Anthropic/OpenAI/Gemini) |
| Architecture Decision Records | 59 |
| Architecture | Hexagonal (Ports-and-Adapters) |
| AI agents | 4 typed (Pydantic AI 1.58) |
| LLM providers | 3 (Anthropic, OpenAI, Gemini) |
| Accessibility themes | 9 (WCAG AAA) |
| Curriculum standards | 4 (BNCC, CCSS Math, CCSS ELA, NGSS) |
| Languages | 3 (English, Portuguese, Spanish) |
| SSE event types | 14 (with replay + terminal guarantee) |
| Docker services | 4 (API, Frontend, PostgreSQL, Redis) |
| Build time (full stack) | Single `docker compose up` command |

---

## 3 ADR Highlights

### ADR-001: Why Hexagonal Architecture

**Decision:** Domain core has zero framework imports. All external systems accessed through port interfaces (protocols).

**Why it matters:** Swapping from ChromaDB to pgvector required changing one adapter file. Adding Gemini as a third LLM provider required one adapter. The domain layer remained untouched. This is not just clean code -- it is operational resilience.

### ADR-049: Why Multi-LLM Smart Routing

**Decision:** Weighted complexity scoring (token count 0.25, structured output 0.25, tools 0.25, history 0.15, intent 0.10) routes requests to the optimal model tier.

**Why it matters:** Not every request needs Opus. A simple vocabulary lookup uses Haiku (fast, cheap). A complex lesson plan with tool calling uses Sonnet or Opus. Hard overrides prevent cheap models from handling tasks that require tool use or strict JSON. Escalation ladder handles failures by moving up tiers automatically.

### ADR-054 + ADR-055: Why SSE with Replay + Terminal Guarantee

**Decision:** 14 typed SSE events stored in Redis ZSET (score=seq, TTL 30min). RunContext async context manager guarantees exactly one terminal event (run.completed or run.failed) per pipeline run.

**Why it matters:** AI pipelines take 30-90 seconds. Users on mobile or unstable connections cannot afford to lose progress. SSE replay delivers missed events on reconnect. The terminal guarantee ensures the UI always reaches a final state -- no stuck spinners, no phantom runs.

---

## Safety and Accessibility Checklist

- [x] **WCAG AAA** -- 9 persona-based themes (hearing, visual, cognitive, motor, dyslexia, autism, ADHD, anxiety, default)
- [x] **Libras Sign Language** -- VLibras 3D avatar for output; MediaPipe + TF.js for gesture input
- [x] **Reduced Motion** -- OS preference sync + manual override
- [x] **Tenant Isolation** -- JWT-only teacher_id, composite FK at DB level, cross-tenant integration tests
- [x] **Input Sanitization** -- Prompt injection prevention, DOMPurify for HTML, structured output enforcement
- [x] **Rate Limiting** -- Sliding window, 429 responses, X-RateLimit-* headers
- [x] **Circuit Breaker** -- 5 failures -> 60s open -> half-open -> reset
- [x] **Security Headers** -- CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy
- [x] **LGPD/FERPA Ready** -- No PII in analytics, consent-based processing, right to deletion
- [x] **RAG Grounding** -- Tutor responses cite source material; confidence scores on every response

---

## How to Run Locally

```bash
# 1. Clone and configure
git clone <repo-url> && cd aiLine
cp .env.example .env
# Add: ANTHROPIC_API_KEY, GOOGLE_API_KEY (minimum)

# 2. Launch (one command)
docker compose up -d --build

# 3. Open
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health/ready
```

All 4 services (PostgreSQL + pgvector, Redis, FastAPI API, Next.js 16 frontend) start with health checks. Demo mode available for offline operation.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI 0.129, SQLAlchemy 2.x async, LangGraph 1.0.8 |
| AI Agents | Pydantic AI 1.58 (Planner, Executor, QualityGate, Tutor) |
| LLMs | Anthropic (Claude), OpenAI (GPT-4o), Google (Gemini 2.5) |
| Embeddings | gemini-embedding-001 @ 1536d (Matryoshka truncation) |
| Vector Store | pgvector 0.8 (HNSW index) on PostgreSQL 17 |
| Frontend | Next.js 16, React 19, Tailwind 4, React Compiler 1.0 |
| Accessibility | 9 CSS themes, VLibras, MediaPipe, ElevenLabs TTS, Whisper STT |
| Infrastructure | Docker Compose, Redis 7.x, GitHub Actions CI |
| Testing | pytest (1,527+), Vitest (331), Playwright E2E, axe-core a11y |

---

## What Makes AiLine Different

1. **Glass Box AI** -- Every pipeline stage is visible, scored, and auditable. Teachers see exactly what the AI decided and why.

2. **True Inclusivity** -- Not an afterthought. 9 disability-specific themes, Brazilian Sign Language (Libras) support, Empathy Bridge simulator for educator training.

3. **Production Engineering** -- Hexagonal architecture, 1,800+ tests, 59 ADRs, circuit breaker, retry with backoff, SSE replay, tenant isolation. Built to run, not just to demo.

4. **Multi-LLM Resilience** -- SmartRouter picks the optimal model per request. If one provider fails, automatic escalation. No single point of AI failure.

---

*Built with Claude Opus 4.6 | AiLine: Every student deserves a lesson designed for them.*
