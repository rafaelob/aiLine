# Sprint 36 — IEP/MTSS Compliance, SM-2 Spaced Repetition, Mastery & Personalization

**Goal:** Build the educational data intelligence backbone: IEP/MTSS compliance (IDEA + LGPD Art. 14), inclusive SM-2 spaced repetition with processing speed adaptation, mastery tracking with evidence-based progression, and heuristic-first personalization engine. This is the data layer that feeds empowerment decisions.

**Theme:** Empowerment Layer Pillar 3 — Educational Data Intelligence. Architecture: GPT-5.3-codex (2 consultations) + GPT-5.2 thinkdeep. Compliance: US IDEA, FERPA, Brazilian LGPD Art. 14.

**Duration:** 4-6 weeks (3 sub-phases) | **Status:** planned

---

## Acceptance Criteria
- [ ] Complete IEP document lifecycle (draft→submitted→approved→active→review→archived)
- [ ] SMART goals linked to curriculum standards with progress monitoring
- [ ] 6 accommodation categories with active/inactive management
- [ ] MTSS 3-tier system with evidence-based intervention catalog
- [ ] Tier movement requires meeting decisions with audit trail
- [ ] Guardian consent management (IDEA + LGPD Art. 14) with withdrawal support
- [ ] Immutable audit ledger (append-only, SHA-256 state hashes)
- [ ] SM-2 algorithm with processing speed multipliers per accessibility need + modality
- [ ] Calibration period (first 5 reviews, cap 3 days) prevents premature profiling
- [ ] Cognitive fatigue detection (3 rules) with gentle session ending
- [ ] Mastery map per student with 5 levels + evidence collection from 5 sources
- [ ] Skill gap analysis from prerequisite graph + mastery data
- [ ] Learning profiles with detected preferences, strengths, challenges
- [ ] AI recommendation engine with teacher approval workflow
- [ ] 24 new DB tables, 38 new API endpoints, 1 migration (0006)

---

## Stories (F-412 → F-447) — 36 stories, 5 phases

### Phase 1 — IEP Document Management (P0, 7 stories)

**F-412: IEP Document CRUD + Status Lifecycle**
- iep_documents table with full lifecycle (IepStatus enum: 7 states)
- Composite FK (teacher_id, student_id) → teacher_students for tenant isolation
- Status transitions: only valid paths allowed; each creates audit_ledger entry
- Review date auto-set 365 days from approval
- API: POST/GET/PATCH /api/v1/iep, PATCH /api/v1/iep/{id}/status
- AC: CRUD works. Invalid transitions rejected. Audit entries created.

**F-413: IEP SMART Goals**
- iep_goals linked to curriculum_objectives.code (optional)
- GoalStatus: not_started → in_progress → meeting_expectations → achieved/discontinued
- Measurable objective, baseline, target criteria, measurement method, target date
- API: POST/PATCH /api/v1/iep/{id}/goals
- AC: Goals linked to standards. Progress percentage auto-calculated.

**F-414: IEP Accommodations Catalog**
- 6 AccommodationCategory: environmental, instructional, assessment, behavioral, technological, communication
- Active/inactive toggle with start/end dates; metadata for AT device details
- API: POST /api/v1/iep/{id}/accommodations
- AC: All 6 categories available. Toggle works. Dates enforced.

**F-415: IEP Progress Monitoring**
- iep_progress_datapoints: measurement_value, unit, evidence_type (observation/work_sample/assessment/ai_generated)
- Evidence URL for uploaded files; optional tutor_session link
- Progress percentage recalculated on each datapoint
- API: POST /api/v1/iep/{id}/goals/{goal_id}/progress, GET /api/v1/iep/{id}/progress
- AC: Datapoints recorded. Evidence types tracked. Timeline renders.

**F-416: IEP Services Tracking**
- Related services: speech therapy, OT, PT, counseling, specialized instruction, behavioral support, AT, transition
- Frequency (minutes/period), provider, location
- API: POST /api/v1/iep/{id}/services
- AC: Service delivery documented. Active/inactive toggle. IDEA compliance.

**F-417: IEP Team & Notifications**
- iep_team_members: case_manager, specialist, parent, student, advocate roles
- iep_notifications: meeting_invite, progress_report, consent_request, status_change
- Channels: in_app, email (via Sprint 32A F-355 notification service)
- API: POST /api/v1/iep/{id}/notifications
- AC: Team assigned. Notifications sent. Read tracking works.

**F-418: IEP Domain Entities + Repository**
- Domain entities: IepDocument, IepGoal, IepAccommodation, IepService, IepProgressDatapoint, IepTeamMember
- Ports: IepRepository Protocol (8 methods)
- Adapter: PostgresIepRepository with tenant-aware queries
- AC: Repository passes integration tests. Tenant isolation verified.

### Phase 2 — MTSS Tier Management (P0, 5 stories)

**F-419: MTSS Tier Placement**
- mtss_tier_placements: Tier 1/2/3 by subject area with effective dates
- Partial index for current placements (WHERE end_date IS NULL)
- TierMovement: escalation/de_escalation/maintain with movement_reason
- API: POST/GET /api/v1/mtss/placements, PATCH /api/v1/mtss/placements/{id}/tier
- AC: Placement works. Tier change creates new row (end_date on previous). Audit trail.

**F-420: MTSS Intervention Catalog**
- mtss_interventions: evidence-based, per-organization, with evidence level (strong/moderate/promising/emerging)
- Recommended duration, frequency, materials
- API: POST/GET /api/v1/mtss/interventions
- AC: Catalog per org. Evidence levels enforced. Search works.

**F-421: MTSS Student Interventions + Fidelity**
- mtss_student_interventions: links placement → intervention with fidelity tracking
- Implementation fidelity score (0-100%), progress monitoring frequency
- API: POST /api/v1/mtss/student-interventions
- AC: Assigned to student. Fidelity tracked. Progress frequency configurable.

**F-422: MTSS Screening + Meetings**
- mtss_screening_results: tool, score, percentile, benchmark level
- mtss_meetings: attendees, decisions, next review date
- API: POST /api/v1/mtss/screenings, POST /api/v1/mtss/meetings
- AC: Screening data recorded. Meeting decisions linked to tier changes.

**F-423: MTSS Domain Entities + Repository**
- Domain entities: MtssTierPlacement, MtssIntervention, MtssStudentIntervention, MtssScreeningResult, MtssMeeting
- Ports: MtssRepository Protocol
- Adapter: PostgresMtssRepository
- AC: Repository integration tests pass. Tenant isolation verified.

### Phase 3 — Compliance & Audit (P0, 3 stories)

**F-424: Consent Management (IDEA + LGPD Art. 14)**
- consent_records: 6 ConsentType (initial_evaluation, reevaluation, services, data_processing, data_sharing, ai_processing)
- ConsentStatus lifecycle: pending → granted/denied, withdrawn, expired
- Policy version tracking; auto-trigger re-consent on policy changes
- API: POST/GET/PATCH /api/v1/compliance/consent
- AC: Consent captured before processing. Withdrawal works. Policy versioning.

**F-425: Immutable Audit Ledger**
- audit_ledger: append-only (NO UPDATE/DELETE at application level)
- SHA-256 before_hash/after_hash for tamper detection
- Every IEP/MTSS/consent operation writes audit entry
- API: GET /api/v1/compliance/audit/{resource_type}/{id}
- AC: Ledger immutable. Hashes correct. Queryable by admin.

**F-426: Data Retention Policies**
- data_retention_policies per category: IEP (7yr), MTSS (5yr), reviews (3yr), consent (indefinite), audit (indefinite)
- Legal hold support; anonymization on delete
- Scheduled cleanup job (arq worker)
- AC: Policies configured. Cleanup runs. Legal holds block deletion.

### Phase 4 — SM-2 Spaced Repetition (P1, 9 stories)

**F-427: Review Items CRUD**
- review_items: linked to curriculum_objectives or lessons; multiple modalities; difficulty level
- Modalities: visual_text, visual_image, audio, video, interactive, braille, sign_language
- API: POST/GET /api/v1/reviews/items
- AC: Items created. Modalities configured. Tenant isolated.

**F-428: Student Review Profiles**
- student_review_profiles: processing speed factors from accessibility needs + modality matrix
- Max items per session, preferred session minutes, fatigue sensitivity
- Auto-populated from student_profiles; teacher-editable
- API: GET/PATCH /api/v1/reviews/profile/{student_id}
- AC: Auto-populated. Matrix factors correct. Teacher overrides work.

**F-429: SM-2 Core Algorithm (Inclusive Adaptation)**
- SpacedRepetitionService (pure domain service): calculate_next_review()
- Standard SM-2 EF update + processing speed factor per accessibility need + modality
- Calibration period: first 5 reviews capped at 3-day intervals
- Streak bonus: 10% at 5+ consecutive correct
- Interval bounds: [0.5, 365] days
- AC: EF updates correctly. PSF applied. Calibration caps. Streak bonus at 5+.

**F-430: Processing Speed Matrix**
- 7 accessibility needs × 7 modalities = 49 multiplier values
- autism: 1.3x visual_text, 1.4x interactive; adhd: 0.7x visual_text; hearing: 1.8x audio
- Modality selection: prefer lowest PSF (easiest for student) among available
- AC: Matrix values configured. Modality selection optimal.

**F-431: Review Outcome Recording**
- review_outcomes: quality 0-5, response_time_ms, modality_used, accommodation snapshot
- EF/interval before/after snapshots for audit
- Growth-oriented feedback per quality level (dignity-framed messages)
- API: POST /api/v1/reviews/outcomes
- AC: Outcomes recorded. EF snapshots stored. Growth feedback displayed.

**F-432: Fatigue Detection**
- 3 rules: declining quality streak (3+), low average (<2.5), session overtime (>1.5x max)
- FatigueLevel: none → mild → moderate → high
- Moderate: suggest break. High: end session gently.
- AC: Rules detect correctly. Break suggested. Session ends gracefully.

**F-433: Due Reviews + Review Sessions**
- get_due_reviews(): ordered by overdue → weakest → hardest; configurable limit
- review_sessions: items reviewed/skipped/deferred, duration, fatigue level
- API: GET /api/v1/reviews/due/{student_id}, GET /api/v1/reviews/sessions/{student_id}
- AC: Due items prioritized correctly. Session stats tracked.

**F-434: Review Health Dashboard**
- Aggregated stats: total items, due today, overdue, avg quality, streak stats
- Calibration status, upcoming schedule visualization
- API: GET /api/v1/reviews/health/{student_id}
- AC: Stats accurate. Dashboard renders for teacher and parent.

**F-435: Tutor Review Integration**
- review_check_node in tutor_workflow (between start and route nodes)
- Check get_due_reviews(limit=3) at session start; inject into TutorGraphState
- Tutor weaves reviews naturally: "Before we dive in, let's revisit..."
- After each review, update schedule; check fatigue
- SSE events: review.due_items, review.outcome_recorded, review.session_completed
- AC: Tutor integrates reviews. Schedule updates in real-time. SSE events emitted.

### Phase 5 — Mastery + Personalization (P1-P2, 12 stories)

**F-436: Mastery Map**
- mastery_maps: per student + curriculum standard; 5 MasteryLevel states
- ZPD bounds (zpd_lower, zpd_upper) from Vygotsky framework
- Time-in-level tracking; prerequisite_codes for dependency graph
- API: GET /api/v1/mastery/{student_id}
- AC: Map renders. Levels update from evidence. ZPD bounds calculated.

**F-437: Mastery Evidence Collection**
- mastery_evidence: 5 sources (tutor_session, review_outcome, assessment, teacher_observation, ai_analysis)
- Normalized 0-1 score; source tracking with source_id
- Evidence triggers mastery level re-evaluation
- AC: Evidence from all 5 sources. Score normalized. Level updates.

**F-438: Skill Gap Analysis**
- Compare current mastery vs prerequisites (prerequisite graph traversal)
- Identify gaps: prerequisites mastered but current topic not
- ZPD integration: recommend topics at learning edge
- API: GET /api/v1/mastery/{student_id}/gaps
- AC: Gaps identified correctly. Prerequisites checked. ZPD-aware.

**F-439: Learning Profile Construction**
- learning_profiles: preferred style (detected from modality performance), engagement patterns, strengths/challenges
- Auto-detected from: session timing, modality completion rates, mastery data
- Accommodation effectiveness tracking (correlation with quality scores)
- API: GET /api/v1/personalization/{student_id}/profile
- AC: Profile auto-constructed. Preferences detected. Effectiveness tracked.

**F-440: AI Recommendations Engine**
- recommendations table: 5 types (next_topic, difficulty_adjust, resource_type, review_focus, accommodation_change)
- Heuristic-first rules engine (ML upgrade path after 10K+ labeled sessions)
- Confidence score; 90-day expiry; teacher approval required
- API: GET /api/v1/personalization/{student_id}/recommendations
- AC: Recommendations generated. Confidence scored. Teacher approves/dismisses.

**F-441: Recommendation Acceptance Flow**
- Accept/dismiss with reason; feedback loop into recommendation engine
- Accepted recommendations update student profile and accommodation_profile
- AC: Accept/dismiss works. Feedback stored. Profile updated.

**F-442: ZPD-Mastery Integration**
- zpd_lower and zpd_upper in mastery_maps from ai-tools ZPD engine
- Review item difficulty matched to ZPD range; items outside ZPD deprioritized
- AC: ZPD bounds populate. Difficulty matching works. Deprioritization correct.

**F-443: Parent IEP Progress Report**
- Unified view: IEP goal progress + review health + mastery map
- Read-only for parent (own child only via parent_students check)
- Asset-based language (from Sprint 34 F-389 patterns)
- AC: Report renders. Own-child only. Growth language.

**F-444: Teacher IEP Dashboard**
- Aggregated view: IEP count by status, MTSS tier distribution, overdue reviews, upcoming meetings
- React: IepDashboard component with Recharts visualizations
- AC: Dashboard renders. Data accurate. Filters work.

**F-445: Review Auto-Generation from Mastery**
- On mastery_level transition to "proficient"/"advanced", auto-create review_item
- AI generates question/answer from curriculum_objectives content
- Enters spaced repetition cycle automatically
- AC: Review items created on transition. AI generation works.

**F-446: Data Retention Enforcement**
- Scheduled arq job checks data_retention_policies
- Anonymizes expired records per category rules; legal holds exempt
- Audit trail of all deletions
- AC: Job runs. Records anonymized. Legal holds respected.

**F-447: Privacy Dashboard**
- School admin view: consent coverage, retention compliance, access audit summary
- Shows % students with required consents; recent access entries
- AC: Dashboard renders. Metrics accurate. Admin-only access.

---

## New Infrastructure

### Database Tables (24)
IEP (7): iep_documents, iep_goals, iep_accommodations, iep_services, iep_progress_datapoints, iep_team_members, iep_notifications
MTSS (5): mtss_tier_placements, mtss_interventions, mtss_student_interventions, mtss_screening_results, mtss_meetings
Compliance (3): consent_records, audit_ledger, data_retention_policies
SM-2 (5): review_items, review_schedules, review_outcomes, student_review_profiles, review_sessions
Mastery/Personalization (4): mastery_maps, mastery_evidence, learning_profiles, recommendations

### Migration: 0006_education_intelligence (single migration, all 24 tables)

### Domain Entities (6 files)
iep.py, mtss.py, compliance.py, review.py, mastery.py, personalization.py

### Repository Ports + Adapters (6 pairs)
IepRepository, MtssRepository, AuditRepository, ReviewRepository, MasteryRepository, PersonalizationRepository

### API Endpoints (38)
IEP: 12, MTSS: 10, Compliance: 4, SM-2: 8, Mastery/Personalization: 4

### Privacy Classification
RESTRICTED: iep_*, mtss_*, consent_records, audit_ledger (field-level encryption)
CONFIDENTIAL: review_*, mastery_*, learning_profiles (at-rest encryption)
INTERNAL: recommendations (no encryption)

---

## Dependencies
- Sprint 30 (audit log infra, PII encryption at rest) — F-425 audit_ledger extends F-314
- Sprint 31 (application service layer) — IEP operations benefit from Command/Query handlers
- Sprint 32A (consent management, data retention) — F-424 consent extends F-349
- Sprint 33+ F-333 (arq worker) — for F-446 data retention job
- Sprint 35 (ZPD engine) — for F-442 ZPD-mastery integration

## Risks
- F-412: IEP data is highly sensitive — encryption + audit trail critical (FERPA)
- F-429: SM-2 multiplier drift across personas — version policy and log policy_version
- F-440: Over-recommendation → alert fatigue — limit to 3 active recommendations per student
- F-447: Cross-tenant data leakage — RLS policies from Sprint 32A F-354 required

## Micro-tasks: ~120 (36 stories × ~3.3 tasks each)
