# Sprint 35 — AI-Powered Educational Intelligence Tools

**Goal:** Build 3 AI-powered educational tools that transform AiLine from accommodation to empowerment: Social Story Generator (ASD, Carol Gray methodology), Cognitive Simplification Engine (4-level readability), and Predictive Accommodations with Adaptive Difficulty (Vygotsky ZPD). Each tool follows existing Pydantic AI agent + LangGraph workflow patterns.

**Theme:** Empowerment Layer Pillar 2 — AI Educational Tools. Architecture: Gemini-3.1-Pro (3 consultations). Frameworks: Carol Gray Social Stories 10.2, Flesch-Kincaid readability, Vygotsky Zone of Proximal Development.

**Duration:** 3 weeks | **Status:** planned

---

## Acceptance Criteria
- [ ] SocialStoryAgent generates 4:1 ratio (descriptive/perspective/affirmative to directive) stories
- [ ] Deterministic Carol Gray ratio validation in QualityGate (no LLM self-assessment)
- [ ] 10 scenario templates seeded (fire drill, substitute teacher, etc.)
- [ ] Multi-format export: large-print text, audio (TTS), visual schedule, PDF, mobile cards
- [ ] SimplificationAgent rewrites at 4 complexity levels preserving learning objectives
- [ ] Readability metrics (Flesch-Kincaid, Gunning Fog) deterministic and accurate (±0.5 grade)
- [ ] Complexity slider UI accessible (keyboard + screen reader)
- [ ] Telemetry pipeline ingests behavioral events (5-10s batches)
- [ ] BehavioralAnalyzer detects 6 signal types with normalized 0-1 scores
- [ ] ZPD adaptive difficulty: +1 after 3 correct, -1 after 2 wrong, frustration ceiling at 2
- [ ] Accommodation suggestions use dignity framing; NEVER auto-activate
- [ ] Teacher approval required for all persistent accommodation changes
- [ ] 2 new Pydantic AI agents, 3 new skills, 1 new LangGraph workflow
- [ ] 5 new DB tables, 14 new API endpoints

---

## Stories (F-394 → F-411) — 18 stories, 3 phases

### Phase 1 — Social Story Generator (P0)

**F-394: SocialStoryAgent + Quality Gate**
- New Pydantic AI agent (anthropic:claude-opus-4-6) with SocialStoryDraft output type
- Carol Gray 6 sentence types: Descriptive, Perspective, Affirmative, Directive, Control, Cooperative
- Deterministic 4:1 ratio validation: `validate_carol_gray_ratio()` — no LLM needed
- First-person check: reject "you should/must/need to" patterns
- AC: Agent generates tagged sentences. Ratio validation passes. First-person enforced.

**F-395: Scenario Template Library**
- DB: scenario_template (name, category, variables JSONB, default_sentences JSONB, locale)
- 10 pre-built templates: fire drill, substitute teacher, lunch routine, field trip, assembly, new student, test day, group work, recess conflict, homework routine
- API: GET /api/v1/social-stories/templates, GET /api/v1/social-stories/templates/{id}
- AC: 10 templates seeded. Variables fillable. Locale-aware (EN, PT-BR, ES).

**F-396: Social Story Multi-Format Export**
- Export pipeline: large-print text, audio (ElevenLabs TTS adapter), visual schedule, PDF (weasyprint), mobile cards (structured JSON)
- DB: social_story (teacher_id, student_id, title, content JSONB, quality_score, status, exports JSONB)
- API: POST /api/v1/social-stories/{id}/export/{format}
- AC: All 5 formats generate. PDF renders. Audio uses existing TTS adapter.

**F-397: Social Story Student Viewer**
- StoryCardViewer: swipeable cards with large text + illustration placeholders + TTS button per card
- VisualScheduleView: vertical timeline with numbered steps
- StoryLibrary: teacher grid with status badges (draft/approved/shared)
- AC: Cards display correctly. TTS per card. WCAG AA compliant.

**F-398: Social Story LangGraph Workflow**
- social_story_workflow: skills_node → social_story_node → validate_node → decision_node → export_node → scorecard
- SSE streaming with typed events (social_story.generating, social_story.validated, etc.)
- API: POST /api/v1/social-stories/generate (SSE stream)
- AC: Full workflow runs. SSE events emitted. Quality gate loops on <60 score.

**F-399: social-story-generator Skill**
- SKILL.md following agentskills.io spec; metadata: methodology=Carol Gray 10.2
- AccessibilityPolicy update: add to autism.should + adhd.should
- AC: Skill loads from registry. Policy routes correctly for ASD profiles.

### Phase 2 — Cognitive Simplification Engine (P0-P1)

**F-400: Readability Analysis Module**
- Pure Python deterministic metrics: flesch_kincaid_grade(), gunning_fog_index(), count_syllables()
- ReadabilityMetrics model: FK grade, Fog index, avg sentence length, complex word count
- recommend_level(): FK grade → simplification level 1-4
- AC: Metrics match standard corpora ±0.5 grade. Zero LLM dependency.

**F-401: Multi-Level Simplification Agent**
- SimplificationAgent (anthropic:claude-sonnet-4-6, cost-effective for rewriting)
- 4 levels: Original → Simplified → Highly Simplified → Symbol-Supported
- Rules per level: L2=shorter sentences/active voice, L3=one idea/concrete examples, L4=AAC symbol descriptions
- JargonTooltip mapping (original term → plain language explanation)
- CognitiveSimplificationResult with learning_objectives_preserved check
- API: POST /api/v1/content/simplify, POST /api/v1/content/analyze
- AC: All 4 levels preserve objectives. Jargon tooltips generated. L4 has symbols.

**F-402: Complexity Slider UI**
- ComplexitySlider (shadcn/ui Slider): levels 1-4 with labels, real-time content switch
- SimplifiedContentView: renders active level with jargon tooltips (Radix Tooltip)
- DiffHighlighter: highlights changes between adjacent levels
- TeacherLockControl: lock content at minimum complexity per concept
- AC: Slider keyboard accessible. Screen reader announces levels. Diff visible.

**F-403: cognitive-simplifier Skill + Workflow Integration**
- SKILL.md; metadata: target-profiles=learning adhd autism speech_language
- Reusable simplification_node in plan_workflow (after executor, before scorecard)
- Auto-generate Level 2+3 variants of student_plan field
- Tutor receives target_reading_level in prompt context
- AC: Plan workflow includes variants. Tutor adapts to reading level.

### Phase 3 — Predictive Accommodations + Adaptive Difficulty (P1)

**F-404: Telemetry Ingestion Pipeline**
- DB: student_telemetry (partitioned by date) — high-frequency behavioral events
- 7 signal types: time_on_task, error_rate, help_request, nav_backtrack, resp_deletion, session_abandon, engagement_drop
- Redis buffer for burst absorption; 30-day retention
- API: POST /api/v1/telemetry/events (batch, client batches every 5-10s)
- AC: Events stored partitioned. Retention enforced. Redis buffers bursts.

**F-405: Behavioral Analyzer Service**
- BehavioralAnalyzer: aggregates telemetry over rolling windows, generates normalized signals (0-1)
- Compare against student's historical baseline + peer cohort (anonymized)
- API: GET /api/v1/students/{id}/signals
- AC: Rolling window works. 6+ signal types detected. Normalized correctly.

**F-406: Accommodation Suggestion Engine**
- AccommodationPredictor: heuristic rules engine mapping signals → accommodations
- 10 accommodation types: cognitive_simplification, tts_read_aloud, reduced_difficulty, hints_scaffolding, worked_examples, sentence_starters, template_responses, break_reminder, task_chunking, quiet_mode
- Dignity framing: "Would you like to try...?" (NEVER "You need...")
- Cold start: <5 sessions → reduce confidence by 0.3
- DB: accommodation_suggestion, accommodation_profile
- API: POST /api/v1/students/{id}/accommodations/{sid}/approve|reject
- AC: Rules map correctly. Cold start works. NEVER auto-activates.

**F-407: ZPD Adaptive Difficulty Engine**
- ZPDManager: +1 after 3 consecutive correct, -1 after 2 consecutive wrong
- Frustration ceiling: max 2 increases without confirmed success
- Dignity messages for each transition (increase/decrease/maintain/ceiling)
- ZPDLevel model: level 1-10, consecutive_correct/incorrect, frustration counter
- AC: Algorithm correct. Ceiling prevents over-challenge. Messages use growth language.

**F-408: Teacher Insights Dashboard**
- InsightsPanel: pending suggestions with approve/reject, dignity message preview
- ZPDHistoryGraph: ZPD level over time (Recharts AreaChart)
- AC: Suggestions visible. Approve/reject works. History renders.

**F-409: Student Accommodation Prompt**
- AccommodationPrompt: non-intrusive, dismissible, accessible, never blocks content
- Dignity framing in both UI AND agent prompts
- Tutor agent receives accommodation context in prompt
- AC: Prompts non-blocking. Dignity language. Agent adapts responses.

**F-410: accommodation-predictor Skill**
- SKILL.md; metadata: framework=Vygotsky ZPD, privacy=FERPA LGPD compliant
- AccessibilityPolicy: add to all disability profiles
- AC: Skill loads. Policy routes for all profiles.

**F-411: Privacy & Compliance Layer**
- Telemetry retained 30 days max, then aggregated
- Pseudonymized student_id (internal UUID, never PII)
- Parent/guardian consent opt-in for behavioral tracking
- DELETE endpoint: purge all telemetry + suggestions + profile
- API: DELETE /api/v1/students/{id}/telemetry
- AC: Retention enforced. Consent required. Erasure works.

---

## New Infrastructure

### Agents (2)
1. SocialStoryAgent — anthropic:claude-opus-4-6, SocialStoryDraft output
2. SimplificationAgent — anthropic:claude-sonnet-4-6, CognitiveSimplificationResult output

### Skills (3)
1. social-story-generator — Carol Gray methodology
2. cognitive-simplifier — 4-level readability
3. accommodation-predictor — Vygotsky ZPD

### LangGraph Workflows (1)
1. social_story_workflow — skills → generate → validate → decision → export → scorecard

### Database Tables (5)
1. scenario_template — Social Story templates
2. social_story — Generated stories
3. student_telemetry — Behavioral events (partitioned)
4. accommodation_suggestion — Teacher-approved suggestions
5. accommodation_profile — Current active accommodations

### API Endpoints (14)
Social Stories: GET templates, GET template/{id}, POST generate (SSE), GET/{id}, PUT/{id}, POST/{id}/approve, POST/{id}/export/{fmt}
Simplification: POST analyze, POST simplify, GET simplify/{id}, PUT students/{id}/reading-level
Accommodations: POST telemetry/events, GET students/{id}/signals, POST approve/reject

---

## Dependencies
- Sprint 29 Design System for component styling
- Sprint 30 F-315 (PII encryption) for student_telemetry data protection
- Existing ElevenLabs TTS adapter for Social Story audio export
- Existing SkillRegistry + AccessibilityPolicy for skill integration

## Risks
- F-394: LLM may struggle with mathematical ratios — deterministic validation catches violations
- F-401: Level 4 (Symbol-Supported) needs few-shot examples — risk of poor quality
- F-404: Telemetry volume may overwhelm Postgres — partition + Redis buffer mitigates
- F-407: ZPD over-accommodation → "learned helplessness" — fading strategy required

## Micro-tasks: ~60 (18 stories × ~3.3 tasks each)
