# Sprint 32 — Privacy Compliance (LGPD/GDPR) + Sprint 33+ Advanced Features

**Goal:** Full LGPD/GDPR compliance framework + advanced features that transform AiLine from MVP to competitive inclusive EdTech platform (gamification, IEP tracking, spaced repetition, AI Social Stories, predictive accommodations).

**Theme:** Legal compliance foundation + differentiation features. GDPR/LGPD plan verified against ANPD Resolucao CD/ANPD 15/2024 and provider DPAs (Anthropic, Google, OpenAI).

**Duration:** 4-6 weeks (2 sub-sprints) | **Status:** planned

---

## Sprint 32A — Privacy Compliance (F-346 → F-355)

### Phase 1 — Data Governance

**F-346: Data Tier Classification + ORM Tagging**
- Column-level tagging via SQLAlchemy `info` dict: RESTRICTED (disability, health), CONFIDENTIAL (email, name, auth), INTERNAL (plan content), PUBLIC (curriculum metadata)
- CI enforcement: lint rule checking new columns have classification
- AC: All existing columns classified. CI catches unclassified new columns.

**F-347: Data Portability Export API (LGPD Art. 18)**
- POST /privacy/exports → async job → ZIP archive (JSON + NDJSON + CSV)
- Includes: user profile, all plans, progress data, tutor sessions, accessibility settings
- Signed download URL with 7-day TTL
- AC: Full user data exportable. Machine-readable format. Signed URLs expire.

**F-348: Deletion & Anonymization Pipeline (LGPD Art. 18 / GDPR Art. 17)**
- Soft-delete: 30-day grace period with recovery option
- Hard-delete: cross-store purge (DB rows, Redis keys, vector embeddings)
- Anonymization: replace PII with tokens, preserve aggregate analytics
- Legal hold support: block deletion when compliance hold active
- AC: Deletion cascade works. Anonymization preserves analytics. Legal holds block purge.

**F-349: Minor Consent Management (LGPD Art. 14)**
- Guardian verification flow: email verification + consent capture
- Granular consent per purpose (AI processing, progress tracking, data sharing)
- Policy versioning: auto-trigger re-consent on policy changes
- DB: consent_purposes, policy_versions, consent_events, guardian_links
- AC: Parental consent captured before student data processing. Re-consent works.

**F-350: Retention Policy Engine**
- Policy matrix: student data (2yr after graduation), plan data (3yr), audit logs (5yr), AI logs (90d), temp stores (30d)
- arq scheduled worker for automated cleanup
- Evidence-backed execution logs (what was deleted, when, why)
- AC: Retention policies configured. Automated cleanup runs. Execution logged.

### Phase 2 — Incident Response & Provider Compliance

**F-351: Incident Response Playbook**
- Documented playbook: detection, classification, containment, notification, recovery
- Notification templates: ANPD (3 business days), GDPR DPA (72h), guardian communication
- Severity classification: P1 (student health data) through P4 (metadata)
- AC: Playbook documented. Templates ready. Severity levels defined.

**F-352: Provider DPA Register + Runtime Guards**
- Register: Anthropic (48h breach notice, no training), OpenAI (API data not for training), Google (PAID only for student data)
- Runtime guard: tag requests with data_classification, block RESTRICTED data to non-DPA-covered providers
- Startup: verify all configured providers have DPA on file
- AC: DPA register maintained. Runtime blocks non-compliant data flows.

**F-353: Redis Maxmemory Eviction Safety**
- Separate logical databases: ephemeral (rate limits, cache) vs critical (idempotency, events)
- maxmemory-policy: allkeys-lru on ephemeral, noeviction on critical
- AC: Critical data never evicted. Ephemeral data safely expires.

**F-354: Postgres Row-Level Security Foundation**
- RLS policies on student_profiles, plans, materials: tenant_id = current_setting('app.tenant_id')
- set_config('app.tenant_id', ...) in connection setup
- AC: RLS enabled. Cross-tenant queries blocked at DB level.

**F-355: Notification Service Foundation**
- Email (SendGrid or SMTP): welcome, password reset, consent request, weekly digest
- In-app (SSE): plan ready, milestone, system alerts
- Push (Web Push API): background plan completion, parent weekly report
- AC: Email sending works. In-app notifications render. Push registration works.

---

## Sprint 33+ — Advanced Features (F-356 → F-375)

### Gamification & Engagement (from Gemini + purpose analysis)

**F-356: "Learning Rhythm" Backend**
- Forgiving momentum: decays -10%/day (not binary streak). Rest days boost recovery.
- Streak freeze: automatic on sick days / holidays.
- Backend API: GET /v1/rhythm/{student_id}, POST /v1/rhythm/freeze
- AC: Momentum calculated. Freezes work. No punitive mechanics.

**F-357: "Skill Nodes" Achievement System**
- Mastery badges: geometric abstract (hexagons/diamonds), age-agnostic 6-18+
- Non-academic achievements: "Used Focus Mode 5x", "Completed Quiet Mode session"
- DB: achievements, student_achievements. API: GET /v1/achievements/{student_id}
- AC: Badges award on criteria. Non-academic wins recognized. No competitive leaderboard.

**F-358: "Constellation" Curriculum Map (Frontend + Backend)**
- SVG night-sky: stars = lessons, constellations = modules, galaxies = subjects
- Real-time update via SSE on lesson completion
- High-contrast for low-vision, instant illumination for reducedMotion, bionicReading labels
- AC: Map renders. Stars animate on completion. All personas work.

### Educational Intelligence

**F-359: Spaced Repetition Scheduler**
- SM-2 algorithm adapted for inclusive learning (longer intervals for processing speed differences)
- Review schedule per student + standard. "Review Due" items in student view.
- Integration with tutor workflow: tutor suggests review topics.
- AC: Schedule calculated. Review items surface. Tutor integration works.

**F-360: IEP Goal Tracking Schema**
- DB: iep_goals(student_id, goal_text, category, target_date, baseline, target_metric)
- iep_accommodations(student_id, accommodation_type, delivery_method, status)
- goal_progress(goal_id, measurement_date, score, notes)
- CRUD API. Links to student_profiles. Audit trail.
- AC: Goals trackable. Accommodations logged. Progress measurable over time.

**F-361: AI Social Story Generator (ASD)**
- New skill: social_story_generator. Input: scenario ("fire drill", "substitute teacher")
- Output: 5-step illustrated social story with visual supports
- Uses Gemini for illustration descriptions, ElevenLabs for audio narration
- AC: Teacher inputs scenario. AI generates story. Visual supports included.

**F-362: Predictive Accommodation Suggestions**
- Analyze student interaction patterns (time-on-task, error rate, help requests)
- After 5+ interactions: suggest accommodations ("Enable Focus Mode", "Try Bionic Reading")
- Teacher approval workflow (suggestions don't auto-activate)
- AC: Suggestions generated after threshold. Teacher approves. Logged for audit.

**F-363: Cognitive Simplification Engine**
- Reading level slider: original → simplified → highly simplified
- Uses LLM to rewrite content at target Flesch-Kincaid level
- Preserves learning objectives while reducing language complexity
- AC: Slider works. 3 levels available. Objectives preserved.

### Platform Evolution

**F-364: Feature Flags System (Redis-backed)**
- FeatureFlag model: name, enabled_global, tenant_overrides (JSONB)
- Admin API: GET/PUT /admin/feature-flags. Frontend SDK via /capabilities.
- AC: Features toggleable per tenant. Admin CRUD works.

**F-365: CQRS Read Models**
- mv_teacher_dashboard_stats: plan count, student count, avg quality, last activity
- mv_student_progress_summary: mastery levels, assessment trends, engagement
- arq job refresh (every 5min). Dashboard queries hit read models.
- AC: 2 materialized views. Dashboard 10x faster. Refresh automated.

**F-366: Agent A/B Testing Framework**
- Experiment registry: variants, traffic split, start/end dates
- SmartRouter skill variant routing. Outcome tracking (quality scores).
- AC: A/B test with 2+ variants. Outcomes tracked. Admin dashboard.

**F-367: Personalization Engine**
- Student mastery tracking per topic. Skill gap analysis from progress data.
- Adaptive recommendations: next topics, difficulty, resource types.
- AC: Mastery tracked. Gaps identified. Recommendations generated.

### Infrastructure & Quality

**F-368: Search Engine (Meilisearch)**
- Full-text search for materials, plans, skills content.
- Docker Compose service. API: GET /v1/search?q=
- AC: Content indexed. Search returns ranked results. Relevance tuned.

**F-369: API SDK Generation (OpenAPI → TypeScript)**
- Generate typed TypeScript client from OpenAPI spec.
- Publish as npm package for frontend consumption.
- AC: Types auto-generated. Frontend uses typed client. CI regenerates on API change.

**F-370: Admin Dashboard API**
- System monitoring: active users, LLM usage, error rates, health status
- User management: list, roles, deactivate
- AC: Admin endpoints operational. Dashboard data complete.

**F-371: Batch Operations API**
- Bulk student import (CSV). Bulk plan generation (multiple students).
- arq jobs for async processing. Progress tracking.
- AC: CSV import works. Bulk generation queues. Progress visible.

**F-372: Webhook System (LMS Integration)**
- Outgoing webhooks: plan.created, plan.approved, student.milestone
- Incoming: Canvas/Moodle grade sync
- Webhook signature verification (HMAC-SHA256)
- AC: Outgoing webhooks fire. Signature verification works.

**F-373: Git LFS for Binary Media**
- Migrate ~15MB tracked binaries to LFS. Update .gitattributes.
- AC: Repo clone smaller. CI works with LFS.

**F-374: Clean Orphaned Root Files**
- Remove: nul, forms_hack.txt, root PNGs. Update .gitignore.
- AC: Clean root directory.

**F-375: Real Assistive Technology Testing**
- axe-core in Playwright E2E. NVDA screen reader assertions.
- Zero critical a11y violations. CI job.
- AC: axe-core runs in CI. Zero criticals. Screenshots archived.

---

## Dependencies
- Sprint 32A depends on Sprint 30 (audit log infra, PII encryption)
- Sprint 33+ items have varied dependencies (see individual stories)
- F-359 (spaced repetition) benefits from F-341 (persistent stores)
- F-365 (CQRS) depends on F-333 (arq worker) for refresh
- F-366 (A/B) depends on F-332 (domain events) for outcome tracking

## Micro-tasks: ~100 (30 stories × ~3.3 tasks each)
