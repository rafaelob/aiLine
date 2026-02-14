# AiLine Demo Script (3 Minutes)

**Narrative:** "Meet Ana" -- a hearing-impaired student with dyslexia who speaks Portuguese and is learning English.

---

## 0:00 - 0:15 | Meet Ana (The Problem)

**Screen:** Landing page with accessibility theme selector visible.

**Narration:**
> "Meet Ana. She's a 4th-grader in Sao Paulo -- hearing impaired, dyslexic, and bilingual. Her teacher needs to create a science lesson about the water cycle that works for Ana AND her 30 classmates. Today, that takes hours of manual adaptation. With AiLine, it takes 90 seconds."

**Actions:**
1. Show the AiLine dashboard (logged in as the teacher)
2. Point out the accessibility persona selector in the header (9 themes visible)
3. Brief hover over "Hearing Impaired" and "Dyslexia" persona badges

---

## 0:15 - 0:45 | Create an Adaptive Lesson (AI Pipeline)

**Screen:** Plan creation form -> Pipeline Viewer.

**Narration:**
> "The teacher types: 'Water cycle for 4th grade, student has hearing impairment and dyslexia.' Watch what happens."

**Actions:**
1. Type the lesson request in the plan creation form
2. Select grade level, check accessibility options (hearing, dyslexia)
3. Click "Generate" -- the **Glass Box Pipeline Viewer** opens
4. **Highlight SSE streaming:** events appear in real-time
   - `stage.started: "rag_search"` and `stage.started: "profile_analysis"` appear simultaneously (parallel fan-out)
   - `stage.started: "planner"` -- show the SmartRouter badge (e.g., "Sonnet 4.5" chosen)
   - `quality.scored: 87` -- the Score Gauge animates to 87/100 (green)
   - `quality.decision: "accept"` -- pipeline continues
   - `stage.started: "executor"` -- tools fire (curriculum alignment)
5. Show BNCC standard alignment badge: "EF04CI02 -- Water Cycle"

**Key talking point:** "This is a Glass Box, not a black box. Every AI decision is visible, scored, and auditable. The SmartRouter selected the optimal model. The Quality Gate scored 87/100 -- above our accept threshold."

---

## 0:45 - 1:15 | Accessibility Features (Universal Design)

**Screen:** Dashboard with accessibility controls.

**Narration:**
> "Now let's see AiLine through Ana's eyes."

**Actions:**
1. **Theme toggle:** Switch to "Hearing Impaired" theme -- visual indicators replace audio cues, high-contrast borders appear
2. **Then toggle "Dyslexia"** theme -- font changes to OpenDyslexic-style, line spacing increases, background softens
3. **VLibras widget:** Click the Libras avatar -- it signs the lesson summary in Brazilian Sign Language (3D avatar)
4. **Reduced motion toggle:** Enable it -- all spring animations gracefully stop (OS preference respected)
5. **Empathy Bridge:** Quick demo of the disability simulator -- show what a standard page looks like with tunnel vision overlay

**Key talking point:** "9 persona-based themes. WCAG AAA compliance. Libras sign language via government VLibras. And the Empathy Bridge lets educators experience what their students face."

---

## 1:15 - 1:45 | Tutor Interaction (Socratic AI)

**Screen:** Tutor chat interface.

**Narration:**
> "Ana opens the lesson and asks the tutor: 'Why does water go up?'"

**Actions:**
1. Open the tutor chat panel
2. Type: "Why does water go up?"
3. Show the Socratic response: the tutor does NOT give the answer directly
   - Instead: "Great question! When you heat water in a pot, what do you see happening? That's a clue about evaporation."
4. Point out the **RAG citation** -- small reference badge showing which material chunk the tutor used
5. Point out the **confidence score** -- tutor's self-assessed confidence in the response
6. Show the structured response sections (Socratic question, hint, scaffolding)

**Key talking point:** "RAG-grounded, not hallucination-prone. Every tutor response cites its source material. Socratic questioning means Ana learns to think, not just copy answers."

---

## 1:45 - 2:15 | Export Comparison (Adapted vs Original)

**Screen:** Export Viewer with side-by-side comparison.

**Narration:**
> "Let's see the transformation."

**Actions:**
1. Open the **Export Viewer** -- show the "Accessibility Twin" (tabbed view)
2. **Left panel:** Original lesson (standard text, complex vocabulary)
3. **Right panel:** Adapted lesson -- simplified language, visual diagrams emphasized, alt-text on all images, sign language glossary
4. **Diff highlights:** Green/yellow highlights show exactly what changed and why
5. Scroll to show: vocabulary simplification, added visual aids section, Libras-friendly structure
6. Show the 10 export formats available (PDF, DOCX, HTML, etc.)

**Key talking point:** "Side-by-side transparency. The teacher sees exactly what the AI adapted, can override any decision, and export in 10 formats. This is not a black box."

---

## 2:15 - 2:45 | Reliability and Engineering Excellence

**Screen:** Split between health dashboard and code metrics.

**Narration:**
> "But beautiful UX means nothing if the system is not reliable."

**Actions:**
1. Show the **health endpoint** (`/health/ready`) returning `{"status": "ready"}` with DB + Redis checks
2. Flash the test count: **2,800+ tests** (1,993 backend + 770+ frontend), all green
3. Show the **circuit breaker** concept: "If Anthropic goes down, the SmartRouter escalates to OpenAI or Gemini. If all providers fail, the circuit breaker opens and returns a graceful degradation message."
4. Show **SSE replay**: "If the user's connection drops mid-pipeline, events are stored in Redis. On reconnect, missed events are replayed -- no lost work."
5. Flash key stats: 60 ADRs, 120 features, hexagonal architecture, tenant isolation

**Key talking point:** "Every architectural decision is documented. Circuit breaker, retry with backoff, SSE replay, tenant isolation at the DB level. This is production-grade engineering."

---

## 2:45 - 3:00 | Impact Statement + Call to Action

**Screen:** Return to Ana's completed lesson on screen.

**Narration:**
> "AiLine: Adaptive Inclusive Learning -- Individual Needs in Education. One AI-powered platform that transforms how educators serve every learner, regardless of ability, language, or learning style."

> "120 features. 2,800+ tests. 60 architecture decisions. 4 AI agents. 3 LLM providers. 9 accessibility themes. 4 curriculum standards. Built in one week."

> "Because every student deserves a lesson designed for them."

**Actions:**
1. Zoom out to show the full dashboard with the completed lesson
2. Final shot: AiLine logo + tagline

---

## Technical Setup for Demo

**Prerequisites:**
```bash
cp .env.example .env   # Add ANTHROPIC_API_KEY + GOOGLE_API_KEY
docker compose up -d --build
# Open http://localhost:3000
```

**Demo Mode:** The application includes a DemoModeMiddleware with 3 pre-cached scenarios for reliable offline demos.

**Fallback Plan:**
- If live LLM calls fail: Demo Mode provides cached golden-path responses
- If Docker issues: Pre-recorded video backup (record before demo day)
- If network issues: All 3 demo scenarios work with cached data
