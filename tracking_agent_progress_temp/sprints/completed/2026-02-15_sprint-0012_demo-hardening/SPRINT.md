# Sprint 0012 — Demo Hardening

**Status:** planned | **Date:** 2026-02-15
**Goal:** Bulletproof demo experience with cached golden paths, curated scenarios,
frontend polish, accessibility audit, 3-minute demo video, and final hackathon
submission.

---

## Scope & Acceptance Criteria

The demo must work flawlessly regardless of network conditions or LLM availability.
Setting `AILINE_DEMO_MODE=1` activates cached golden path responses for 3 curated
scenarios; the pipeline still runs the validator and executor stages so the Glass
Box viewer shows real transitions, but LLM calls are served from cache. A visible
"Demo Mode" badge appears in the frontend when active. Three curated scenarios
showcase different accessibility needs and curriculum systems. The frontend is
polished with loading skeletons, micro-interactions, and complete error handling.
An automated accessibility audit (axe-core + pa11y) verifies WCAG AAA compliance.
A 3-minute demo video and hackathon submission text are prepared. The repository is
cleaned, tagged `v1.0.0-hackathon`, and ready for submission.

---

## Architecture

- **Demo Mode**: `AILINE_DEMO_MODE=1` env var activates the demo subsystem.
  Architecture: request enters FastAPI -> `DemoCacheMiddleware` checks if demo mode
  is active AND the route matches a cached scenario -> if yes, returns cached
  golden path response with simulated timing; if no, falls through to real handlers.
  The pipeline still runs the validator + executor stages even in demo mode so that
  the Glass Box viewer shows real stage transitions; only the LLM responses are
  served from cached golden path data.
- **Golden Path Data (3 scenarios)**: Pre-generated JSON files in
  `runtime/ailine_runtime/data/demo/` containing complete pipeline outputs, export
  variants, tutor conversations, and accessibility scores for all 3 curated
  scenarios ("Meet Ana" / Dyslexia, "Full Spectrum" / TEA+TDAH, "US Classroom" /
  Visual impairment).
- **"Demo Mode" Badge**: When `AILINE_DEMO_MODE=1` is active, the frontend renders
  a visible "Demo Mode" badge (top-right corner, semi-transparent overlay) so that
  viewers and judges can see the system is running against cached data. The badge
  is styled with `position: fixed; z-index: 9999` and disappears when demo mode
  is off.
- **Graceful Degradation**: If real LLM is available, use it. If not, fall back to
  cached responses. The frontend experience is identical in both cases.

```
Request flow (demo mode, AILINE_DEMO_MODE=1):
  Client -> FastAPI -> DemoCacheMiddleware
    |-- Route matches cached scenario?
    |     YES --> Validator + Executor run (real stages) with cached LLM responses
    |             --> Simulated delay --> Golden path JSON response
    |     NO  --> Real handler (with LLM fallback to cache)

  Frontend badge:
    AILINE_DEMO_MODE=1 --> renders "Demo Mode" badge (top-right, semi-transparent)
```

---

## Stories

### S12-001: Demo Mode Toggle (Cached Golden Path)

**Description:** Demo mode interceptor that serves cached golden path responses for
reliable, fast demonstration. Activated via `AILINE_DEMO_MODE=1` environment
variable (already defined in `shared/config.py` as `Settings.demo_mode`). The
interceptor is a FastAPI middleware that matches incoming requests against 3 cached
scenario routes and returns pre-built responses with realistic simulated timing.
The pipeline still runs the validator and executor stages so the Glass Box viewer
shows real stage transitions; only the LLM call responses are served from cache.
The frontend displays a visible "Demo Mode" badge when this mode is active.

**Files:**
- `runtime/ailine_runtime/app/services/demo_cache.py` (new: demo cache service
  with scenario loading, route matching, simulated delay)
- `runtime/ailine_runtime/api/middleware/demo_mode.py` (new: FastAPI middleware)
- `runtime/ailine_runtime/api/app.py` (update: register demo middleware when
  `settings.demo_mode` is True)
- `runtime/ailine_runtime/data/demo/__init__.py` (new)
- `runtime/ailine_runtime/data/demo/scenarios.json` (new: scenario index)

**Implementation details:**
- `DemoCacheService` loads all scenario JSON files at startup into a dict keyed
  by `(http_method, path_pattern, scenario_id)`.
- `DemoCacheMiddleware` checks `request.app.state.settings.demo_mode`; if False,
  passes through immediately.
- For SSE endpoints (`/plans/generate/stream`), the middleware returns a
  `StreamingResponse` that yields cached SSE events with realistic delays
  (0.5-2s per stage change, 0.1s per progress event).
- For WebSocket endpoints (`/tutors/sessions/{id}/ws`), the middleware is not
  applied (WebSocket handled separately); instead, the tutor service checks demo
  mode and returns pre-cached conversation turns.
- Each cached response includes realistic HTTP headers (`Content-Type`,
  `X-Request-Id`, `X-Demo-Mode: true`).

**Deterministic seed inputs for guaranteed demo behavior.**
When demo mode is active, all randomness sources (UUIDs, timestamps, LLM
temperature) are seeded with deterministic values so that repeated demo runs
produce identical outputs. This ensures the demo narrative is fully predictable.

**Pre-recorded run replay as failsafe if LLM APIs fail during live demo.**
In addition to the cached golden path responses, the demo mode includes a
run replay engine that plays back a pre-recorded sequence of SSE events with
accurate timing. If the live pipeline fails mid-run (LLM timeout, rate limit,
network error), the system transparently switches to replaying the pre-recorded
event sequence from the point of failure. The frontend sees no difference.

**Acceptance Criteria:**
- [ ] `AILINE_DEMO_MODE=1` activates demo cache middleware
- [ ] Pipeline still runs validator + executor stages (real stage transitions
      visible in Glass Box viewer); only LLM responses are served from cache
- [ ] Cached golden path responses for 3 demo scenarios stored as JSON files
      under `runtime/ailine_runtime/data/demo/`
- [ ] "Demo Mode" badge visible in frontend UI (top-right corner, semi-transparent,
      `position: fixed; z-index: 9999`) when `AILINE_DEMO_MODE=1` is set
- [ ] Deterministic seed inputs: UUIDs, timestamps, and LLM temperature are
      seeded for reproducible demo output
- [ ] Pre-recorded run replay engine plays back SSE event sequences as failsafe
      when live pipeline fails mid-run
- [ ] Transparent failover: if live pipeline errors during demo, replay engine
      takes over from the last successful event without frontend disruption
- [ ] SSE streaming simulated with realistic timing (0.5-2s per stage transition)
- [ ] All 9 export variants pre-generated and cached per scenario
- [ ] Accessibility scores show realistic values (82-94 range depending on scenario)
- [ ] Tutor has pre-cached conversation flows (first 5 turns per scenario)
- [ ] Sign language recognition works with pre-recorded hand landmark data files
- [ ] Graceful fallback: if `AILINE_DEMO_MODE=1` but request does not match a
      cached route, fall through to real handlers
- [ ] `X-Demo-Mode: true` header included in all demo responses
- [ ] Demo mode does not affect the test suite (tests always use real handlers)

---

### S12-002: Curated Demo Scenarios (3 Scenarios)

**Description:** Three pre-built demo scenarios showcasing different accessibility
needs, curriculum systems, and languages. Each scenario includes complete pipeline
output, all 9 export variants, tutor conversation history, and a golden path JSON
file for deterministic demo replay.

**Files:**
- `runtime/ailine_runtime/data/demo/scenarios/scenario_01_math_tea.json` (new)
- `runtime/ailine_runtime/data/demo/scenarios/scenario_02_science_inclusive.json` (new)
- `runtime/ailine_runtime/data/demo/scenarios/scenario_03_literacy_dyslexia.json` (new)
- `runtime/ailine_runtime/data/demo/exports/` (new: pre-rendered HTML/text exports
  for all 3 scenarios, 9 variants each = 27 files)
- `runtime/ailine_runtime/data/demo/tutor/` (new: pre-cached tutor conversations,
  1 per scenario)

**Three scenarios designed for maximum visual impact:**
1. **"Meet Ana"** (Dyslexia + Libras) -- emotional hook, character-driven
2. **"Full spectrum"** (TEA + TDAH + all needs) -- technical depth, multi-need
3. **"US Classroom"** (English, CCSS Math, Visual impairment) -- international appeal

These map to the existing three scenarios below but reframe their demo purpose.
Scenario 3 (Literacy/Dyslexia) becomes the "Meet Ana" lead scenario in the video.
Scenario 1 (Math/TEA) demonstrates full spectrum support. Scenario 2 (Science/
Hearing+ADHD) demonstrates international reach and multi-need handling.

**Scenario 1: "Math for TEA student" (BNCC, 6 ano)**
```
Input:  "Plano de aula de fracoes para 6o ano com aluno TEA na turma"
System: BNCC (Brazil)
Grade:  6o ano
Language: pt-BR
Accessibility needs: autism (TEA)
Highlights:
  - Visual schedule with pictograms and timers
  - Predictable structure (same routine each step)
  - Sensory break slots built into the plan
  - Libras avatar for sign language support
  - Simplified student plan with visual cues
Accessibility score: 92
Export variants: all 9
Tutor conversation (5 turns):
  1. Student: "O que sao fracoes?"
  2. Tutor: (Socratic) "Voce ja dividiu uma pizza em pedacos iguais? Cada pedaco e uma fracao..."
  3. Student: "Como sei qual fracao e maior?"
  4. Tutor: "Boa pergunta! Vamos comparar usando desenhos..."
  5. Student: "Entendi, obrigado!"
```

**Scenario 2: "Science for inclusive classroom" (CCSS, Grade 5)**
```
Input:  "Lesson plan on water cycle for Grade 5 with hearing-impaired and ADHD students"
System: Common Core (US)
Grade:  Grade 5
Language: en
Accessibility needs: hearing impairment, ADHD
Highlights:
  - Closed captions on all video content
  - Chunked activities (max 10 minutes per chunk)
  - Movement breaks every 15 minutes
  - Visual diagrams with alt text
  - High-contrast mode for projector visibility
Accessibility score: 87
Export variants: all 9
Tutor conversation (5 turns):
  1. Student: "What is evaporation?"
  2. Tutor: "Great question! Have you ever seen a puddle disappear on a hot day?..."
  3. Student: "Why does water go up into clouds?"
  4. Tutor: "Think about what happens when you boil water..."
  5. Student: "Oh, so the sun heats the water and it turns into vapor!"
```

**Scenario 3: "Literacy with dyslexia support" (BNCC, 3 ano)**
```
Input:  "Plano de alfabetizacao com alunos dislexicos, incluindo texto alternativo e leitura em voz alta"
System: BNCC (Brazil)
Grade:  3o ano
Language: pt-BR
Accessibility needs: dyslexia
Highlights:
  - OpenDyslexic font applied in dyslexia-friendly export
  - Read-aloud button on every text block (TTS integration)
  - Simplified text at Flesch-Kincaid grade 2 level
  - Large print variant (24px base, 1.8 line-height)
  - Color-coded syllable highlighting
Accessibility score: 85
Export variants: all 9
Tutor conversation (5 turns):
  1. Student: "Eu nao consigo ler direito"
  2. Tutor: "Tudo bem! Vamos devagar. Quer que eu leia junto com voce?..."
  3. Student: "As letras parecem se mexer"
  4. Tutor: "Isso acontece com muitas pessoas. Vamos usar uma regua de leitura..."
  5. Student: "Com a regua ficou mais facil!"
```

**Each scenario JSON structure:**
```json
{
  "scenario_id": "scenario_01_math_tea",
  "input": { "user_prompt": "...", "subject": "...", "grade": "...", ... },
  "pipeline_run": {
    "run_id": "01DEMO0001...",
    "stages": [ ... ],
    "accessibility_score": 92,
    "total_time_ms": 45000
  },
  "plan": { ... },
  "exports": {
    "standard_html": "...",
    "low_distraction_html": "...",
    ...
  },
  "tutor_conversation": [ ... ],
  "sse_events": [ ... ]
}
```

**Acceptance Criteria:**
- [ ] Scenario 1 (Math/TEA/BNCC): complete plan, 9 exports, 5 tutor turns,
      score 92, visual schedule with pictograms
- [ ] Scenario 2 (Science/Hearing+ADHD/CCSS): complete plan, 9 exports, 5 tutor
      turns, score 87, captions and movement breaks
- [ ] Scenario 3 (Literacy/Dyslexia/BNCC): complete plan, 9 exports, 5 tutor
      turns, score 85, OpenDyslexic font and read-aloud
- [ ] Each scenario includes: pre-generated plan JSON, all 9 export variant files,
      tutor conversation JSON, golden path SSE event sequence
- [ ] Scenario data generated by running real pipeline (with real LLM) and caching
      the output; not hand-written
- [ ] Scenario index file (`scenarios.json`) lists all scenarios with metadata for
      demo UI discovery
- [ ] Export HTML files are fully rendered and self-contained (inline CSS, no
      external dependencies)

---

### S12-003: Frontend Polish (Animations, Skeletons, Loading States)

**Description:** Add loading skeletons, micro-interactions, page transitions, empty
states, error boundaries, and toast notifications for a polished demo experience.
All animations respect `prefers-reduced-motion`.

**Files:**
- `frontend/components/ui/skeleton.tsx` (new: reusable skeleton component)
- `frontend/components/ui/toast.tsx` (new or update: shadcn/ui toast)
- `frontend/components/ui/error-boundary.tsx` (new: React error boundary)
- `frontend/components/ui/empty-state.tsx` (new: empty state with illustration)
- `frontend/components/pipeline/pipeline-viewer.tsx` (update: add skeleton)
- `frontend/components/plan/plan-tabs.tsx` (update: add loading skeleton)
- `frontend/components/plan/score-gauge.tsx` (update: add loading animation)
- `frontend/components/chat/chat-messages.tsx` (update: add typing skeleton)
- `frontend/components/export/export-viewer.tsx` (update: add skeleton)
- `frontend/app/layout.tsx` (update: add page transition wrapper)

**Implementation details:**
- **Skeletons:** Pulse-animated placeholder shapes matching the content they
  replace. Skeleton for plan content (3 text lines + heading), export viewer
  (two side-by-side panes), score gauge (circular arc), chat messages (bubble
  shapes).
- **Page transitions:** `framer-motion` `AnimatePresence` with fade + slight
  vertical slide (opacity 0->1, y 8->0, duration 200ms). Optionally integrate
  with View Transitions API where supported.
- **Smooth scroll:** `scroll-behavior: smooth` on html, with
  `scrollIntoView({ behavior: "smooth" })` for programmatic scrolling to new
  content.
- **Empty states:** Illustrated cards with descriptive text and a primary action
  button (e.g., "No plans yet. Create your first plan." with "Create Plan" CTA).
- **Error boundaries:** React `ErrorBoundary` component wrapping route segments.
  Shows friendly error message with "Try Again" button. Logs error to console
  (and structured logger in production).
- **Toast notifications:** shadcn/ui toast component for success ("Plan generated
  successfully!"), error ("Failed to generate plan. Please try again."), and info
  ("Exporting plan...") notifications. Auto-dismiss after 5s, dismissible by
  click, accessible via `role="alert"`.
- **Reduced motion:** All `framer-motion` animations wrapped in
  `useReducedMotion()` check; if reduced motion preferred, skip animations and
  show instant state changes.

**Acceptance Criteria:**
- [ ] Loading skeletons for: plan content, export viewer, score gauge, chat messages
- [ ] `framer-motion` page transitions (fade + slide, 200ms)
- [ ] `scroll-behavior: smooth` on html element
- [ ] Empty states with descriptive text and primary action CTA for: plans list,
      exports list, chat (no messages yet)
- [ ] Error boundaries wrapping each route segment with friendly error UI
- [ ] Toast notifications (shadcn/ui) for success, error, and info actions
- [ ] All animations respect `prefers-reduced-motion` (instant transitions when
      reduced motion enabled)
- [ ] No layout shift (CLS) during skeleton-to-content transitions
- [ ] Skeleton dimensions match actual content dimensions (prevent visual jump)
- [ ] Toast accessible via `role="alert"` and auto-dismissed after 5 seconds

---

### S12-004: Accessibility Audit (axe-core + pa11y)

**Description:** Automated and manual accessibility audit of the entire frontend
application. Automated scans via axe-core (component-level) and pa11y (page-level).
Manual audit for keyboard navigation, screen reader compatibility, focus management,
and color contrast.

**Files:**
- `frontend/tests/a11y/axe-scan.test.ts` (new: axe-core automated scan per page)
- `frontend/tests/a11y/pa11y-scan.ts` (new: pa11y script for page-level scan)
- `docs/a11y-audit-report.md` (new: audit findings and resolutions)
- `frontend/tests/a11y/keyboard-nav.test.ts` (new: keyboard navigation tests)

**Automated scans:**
- **axe-core** (via `@axe-core/react` or `vitest-axe`): run against every rendered
  page (dashboard, plan viewer, export viewer, tutor chat, settings). Assert zero
  critical and serious violations.
- **pa11y** (CLI): run against the built app served locally. WCAG AAA standard.
  Pages scanned: `/`, `/plans/{id}`, `/plans/{id}/exports`, `/tutors/{id}/chat`,
  `/settings`.

**Manual audit checklist:**
```markdown
- [ ] Keyboard navigation: Tab through all interactive elements in logical order
- [ ] Keyboard navigation: Enter/Space activates buttons and links
- [ ] Keyboard navigation: Arrow keys navigate within tab lists and menus
- [ ] Keyboard navigation: Escape closes modals and dropdowns
- [ ] Focus management: Focus moves to new content when navigating
- [ ] Focus management: Focus ring visible on all interactive elements
- [ ] Focus management: No focus traps (except modals)
- [ ] Screen reader: Page titles announced on navigation
- [ ] Screen reader: Headings hierarchy (h1 > h2 > h3) logical
- [ ] Screen reader: Form labels associated with inputs
- [ ] Screen reader: Images have descriptive alt text
- [ ] Screen reader: ARIA landmarks (main, nav, aside) present
- [ ] Screen reader: Live regions announce dynamic content
- [ ] Color contrast: All text meets 7:1 ratio in high-contrast mode
- [ ] Color contrast: All text meets 4.5:1 ratio in standard mode
- [ ] Color contrast: Non-text elements (icons, borders) meet 3:1 ratio
- [ ] Motion: Animations disabled with prefers-reduced-motion
- [ ] Text: All text resizable to 200% without loss of content
- [ ] Touch: All targets >= 48x48px
```

**Acceptance Criteria:**
- [ ] axe-core scan: 0 critical violations, 0 serious violations across all pages
- [ ] pa11y scan: 0 errors at WCAG AAA level on all 5 main pages
- [ ] Keyboard navigation audit: all interactive features accessible via keyboard
      only (no mouse required)
- [ ] Screen reader walkthrough documented (VoiceOver on macOS or NVDA on Windows):
      user can complete full demo flow using screen reader
- [ ] Color contrast: all text meets 7:1 ratio in high-contrast mode, 4.5:1 in
      standard mode
- [ ] Focus management: logical tab order, visible focus indicators (2px solid,
      offset 2px), no focus traps
- [ ] Audit report (`docs/a11y-audit-report.md`) with: findings, severity, status
      (resolved/deferred), evidence (screenshots or tool output)
- [ ] All critical and serious findings resolved before submission
- [ ] Minor/moderate findings documented with follow-up items in
      `control_docs/TODO.md`

---

### S12-005: Demo Video + Submission Text

**Description:** Record a 3-minute demo video showcasing AiLine's capabilities and
write the hackathon submission text covering project overview, tech stack, innovation,
and impact.

**Files:**
- `docs/demo-video-script.md` (new: video script with timestamps)
- `docs/submission.md` (new: hackathon submission text)
- `docs/demo-video-checklist.md` (new: recording setup checklist)

**Video script (3 minutes):**

**Primary narrative: "Meet Ana" (updated from Gemini consultation)**

This narrative is a character-driven, emotionally engaging 5-act story
that demonstrates technical depth through Ana's experience.

```markdown
## Act 1 -- THE STRUGGLE (0:00-0:20)
- Show dense text on screen (standard lesson plan PDF).
- Enable "Simulate Dyslexia" toggle.
- Text dances, screen blurs -- the viewer experiences dyslexic reading.
- Narration: "This is Ana's reality. Standard platforms are walls,
  not doors."

## Act 2 -- THE MAGIC SWITCH (0:20-0:45)
- Click Dyslexia Persona toggle.
- Whoosh animation plays.
- Font changes to OpenDyslexic, spacing increases, contrast jumps.
- Narration: "One click, and the wall disappears."

## Act 3 -- THE ENGINE (0:45-1:45)
- Upload a PDF into the Pipeline Run Viewer.
- Glass Box viewer shows stages animating in real-time via SSE.
- Quality Gate shows RED (score: 65).
- Click "Fix with AI".
- Score gauge spins from 65 up to 98.
- Narration: "Our multi-agent brain analyzes content and automatically
  simplifies."

## Act 4 -- COMMUNICATION (1:45-2:30)
- Switch to Sign Language Layout.
- Webcam detects "Next" gesture via MediaPipe -- content advances
  hands-free.
- VLibras avatar signs a summary of the lesson content.
- Narration: "Ana communicates in LIBRAS hands-free."

## Act 5 -- CLOSE (2:30-3:00)
- Dashboard with progress graph showing Ana's learning trajectory.
- Tagline: "AiLine isn't just a tool, it's an empathy bridge."
- End card: AiLine logo + team credits + hackathon branding.
```

**Fallback narrative (original structure, in case "Meet Ana" does not
fit the recording flow):**

```markdown
## 0:00-0:30 -- Problem Statement
- "15% of students worldwide have disabilities that affect their learning."
- "Teachers spend hours adapting lesson plans for diverse needs."
- "Most ed-tech ignores accessibility. We are changing that."
- Show statistics overlay, then transition to AiLine logo.

## 0:30-1:00 -- Solution Introduction
- "AiLine -- Adaptive Inclusive Learning, Individual Needs in Education."
- "An AI-powered platform that generates fully accessible lesson plans."
- Show: type a prompt in Portuguese -> pipeline starts -> stages animate.
- Narrate the pipeline stages briefly.

## 1:00-2:00 -- Live Demo (Scenario 1)
- Input: "Plano de aula de fracoes para 6o ano com aluno TEA na turma"
- Show SSE streaming: pipeline stages progress in real-time.
- Show plan tabs: Teacher view, Student view, Report, Exports.
- Show score gauge: accessibility score = 92.
- Show persona toggle: switch between Standard/TEA/ADHD/LowVision.
- Show export viewer: side-by-side standard vs. dyslexia-friendly.
- Show visual schedule with pictograms.

## 2:00-2:30 -- Wow Moments
- Libras avatar: click VLibras, watch sign language translation.
- Simulate Disability: toggle color blindness filter, show contrast.
- Accessibility Twin: before/after slider on a plan section.
- Tutor chat: student asks a question, tokens stream in real-time.

## 2:30-3:00 -- Tech Stack + Vision
- Architecture diagram: FastAPI + Next.js + PostgreSQL/pgvector + Docker.
- AI models: Claude Opus 4.6 (planning, tutoring), Gemini (embeddings),
  Whisper (STT), ElevenLabs (TTS), MediaPipe (sign recognition).
- "9 accessibility export variants per lesson plan."
- Future: multi-school rollout, analytics dashboard, curriculum marketplace.
- End with: "AiLine -- because every student deserves an education that
  adapts to them."
```

**Submission text:**
```markdown
## Project: AiLine -- Adaptive Inclusive Learning, Individual Needs in Education

### What it does
AiLine generates fully accessible, curriculum-aligned lesson plans using
multi-agent AI pipelines. Given a teacher's prompt and class accessibility
profile, AiLine produces a complete lesson plan with 9 accessibility export
variants (standard, low distraction, large print, high contrast, dyslexia-
friendly, screen reader, visual schedule, student plain text, audio script),
an accessibility score, and a Socratic AI tutor for students.

### Built with
- **Primary AI:** Claude Opus 4.6 (plan generation, Socratic tutor, image
  description, code generation)
- **Embeddings:** Google Gemini (gemini-embedding-001, 3072 dimensions)
- **Speech:** OpenAI Whisper (STT), ElevenLabs (TTS)
- **Sign Language:** MediaPipe (hand landmark recognition), VLibras (avatar)
- **Backend:** FastAPI, LangGraph, SQLAlchemy 2.x, PostgreSQL 17 + pgvector
- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, shadcn/ui, Zustand
- **Infrastructure:** Docker Compose, GitHub Actions CI

### Key Innovation
- 9 accessibility export variants generated per lesson plan
- Real-time Libras (Brazilian Sign Language) recognition via webcam
- "Simulate Disability" mode: experience the plan through different lenses
- Accessibility Twin: before/after comparison slider
- Socratic AI tutor with token-by-token streaming

### Impact
- Serves 15%+ of students with disabilities worldwide
- Reduces teacher plan adaptation time from hours to minutes
- Supports BNCC (Brazil) and Common Core (US) curriculum standards
- Available in English, Portuguese (BR), and Spanish
```

**Acceptance Criteria:**
- [ ] Demo video script covers all 5 segments with exact timestamps
- [ ] Video script includes narration text, screen actions, and transitions
- [ ] Submission text covers: what it does, built with, key innovation, impact
- [ ] Submission text names all AI models used with specific model IDs
- [ ] Recording checklist includes: OBS Studio settings (1080p, 30fps),
      browser setup (clean profile, no extensions), demo mode enabled,
      microphone test
- [ ] Script rehearsed and timed (must fit within 3:00)
- [ ] Backup plan: if live demo fails, switch to pre-recorded golden path

---

### S12-006: Final Cleanup + Tag v1.0.0-hackathon

**Description:** Clean all temporary files, sync all documentation, verify all tests
pass, ensure Docker Compose builds cleanly, and tag the release.

**Files:** Multiple (cleanup across the repository)

**Cleanup checklist:**
```markdown
1. Tracking cleanup:
   - [ ] Delete all files in tracking_agent_progress_temp/session_plans/
   - [ ] Move all sprint folders to completed/
   - [ ] Empty tracking_agent_progress_temp/artifacts_reports_tmp/
   - [ ] Clean tracking_agent_progress_temp/sync/ (if used)

2. Control docs sync:
   - [ ] control_docs/TODO.md: all [x] items migrated to FEATURES.md
   - [ ] control_docs/FEATURES.md: move implemented features to Done section
   - [ ] control_docs/SYSTEM_DESIGN.md: Dependencies in Use table current
   - [ ] control_docs/TEST.md: coverage targets and run commands current
   - [ ] control_docs/RUN_DEPLOY.md: Docker Compose and deploy commands current
   - [ ] control_docs/CHANGELOG.md: all changes documented
   - [ ] control_docs/SECURITY.md: current threat model
   - [ ] Total control_docs/ <= 500 lines

3. Repository hygiene:
   - [ ] No secrets committed (.env, API keys) -- verify with git log search
   - [ ] .gitignore covers: .env, __pycache__, .venv, node_modules, .next,
         *.pyc, .DS_Store, pgdata/
   - [ ] No temporary files (*.tmp, *.bak, nul)
   - [ ] No oversized files (check with git ls-files | xargs wc -c)

4. Quality gates:
   - [ ] ruff check . -- clean
   - [ ] ruff format --check . -- clean
   - [ ] mypy . -- clean
   - [ ] pytest tests/unit -- all green
   - [ ] pytest tests/integration -- all green (Docker)
   - [ ] pnpm lint -- clean
   - [ ] pnpm typecheck -- clean
   - [ ] pnpm test -- all green
   - [ ] docker compose up --build -- all services healthy

5. Documentation:
   - [ ] README.md updated with: project overview, quick start, architecture
         diagram, screenshots, team, license
   - [ ] CONTRIBUTING.md current
   - [ ] LICENSE file present and correct
   - [ ] docs/a11y-audit-report.md complete
   - [ ] docs/demo-video-script.md complete
   - [ ] docs/submission.md complete

6. Release:
   - [ ] Git tag: v1.0.0-hackathon
   - [ ] Tag message includes: summary of what is delivered, known limitations,
         setup instructions
```

**Acceptance Criteria:**
- [ ] All `tracking_agent_progress_temp/session_plans/` cleaned (empty)
- [ ] All sprint folders moved to `completed/` status directory
- [ ] `control_docs/` synced and total <= 500 lines
- [ ] `control_docs/CHANGELOG.md` updated with all hackathon changes
- [ ] No secrets in git history (verified with `git log --all -p | grep -i "api_key"`)
- [ ] All linters, typecheckers, and test suites pass
- [ ] `docker compose up --build` brings all services to healthy state
- [ ] Repository `README.md` updated with:
  - Project name and description
  - Architecture overview (text or diagram)
  - Quick start (`git clone` -> `cp .env.example .env` -> `docker compose up`)
  - Screenshots of key screens
  - Tech stack summary
  - Team credits
  - License
- [ ] Git tag `v1.0.0-hackathon` created with annotated message
- [ ] No `nul` file or other Windows artifacts committed
- [ ] `.gitignore` comprehensive and tested

---

## Dependencies

- **ALL prior sprints (0-11)**: Every feature, test, and infrastructure component
  must be in place before demo hardening.
- **Sprint 10** (SSE Streaming): SSE and WebSocket must work for live demo.
- **Sprint 11** (Docker + Testing): Docker Compose must be functional; all tests
  must pass.

---

## Decisions

- **Demo mode as middleware**: Middleware pattern chosen over mock services because
  it preserves the real API contract and can be toggled without code changes.
- **3 scenarios, not more**: Three scenarios cover the key demo narratives (autism,
  hearing+ADHD, dyslexia) across two curriculum systems (BNCC, CCSS) and two
  languages (pt-BR, en). More scenarios would dilute the demo impact.
- **Pre-generated via real pipeline**: Scenario data is generated by running the
  real pipeline with real LLM calls, then caching the output. This ensures the
  demo data is representative of actual system behavior.
- **Video before submission**: Record the video on Feb 15 (day before deadline)
  to allow time for re-recording if needed. Submission text can be finalized on
  Feb 16 morning.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Demo video recording quality (audio, screen) | Checklist with OBS settings; practice run; quiet room |
| Last-minute bugs during demo | Cached golden paths guarantee deterministic demo regardless of live system state |
| Submission deadline pressure (Feb 16) | Write submission text by Feb 15 EOD; video recorded by Feb 15; only final polish on Feb 16 |
| LLM API outage during live demo | Demo mode with cached responses is the primary safety net |
| Accessibility audit finds critical issues | Run axe-core scan early (Feb 14); critical fixes prioritized in Sprint 12 scope |
| Repository cleanup missed items | Automated cleanup checklist (S12-006) run as final gate before tagging |

---

## Timeline

| Date | Activity |
|------|----------|
| Feb 15 morning | S12-001 + S12-002: Demo mode + cached scenarios |
| Feb 15 midday | S12-003: Frontend polish (skeletons, transitions, toasts) |
| Feb 15 afternoon | S12-004: Accessibility audit (axe-core + pa11y + manual) |
| Feb 15 evening | S12-005: Record demo video (2-3 takes) |
| Feb 15 late | S12-006: Final cleanup, tag v1.0.0-hackathon |
| Feb 16 morning | Write submission text, final review, submit |

---

## Technical Notes

**Existing code to leverage:**
- `runtime/ailine_runtime/shared/config.py` already has `demo_mode: bool = False`
  in Settings -- just needs middleware to consume it.
- `runtime/ailine_runtime/api/app.py` has `create_app()` with middleware
  registration point after CORS.
- `runtime/ailine_runtime/api/streaming/sse.py` has `format_sse_event()` -- demo
  SSE streaming can reuse the same format.
- `runtime/ailine_runtime/accessibility/exports.py` has export generation logic --
  pre-generate exports by running this module with real input.
- `runtime/ailine_runtime/domain/entities/plan.py` has `ExportFormat` enum with
  all 9 variants (10 values, but `VISUAL_SCHEDULE_JSON` is structural, not a user
  export; 9 user-facing variants as listed in `Settings.default_variants`).

**Tools for accessibility audit:**
- `axe-core` via `@axe-core/react` (component-level) or `vitest-axe` (test-level)
- `pa11y` CLI: `npx pa11y http://localhost:3000 --standard WCAG2AAA`
- Browser DevTools Lighthouse: accessibility score as secondary check
- Screen reader: NVDA (Windows) for manual testing
