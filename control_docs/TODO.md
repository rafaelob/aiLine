# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints (S0-25)

All 26 sprints COMPLETED. 224 features (F-001 through F-224). ~3,600+ tests (2,348 runtime + 277 agents + 1,236 frontend). 0 lint/type errors. Docker 4 services healthy. See FEATURES.md for per-sprint detail.

---

## Sprint 26 — "Make the Invisible Visible" — DONE

### Backend Wiring (F-175/F-176/F-165/F-177)
- [x] Skills API wired to app factory with SessionFactorySkillRepository (F-176)
- [x] TTS router wired with ElevenLabs/FakeTTS fallback (F-165)
- [x] Skills workflow nodes integrated in plan + tutor workflows (F-177)
- [x] Settings: elevenlabs_api_key field, diagnostics endpoint updated

### Frontend — High-Impact Visual Features
- [x] Agent Pipeline Visualization — 6-node real-time graph with "Opus 4.6 Core" badge (F-217)
- [x] Adaptation Diff View — split-pane standard vs adapted with profile switching (F-218)
- [x] Evidence Panel — 6-section trust accordion (model, quality, standards, RAG, a11y, time) (F-219)
- [x] TTS Audio Player — play/pause, speed, language, voice selector (F-220)
- [x] Braille Download + Copy — download .brf, copy to clipboard (F-221)
- [x] Inclusive Classroom Mode — 4-student cockpit grid with accent colors (F-222)

### Quality
- [x] 15 ruff lint errors fixed
- [x] 2 TypeScript errors fixed (FeatureItem icon type, ReactNode cast)
- [x] ai_receipt SSE event type mismatch fixed
- [x] evidence-panel null-safety fixes
- [x] Docker frontend memory increased to 2G

---

## Post-Hackathon (unscheduled)
- [ ] Postgres RLS, Redis rate limiter, disable OpenAPI in prod, SW multi-locale caching
- [ ] Auth: migrate in-memory store to PostgreSQL-backed user persistence
- [ ] Teacher Skill Sets — per-teacher presets (F-178)
- [ ] Real assistive technology testing (axe-core E2E with NVDA/VoiceOver)
- [ ] Braille Grade 2 via liblouis
