# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints (S0-28)

All 29 sprints COMPLETED. 271 features (F-001 through F-271). 3,889 tests (2,451 runtime + 1,438 frontend). 0 lint/type errors. Docker 4 services healthy. See FEATURES.md for per-sprint detail.

---

## Sprint 29 — Design System, SVG Illustrations, Core Views & Emotional UX ("Soft Clay") — PLANNED

39 stories (F-272 → F-310). HIGHEST PRIORITY. 3 weeks.
Design: "Soft Clay 2.5D Organic" (Gemini-3.1-Pro, 6 consultations). Benchmarks: Khan Academy, Duolingo, Seesaw.
Sources: 2 agent rounds (7 agents), competitive analysis (8 platforms), purpose analysis (10 gaps).

### Phase 1 — Design System Foundation (P0)
- [ ] F-272: Modularize globals.css → token files (<400 LOC each)
- [ ] F-273: tailwind-variants + UI primitives (Button, Input, Dialog, Card, Badge, ActionButton w/ loading states)
- [ ] F-274: lucide-react icons (zero inline SVGs)
- [ ] F-275: Inter + Plus Jakarta Sans typography (base 18px)
- [ ] F-276: Azure #1E4ED8 / Sage #10B981 / Amber #F59E0B palette (WCAG AAA verified)
- [ ] F-277: useMotionConfig hook (centralized persona animation control)
- [ ] F-278: "Soft Clay" aesthetic (solid surfaces, 20px radius, ambient shadows, pill CTAs)

### Phase 2 — SVG Illustration System (P0)
- [ ] F-279: IllustrationBase component + ClayFilterProvider architecture
- [ ] F-280: 6 empty state illustrations (Gemini-generated, CSS custom properties, accessible)
- [ ] F-281: 5 onboarding step illustrations (Gemini-generated)
- [ ] F-282: Landing hero + 4 "How It Works" illustrations (Gemini-generated)
- [ ] F-283: 6 persona avatars + 8 a11y profile icons + 8 subject icons
- [ ] F-284: 5 error/status illustrations (404, 500, Offline, Loading, Success)

### Phase 3 — Core Missing Views (P0-CRITICAL)
- [ ] F-285: Learning Analytics Dashboard (teacher mastery view, BarChart+AreaChart+sparklines)
- [ ] F-286: Student Learning View (/(app)/learn/[planId], mastery map, per-persona adaptations)
- [ ] F-287: Parent Progress Report (/(app)/parent-report, "Stepping Stones", conversation starters)
- [ ] F-288: Recharts a11y infra (PatternDefs, AccessibleTooltip, 56px motor hit-areas)

### Phase 4 — Page Redesigns & Responsive (P1)
- [ ] F-289: Landing page "Soft Clay" redesign (hero illustration, ScrollReveal, scroll-snap testimonials)
- [ ] F-290: Teacher dashboard 12-col grid (bento stats, analytics integration)
- [ ] F-291: Tablet breakpoint md:768px (off-canvas sidebar, Master-Detail)
- [ ] F-292: Standard dark theme (prefers-color-scheme + toggle)
- [ ] F-293: Multi-step teacher onboarding (5 steps with SVG illustrations)

### Phase 5 — Emotional Safety & A11y Innovation (P0-P1)
- [ ] F-294: Neutral error states (trauma-informed: no red X, encouraging microcopy)
- [ ] F-295: Visual Pie-Chart Timer (ADHD time blindness, not numeric countdown)
- [ ] F-296: "Quiet Mode" toggle (grayscale, no animations, no social — sensory processing)
- [ ] F-297: Empty states with SVG illustrations + encouraging microcopy + CTA
- [ ] F-298: ADHD Reading Ruler + Executive Function Support (chunking, Pacing Bar, checklists)
- [ ] F-299: Dyslexia alternating rows + font enhancements

### Phase 6 — Engagement Foundation (P2)
- [ ] F-300: Drag-and-drop plan reorder (motion Reorder, keyboard a11y)
- [ ] F-301: ScrollReveal + micro-interactions kit
- [ ] F-302: PWA foundation (@serwist/next, offline read-only, InstallPrompt)
- [ ] F-303: "Learning Rhythm" forgiving gamification (no anxiety triggers)
- [ ] F-304: Celebration pattern evolution (subtle ring, no confetti)
- [ ] F-305: Persona explainer + improved a11y status

### Stretch Goals (if time permits)
- [ ] F-306: "Constellation" curriculum map (SVG night-sky)
- [ ] F-307: Push notifications (Web Push API)
- [ ] F-308: Multimodal student responses (voice, drawing, photo)
- [ ] F-309: Classroom Constellation (cooperative social learning)
- [ ] F-310: Digital Transition Passport (Self-Advocacy Card export)

---

## Sprint 30 — Backend Production, Observability & Compliance — PLANNED

20 stories (F-311 → F-330). 2-3 weeks.
Architecture: GPT-5.3-codex (3 consultations). GDPR/LGPD verified against ANPD Resolucao 15/2024.

### Phase 1 — Critical Fixes (P0, Day 1)
- [ ] F-311: GEMINI_API_KEY env var fix (config.py AliasChoices + 8 doc files)
- [ ] F-312: PII redaction in logs (structlog processor, zero student PII in output)
- [ ] F-313: Google paid-service guard (block free Gemini for student data per ToS)

### Phase 2 — Compliance & Security (P0)
- [ ] F-314: Persistent audit log (FERPA/LGPD), migration 0005, admin query endpoint
- [ ] F-315: PII encryption at rest (Fernet/AES-256, key rotation)

### Phase 3 — Observability Stack (P0-P1)
- [ ] F-316: OTEL Redis instrumentation (spans, no PII in attributes)
- [ ] F-317: Trace-ID log correlation (structlog + OTel span injection)
- [ ] F-318: LLM call baggage propagation (student_id, plan_id, agent_name across calls)

### Phase 4 — Resilience & Reliability (P1)
- [ ] F-319: Redis-backed distributed IdempotencyGuard
- [ ] F-320: SmartRouter cross-tier fallback (primary → middle → cheap)
- [ ] F-321: SSE backpressure (bounded Queue, stream.gap notification)
- [ ] F-322: Lifecycle state + graceful shutdown (STARTING→READY→DRAINING→STOPPED)
- [ ] F-323: K8s-style health probes (live/ready/startup, migration check, LLM probe)

### Phase 5 — Refactoring (P1)
- [ ] F-324: Split app.py (709 → ~4 modules <300 LOC each)
- [ ] F-325: Split auth.py (654 → auth_service + thin router)
- [ ] F-326: Split models.py (646 → per-domain: core/materials/pipeline/rbac/skills)
- [ ] F-327: Remove deprecated AiLineConfig (single config system)

### Phase 6 — CI/CD (P2)
- [ ] F-328: Docker Compose integration test CI job (real Postgres + Redis)
- [ ] F-329: E2E Playwright CI job (8 specs, screenshots archived)
- [ ] F-330: Consolidate /skills vs /v1/skills (301 redirect)

---

## Sprint 31 — Architecture Evolution & Agent Maturity — PLANNED

15 stories (F-331 → F-345). 2-3 weeks.

### Phase 1 — Application Layer (P1)
- [ ] F-331: Application Service Layer (Commands/Queries, 3 handlers)
- [ ] F-332: Domain Events Infrastructure (5 event types, 3 async handlers)
- [ ] F-333: Background Job Processing (arq worker Docker service)

### Phase 2 — API Maturity (P1)
- [ ] F-334: API versioning (/v1/, X-API-Version header, 301 redirects)
- [ ] F-335: Cursor-based pagination (CursorPage[T], Link headers)
- [ ] F-336: Consolidate skills routers

### Phase 3 — Agent Production Maturity (P1-P2)
- [ ] F-337: Prompt version registry (DB, activate/rollback, A/B split)
- [ ] F-338: Per-tenant cost tracking (usage_events, budget alerts)
- [ ] F-339: Content safety guardrails (age-appropriate, bias-free, PII scrub)
- [ ] F-340: Semantic AI caching (Redis, prompt-hash keys, invalidation)

### Phase 4 — Data Layer & Cleanup (P2)
- [ ] F-341: PostgreSQL-backed persistent stores (4 stores, auto-cleanup)
- [ ] F-342: Embedding dimension fix (align to 1536, startup validation)
- [ ] F-343: Unified InMemoryStore[K,V] base (TTL, max_size, LRU)
- [ ] F-344: Expose session_factory on PgVectorStore
- [ ] F-345: Document/refactor 14 global mutable state instances

---

## Sprint 32A — Privacy Compliance (LGPD/GDPR) — PLANNED

10 stories (F-346 → F-355). 2 weeks.

- [ ] F-346: Data tier classification + ORM tagging (CI enforcement)
- [ ] F-347: Data portability export API (LGPD Art. 18, ZIP archive)
- [ ] F-348: Deletion & anonymization pipeline (soft→hard delete, legal hold)
- [ ] F-349: Minor consent management (LGPD Art. 14, guardian verification)
- [ ] F-350: Retention policy engine (automated cleanup, execution logs)
- [ ] F-351: Incident response playbook (ANPD 3d / GDPR 72h templates)
- [ ] F-352: Provider DPA register + runtime guards
- [ ] F-353: Redis maxmemory eviction safety (separate logical DBs)
- [ ] F-354: Postgres RLS foundation (tenant_id policies)
- [ ] F-355: Notification service foundation (email, in-app SSE, Web Push)

---

## Sprint 33+ — Advanced Features — PLANNED

20 stories (F-356 → F-375). 4-6 weeks.

### Gamification & Engagement
- [ ] F-356: "Learning Rhythm" backend (forgiving momentum, streak freeze)
- [ ] F-357: "Skill Nodes" achievement system (geometric badges, non-academic wins)
- [ ] F-358: "Constellation" curriculum map (frontend+backend, SVG night-sky)

### Educational Intelligence
- [ ] F-359: Spaced repetition scheduler (SM-2 adapted for inclusive learning)
- [ ] F-360: IEP goal tracking schema (goals, accommodations, progress)
- [ ] F-361: AI Social Story Generator (ASD, scenario→5-step illustrated story)
- [ ] F-362: Predictive accommodation suggestions (usage patterns → teacher approval)
- [ ] F-363: Cognitive simplification engine (reading level slider, Flesch-Kincaid)

### Platform Evolution
- [ ] F-364: Feature flags system (Redis, per-tenant)
- [ ] F-365: CQRS read models (materialized views, 10x dashboard)
- [ ] F-366: Agent A/B testing framework
- [ ] F-367: Personalization engine (mastery tracking, gap analysis, recommendations)

### Infrastructure & Quality
- [ ] F-368: Search engine (Meilisearch for materials/plans)
- [ ] F-369: API SDK generation (OpenAPI → TypeScript client)
- [ ] F-370: Admin dashboard API (monitoring, user management)
- [ ] F-371: Batch operations API (bulk import, bulk generation)
- [ ] F-372: Webhook system (LMS: Canvas/Moodle, HMAC-SHA256)
- [ ] F-373: Git LFS for binary media (~15MB)
- [ ] F-374: Clean orphaned root files
- [ ] F-375: Real assistive technology testing (axe-core + NVDA/VoiceOver CI)

---

## Sprint 34 — Emotional Safety & Executive Function — PLANNED

18 stories (F-376 → F-393). 3 weeks. Empowerment Layer Pillar 1.
Framework: SAMHSA Trauma-Informed Care. Architecture: Gemini-3.1-Pro (3 consultations).
Sources: 3-round Gemini debate (emotional-safety-architect), purpose analysis (10 gaps).

### Phase 1 — Emotional Safety Foundation (P0)
- [ ] F-376: Transition Warnings (ASD, 2-min, aria-live="assertive", VisualScheduleBar)
- [ ] F-377: Task Decomposition "Stepping Stones" (SVG path, 5-7 micro-tasks, aria-current)
- [ ] F-378: Safe Feedback — no red for learning (amber --color-feedback-safe, growth language)
- [ ] F-379: Global Undo + Auto-Save (Ctrl+Z, VersionHistoryPanel, session_drafts)

### Phase 2 — Executive Function Support (P0)
- [ ] F-380: Working Memory "Where was I?" (ContextPanel, context-snapshot API)
- [ ] F-381: Initiation "Just Start" (JustStartButton, SentenceStarters, WatchMeFirst)
- [ ] F-382: Emotional Check-In (energy/pleasantness grid, mood widget, not face emojis)
- [ ] F-383: Frustration Detection + De-Escalation (rage clicks, idle, accuracy drops)
- [ ] F-384: Breathing Exercise (BoxBreathingVisualizer, 4-4-4-4 cycle)
- [ ] F-385: Parking Lot (distracting thoughts sidebar, persisted)

### Phase 3 — Safe Failure & Growth Mindset (P1)
- [ ] F-386: Productive Struggle Indicator (3+ fails → normalize, never auto-reduce)
- [ ] F-387: Dignity-Preserving Celebrations (per-persona: TEA=text-only, ADHD=short)
- [ ] F-388: Self-Assessment (confidence emoji scale, end-session reflection)

### Phase 4 — Reports & Portfolio (P2)
- [ ] F-389: Asset-Based Parent Reports (no deficit language, LLM constraints)
- [ ] F-390: Growth Portfolio (early vs recent work comparison)
- [ ] F-391: useEmotionalSafetyStore full integration (6+ stores consolidated)
- [ ] F-392: Executive Function i18n (40+ keys, EN/PT-BR/ES)
- [ ] F-393: Emotional Safety test suite (≥85% coverage)

---

## Sprint 35 — AI Educational Intelligence Tools — PLANNED

18 stories (F-394 → F-411). 3 weeks. Empowerment Layer Pillar 2.
Frameworks: Carol Gray Social Stories, Flesch-Kincaid, Vygotsky ZPD. Architecture: Gemini-3.1-Pro (3 consultations).

### Phase 1 — Social Story Generator (P0)
- [ ] F-394: SocialStoryAgent + deterministic 4:1 ratio QualityGate (Carol Gray)
- [ ] F-395: Scenario Template Library (10 templates, DB-backed, locale-aware)
- [ ] F-396: Social Story multi-format export (text, audio, visual, PDF, cards)
- [ ] F-397: Social Story Student Viewer (swipeable cards, TTS per card)
- [ ] F-398: social_story_workflow LangGraph (skills→generate→validate→export→scorecard)
- [ ] F-399: social-story-generator skill (agentskills.io spec, AccessibilityPolicy update)

### Phase 2 — Cognitive Simplification Engine (P0-P1)
- [ ] F-400: Readability Analysis Module (Flesch-Kincaid, Gunning Fog, deterministic)
- [ ] F-401: Multi-Level SimplificationAgent (4 levels, jargon tooltips, objectives preserved)
- [ ] F-402: Complexity Slider UI (1-4 levels, real-time, DiffHighlighter)
- [ ] F-403: cognitive-simplifier skill + plan_workflow/tutor_workflow integration

### Phase 3 — Predictive Accommodations + ZPD (P1)
- [ ] F-404: Telemetry Ingestion Pipeline (7 signal types, partitioned, Redis buffer)
- [ ] F-405: BehavioralAnalyzer Service (rolling windows, normalized 0-1 signals)
- [ ] F-406: Accommodation Suggestion Engine (heuristic rules, dignity framing, NEVER auto-activate)
- [ ] F-407: ZPD Adaptive Difficulty (+1 after 3 correct, -1 after 2 wrong, frustration ceiling)
- [ ] F-408: Teacher Insights Dashboard (approve/reject suggestions, ZPD history graph)
- [ ] F-409: Student Accommodation Prompt (non-intrusive, dismissible, dignity-framed)
- [ ] F-410: accommodation-predictor skill (Vygotsky ZPD, FERPA/LGPD compliant)
- [ ] F-411: Privacy & Compliance (30d telemetry retention, consent, erasure endpoint)

---

## Sprint 36 — IEP/MTSS, SM-2 Spaced Repetition, Mastery & Personalization — PLANNED

36 stories (F-412 → F-447). 4-6 weeks. Empowerment Layer Pillar 3.
Architecture: GPT-5.3-codex (2 consultations) + GPT-5.2 thinkdeep. Compliance: IDEA, FERPA, LGPD Art. 14.

### Phase 1 — IEP Document Management (P0)
- [ ] F-412: IEP Document CRUD + status lifecycle (7 states, audit trail)
- [ ] F-413: IEP SMART Goals (linked to curriculum standards, progress %)
- [ ] F-414: IEP Accommodations (6 categories, active/inactive, dates)
- [ ] F-415: IEP Progress Monitoring (datapoints, evidence types, timeline)
- [ ] F-416: IEP Services Tracking (8 service types, frequency, provider)
- [ ] F-417: IEP Team & Notifications (roles, channels, read tracking)
- [ ] F-418: IEP domain entities + PostgresIepRepository

### Phase 2 — MTSS Tier Management (P0)
- [ ] F-419: MTSS Tier Placement (Tier 1/2/3, subject, dates, movement)
- [ ] F-420: MTSS Intervention Catalog (evidence-based, per-org, 4 evidence levels)
- [ ] F-421: MTSS Student Interventions + fidelity tracking
- [ ] F-422: MTSS Screening + Meetings (tools, decisions, next review)
- [ ] F-423: MTSS domain entities + PostgresMtssRepository

### Phase 3 — Compliance & Audit (P0)
- [ ] F-424: Consent Management (6 types, IDEA + LGPD Art. 14, withdrawal)
- [ ] F-425: Immutable Audit Ledger (append-only, SHA-256 state hashes)
- [ ] F-426: Data Retention Policies (IEP 7yr, MTSS 5yr, reviews 3yr, legal hold)

### Phase 4 — SM-2 Spaced Repetition (P1)
- [ ] F-427: Review Items CRUD (7 modalities, difficulty, curriculum-linked)
- [ ] F-428: Student Review Profiles (processing speed matrix, fatigue sensitivity)
- [ ] F-429: SM-2 Core Algorithm (EF update + processing speed factor + calibration)
- [ ] F-430: Processing Speed Matrix (7 needs × 7 modalities = 49 multipliers)
- [ ] F-431: Review Outcome Recording (quality 0-5, growth feedback, EF snapshots)
- [ ] F-432: Fatigue Detection (3 rules: declining quality, low average, overtime)
- [ ] F-433: Due Reviews + Review Sessions (priority ordering, session stats)
- [ ] F-434: Review Health Dashboard (aggregated stats, calibration status)
- [ ] F-435: Tutor Review Integration (review_check_node, SSE events)

### Phase 5 — Mastery + Personalization (P1-P2)
- [ ] F-436: Mastery Map (5 levels, ZPD bounds, prerequisite graph)
- [ ] F-437: Mastery Evidence Collection (5 sources, normalized 0-1)
- [ ] F-438: Skill Gap Analysis (prerequisite traversal, ZPD-aware)
- [ ] F-439: Learning Profile Construction (auto-detected preferences, effectiveness)
- [ ] F-440: AI Recommendations Engine (5 types, heuristic-first, teacher approval)
- [ ] F-441: Recommendation Acceptance Flow (accept/dismiss, feedback loop)
- [ ] F-442: ZPD-Mastery Integration (bounds populate, difficulty matching)
- [ ] F-443: Parent IEP Progress Report (unified view, asset-based language)
- [ ] F-444: Teacher IEP Dashboard (caseload overview, Recharts visualizations)
- [ ] F-445: Review Auto-Generation from Mastery (proficient → review item)
- [ ] F-446: Data Retention Enforcement (arq job, anonymization, legal holds)
- [ ] F-447: Privacy Dashboard (consent coverage, retention compliance, audit)

---

## Backlog (unscheduled)
- [ ] F-035: Sign Language Post-MVP — SPOTER transformer + VLibrasBD NMT
- [ ] F-178: Teacher Skill Sets — per-teacher presets
- [ ] Braille Grade 2 via liblouis
- [ ] SW multi-locale caching for PWA
- [ ] Symbol-Supported Text (PCS pictograms for intellectual disabilities)
- [ ] Synchronized word-level TTS highlighting (Kurzweil-style)
- [ ] Haptic/Vibrational feedback (Web Haptics API)
