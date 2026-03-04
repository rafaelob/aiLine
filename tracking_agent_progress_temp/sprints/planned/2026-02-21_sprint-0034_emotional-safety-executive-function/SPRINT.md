# Sprint 34 — Emotional Safety & Executive Function Support

**Goal:** Close the accommodation-to-empowerment gap with trauma-informed emotional safety (SAMHSA 6 principles), 6-subsystem executive function support, safe failure patterns, and dignity-preserving celebrations. Transform AiLine from technically accessible to psychologically safe.

**Theme:** Empowerment Layer Pillar 1 — Psychological Safety. Architecture: Gemini-3.1-Pro (3 consultations). Framework: SAMHSA Trauma-Informed Care (6 principles adapted for EdTech).

**Duration:** 3 weeks | **Status:** planned

---

## Acceptance Criteria
- [ ] Emotional check-in (energy/pleasantness grid, not facial emojis) at natural break points
- [ ] Frustration detection (rage clicks, idle, accuracy drops) with gentle de-escalation
- [ ] Task decomposition ("Stepping Stones" SVG path, not progress bars) for ADHD/executive dysfunction
- [ ] "Where was I?" working memory restoration (scroll position, active task, instruction context)
- [ ] "Just Start" initiation support (single action button, sentence starters, "Watch Me First")
- [ ] Transition warnings (2-min, `aria-live="assertive"`) for ASD
- [ ] Safe feedback: amber (never red) for learning feedback; no "wrong" language
- [ ] Global undo + auto-save indicator visible at all times
- [ ] Per-persona celebration rules enforced (TEA: text-only, ADHD: short, no confetti)
- [ ] Self-assessment emoji scale + end-of-session reflection
- [ ] Asset-based parent reports (no deficit language)
- [ ] All persona themes render correctly; all new components WCAG AA
- [ ] 6 new Zustand stores operational; 12 new DB tables created

---

## Stories (F-376 → F-393) — 18 stories, 4 phases

### Phase 1 — Emotional Safety Foundation (P0)

**F-376: Transition Warnings (ASD Critical)**
- TransitionWarningToast (2-min before activity change), VisualScheduleBar
- "Not Ready" extension button; `aria-live="assertive"` (ONLY exception to polite rule)
- DB: session_schedules; API: GET /api/v1/sessions/{id}/schedule
- AC: Toast appears 120s before. Extension button works. TEA theme: no animation, text-only.

**F-377: Task Decomposition ("Stepping Stones")**
- TaskPath SVG with stepping stone nodes (NOT progress bar); MicroTaskNode
- AI decomposes session into 5-7 micro-tasks; `aria-current="step"` on active
- DB: micro_tasks; API: POST /api/v1/sessions/{id}/decompose
- Store: useExecutiveStore; Animation: @keyframes dash-flow (disabled in reduced-motion)
- AC: AI decomposes. SVG path renders. Screen reader announces "Step N of M".

**F-378: Safe Feedback (No Red for Learning)**
- --color-feedback-safe (#F59E0B amber) replaces --color-error for student answers
- SafeFeedbackBoundary wraps all student inputs; HintOverlay for coaching
- `aria-describedby` for coaching text instead of `aria-invalid="true"`
- AC: Zero red for student answers. "Wrong" word banned. Growth language in microcopy.

**F-379: Global Undo + Auto-Save**
- GlobalOopsButton (Ctrl+Z), AutoSaveIndicator ("Your work is saved"), VersionHistoryPanel
- useHistoryStore with time-travel (past/present/future); debounced auto-save
- DB: session_drafts; API: PUT /api/v1/sessions/{id}/draft, GET /api/v1/sessions/{id}/history
- AC: Ctrl+Z works everywhere. Checkmark visible. Version comparison works.

### Phase 2 — Executive Function Support (P0)

**F-380: Working Memory Support ("Where was I?")**
- ContextPanel (always visible: objective + current instruction), ReturnToTaskButton
- useWorkingMemoryStore: captures/restores scroll position, active task, context
- API: PUT /api/v1/sessions/{id}/context-snapshot
- AC: Button restores exact state. `aria-live="polite"` on context. Keyboard shortcut.

**F-381: Initiation Support ("Just Start")**
- JustStartButton (single prominent action), SentenceStarterList, WatchMeFirstModal
- AI demonstrates task before student attempts
- DB: scaffolding_templates; API: POST /api/v1/tutor/demonstrate
- AC: One-click start. Sentence starters for writing. Modal accessible.

**F-382: Emotional Check-In (Mood Widget)**
- MoodCheckInWidget at natural break points; energy/pleasantness grid (NOT face emojis)
- useEmotionalSafetyStore: energyLevel, pleasantness, distressFlags, activeIntervention
- API: POST /api/v1/check-ins/mood
- AC: Appears between modules. Optional (dismissible). Culturally neutral.

**F-383: Frustration Detection + De-Escalation**
- FrustrationDetector (headless: rage clicks, idle, accuracy drops, deletions)
- DeEscalationOverlay (dims surroundings, calming colors, breathing animation)
- InterventionPrompt: gentle, non-blocking; useRegulationStore
- DB: frustration_events; API: POST /api/v1/analytics/frustration-events
- AC: Detection works (3+ rage clicks, 60s idle, 30% accuracy drop). Not blocking.

**F-384: Breathing Exercise**
- BoxBreathingVisualizer (expand/hold/contract circle); accessible via "Breathe" button
- Pure frontend (no backend needed); CSS animated circle
- `aria-live="polite"` announcing phases: "Breathe in for 4 seconds..."
- AC: 4-4-4-4 box breathing. Circle animates. Reduced-motion: text instructions only.

**F-385: Parking Lot (Distracting Thoughts)**
- ParkingLotSidebar: add/remove notes; persisted to backend
- useRegulationStore.parkedThoughts; `aria-expanded` on drawer
- DB: parking_lot_notes; API: POST /api/v1/parking-lot
- AC: Sidebar drawer opens. Notes persist across sessions. ADHD persona: always visible.

### Phase 3 — Safe Failure & Growth Mindset (P1)

**F-386: Productive Struggle Indicator**
- ProductiveStruggleIndicator ("Growing brain" visual); TutorInterventionCard
- useStruggleStore: consecutiveMisses, inStruggleZone
- After 3+ fails: tutor normalizes + offers alternative (NEVER auto-reduces difficulty)
- API: POST /api/v1/tutor/struggle-intervention
- DB: student_struggle_events
- AC: Zone indicator shows at 3+ misses. Tutor uses growth language.

**F-387: Dignity-Preserving Celebrations**
- MicroCelebrationRing (subtle expanding ring), MilestoneStar, StreakBanner
- Per-persona rules: TEA=text-only/NEVER confetti, ADHD=short/0.3s, Hearing=visual-only
- Modify use-confetti.ts: gate by persona theme, not just reducedMotion
- DB: student_streaks; API: GET /api/v1/students/{id}/streaks
- AC: Rules enforced per persona. No surprise animations for ASD.

**F-388: Self-Assessment & Reflection**
- ConfidenceEmojiScale (emoji-based, NOT numeric); EndSessionReflection
- `role="radiogroup"` with labeled options ("Feeling very confident" → "Need more practice")
- DB: self_assessments; API: POST /api/v1/assessments/self-reflection
- AC: Scale accessible. Data visible to teacher. Growth-oriented framing.

### Phase 4 — Reports & Portfolio (P2)

**F-389: Asset-Based Parent Reports**
- GrowthReportCard with LLM-enforced language constraints
- Replace "struggles with X" → "is developing strategies for X"
- Include 1 actionable at-home support item; celebrate non-academic growth
- DB: asset_based_reports; API: POST /api/v1/reports/generate-asset-based
- AC: Zero deficit language. Actionable tips. Non-academic wins celebrated.

**F-390: Growth Portfolio**
- GrowthPortfolioView: side-by-side comparison of early vs recent work
- Growth narrative generated by AI; student controls visibility
- API: GET /api/v1/students/{id}/portfolio
- AC: Comparison renders. Narrative encouraging. Student agency over sharing.

**F-391: useEmotionalSafetyStore (Full Integration)**
- Consolidate all emotional safety state: mood, distress flags, interventions, parked thoughts
- Integration with accessibility-store.ts (persona-gated behaviors)
- AC: Single store coordinates all emotional safety features. No state conflicts.

**F-392: Executive Function i18n**
- All executive function components fully localized (EN, PT-BR, ES)
- 40+ new i18n keys: ef.tasks.*, ef.memory.*, ef.time.*, ef.initiate.*, ef.regulate.*, ef.transition.*
- AC: All 3 locales render correctly. Diacritics preserved.

**F-393: Emotional Safety Test Suite**
- Unit tests for all 6 stores; integration tests for detection algorithms
- E2E: frustration detection flow, breathing exercise, undo system
- AC: ≥85% coverage on new emotional safety code.

---

## New Infrastructure

### Database Tables (12)
1. micro_tasks — session decomposition
2. session_drafts — undo/auto-save
3. session_schedules — transition support
4. scaffolding_templates — initiation support
5. frustration_events — behavioral analytics
6. parking_lot_notes — thought parking
7. student_struggle_events — struggle tracking
8. student_streaks — celebration data
9. self_assessments — reflection data
10. asset_based_reports — parent reports
11. learning_attempts — safe feedback analytics
12. task_time_logs — time perception

### Zustand Stores (6+)
1. useEmotionalSafetyStore — mood, distress, interventions
2. useExecutiveStore — task decomposition
3. useWorkingMemoryStore — context persistence
4. useRegulationStore — frustration, parking lot
5. useStruggleStore — consecutive misses
6. useHistoryStore — undo/redo time-travel
7. useTransitionStore — upcoming activity warnings

### API Endpoints (15)
POST /api/v1/sessions/{id}/decompose, PUT /api/v1/sessions/{id}/context-snapshot, PUT /api/v1/sessions/{id}/draft, GET /api/v1/sessions/{id}/history, GET /api/v1/sessions/{id}/schedule, POST /api/v1/check-ins/mood, POST /api/v1/analytics/frustration-events, POST /api/v1/tutor/demonstrate, POST /api/v1/tutor/struggle-intervention, POST /api/v1/assessments/self-reflection, POST /api/v1/reports/generate-asset-based, GET /api/v1/students/{id}/streaks, GET /api/v1/students/{id}/portfolio, POST /api/v1/parking-lot, GET /api/v1/analytics/time-estimates/{task_type}

### CSS Changes
- Add --color-feedback-safe (#F59E0B) and --color-feedback-bg (#FFF8E1) to all 9 persona themes
- Gate celebration animations per persona
- Remove --color-error from all student-facing contexts

---

## Dependencies
- Sprint 29 Design System should complete first (persona themes, CSS tokens)
- F-377 (Task Decomposition) depends on tutor agent for AI decomposition
- F-389 (Parent Reports) depends on Sprint 33+ F-356 (Learning Rhythm) for streak data
- Independent of Sprint 30 (backend) — pure frontend + thin API layer

## Risks
- F-383 (Frustration Detection): False positive rate — tuning thresholds per persona
- F-378 (Safe Feedback): CSS token migration may break existing error states
- F-387 (Celebrations): Persona-gated confetti requires modifying existing use-confetti hook

## Micro-tasks: ~60 (18 stories × ~3.3 tasks each)
