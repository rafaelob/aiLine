# Sprint 29 — Design System, SVG Illustrations, Core Views & Emotional UX ("Soft Clay")

**Goal:** Transform AiLine from hackathon-grade to a professional, inclusive EdTech platform with original design system, rich illustrations, 3 missing core views (analytics/student/parent), and emotional safety patterns.

**Theme:** Frontend-first — HIGHEST PRIORITY per stakeholder. Design direction: "Soft Clay 2.5D Organic" (via Gemini-3.1-Pro, 12 consultations total). Competitive benchmarks: Khan Academy, Duolingo, Seesaw, Google Classroom.

**Duration:** 3 weeks | **Status:** planned

**Prerequisites:** Sprint 29-A (Foundation & Hygiene) must be completed first.

**Updated Feb 27, 2026:** Enriched with 6 additional Gemini-3.1-Pro consultations + Codex architecture review findings. Key additions:
- React 19 `use()` hook + streaming SSR patterns (server-first data fetching)
- `tailwind-variants` (replaces CVA) for component variant management
- OKLCH `color-mix()` for derived colors (Tailwind 4.2 native)
- `inert` attribute replacing manual focus traps
- Emotional Safety UI patterns pulled forward from Sprint 34 (neutral errors, visual timers, quiet mode) — build correctly into primitives from the start
- PWA foundation with `@serwist/next` + `idb-keyval` for offline persistence
- `eslint-plugin-react-compiler` for React Compiler compatibility enforcement
- Dynamic imports for heavy deps (Recharts, Mermaid, canvas-confetti, DOMPurify)
- Per-disability focus ring customization + `data-intensity` attribute
- `role="log"` for SSE streaming, `<meter>` for score gauges
- Clay shadow system: dual outer+inner shadows for volumetric depth
- Fluid typography with `clamp()` scale

---

## Acceptance Criteria
- [ ] Design system modularized (no file >400 LOC), tailwind-variants for all primitives
- [ ] Professional typography (Inter + Plus Jakarta Sans) and new color palette (Azure/Sage/Amber)
- [ ] 38+ SVG illustrations in "Soft Clay" style, theme-adaptive via CSS custom properties
- [ ] Learning Analytics Dashboard operational (teacher class-level mastery view)
- [ ] Student Learning View with mastery map and adaptive persona features
- [ ] Parent Progress Report with encouraging "Stepping Stones" visualization
- [ ] Emotional safety: neutral errors, Quiet Mode, visual timer, auto-save indicators
- [ ] lucide-react icons replacing all inline SVGs
- [ ] All 1,438+ frontend tests pass, Lighthouse a11y >= 95
- [ ] All 9 persona themes render correctly with new design

---

## Stories (F-272 → F-310) — 39 stories, 6 phases

### Phase 1 — Design System Foundation (P0) [Week 1]

**F-272: Modularize globals.css into token files**
Split 1,463-line globals.css → `tokens/base.css`, `tokens/personas.css`, `utilities/glass.css`, `utilities/animations.css`, `utilities/premium.css`. Each <400 LOC.

**F-273: tailwind-variants + UI primitive components**
Install `tailwind-variants`. Build `components/ui/`: Button (pill/rect, primary/secondary/ghost/danger), Input, Textarea, Select, Dialog/Modal, Badge, Card, Tooltip, Spinner, ActionButton (idle→loading→success states, persona-specific scale, aria-busy).

**F-274: Migrate icon system to lucide-react**
Replace ~30+ inline SVG function components. Create `<Icon>` wrapper (consistent sizing, aria-hidden decorative, role=img semantic).

**F-275: Professional typography (Inter + Plus Jakarta Sans)**
Via `next/font/google`. Base 18px. Scale: h1=2.5rem/700, h2=2rem/600, h3=1.5rem/600, body=1.125rem/400. Dyslexia keeps OpenDyslexic, low-vision keeps Atkinson Hyperlegible.

**F-276: New color palette — Azure/Sage/Amber**
Primary `#1E4ED8`, secondary `#10B981`, accent `#F59E0B`, bg `#FBFDFE`, surface `#F3F4F6`, text `#0F172A`. All 9 persona themes verified WCAG AAA.

**F-277: Centralized useMotionConfig hook**
Reads accessibility store → returns motion config per persona. All `motion` components consume hook. Single source of truth.

**F-278: "Soft Clay" component aesthetic**
Cards: solid `#FFFFFF`, 20px radius, 1px border, ambient shadows. Buttons: pill primary. Forms: gray fill, thick outline on focus. Glass restricted to decorative backgrounds only.

### Phase 2 — SVG Illustration System (P0) [Week 1-2]

**F-279: SVG illustration component architecture**
Create `components/illustrations/` with `IllustrationBase` (a11y: role, aria-labelledby, useId for unique IDs), `ClayFilterProvider` (global `<defs>` for soft shadow filter), organized subdirectories (empty-states/, onboarding/, landing/, personas/, accessibility-icons/, subject-icons/).

**F-280: 6 empty state illustrations (Gemini-generated)**
Convert Gemini SVGs to React components: no-classes (desk+plant), no-plans (canvas+sparkles), no-materials (open book+pages), no-tutors (AI chat bubble), no-progress (seed→sprout), welcome-accessibility (diverse hands+star). All use CSS custom properties, `<title>`/`<desc>`, 400x300 viewport.

**F-281: 5 onboarding illustrations (Gemini-generated)**
Welcome (archway+stepping stones), class setup (cards on grid), meet students (hub+5 satellites), accessibility matters (central figure+4 adaptation nodes), first plan (document→AI→3 adapted docs).

**F-282: Landing page illustrations (Gemini-generated)**
Hero (6 pebble figures in arc around star, 600x400), 4 "How It Works" icons (Upload/AI/Adapt/Track, 200x150 each).

**F-283: 6 persona avatars + 8 accessibility profile icons + 8 subject icons**
Persona avatars (128x128, abstract "pebble figures"): Teacher, Lucas/ASD, Sofia/ADHD, Pedro/Dyslexia, Ana/Hearing, Carlos/Parent. Accessibility icons (64x64): ASD, ADHD, Dyslexia, Low Vision, Color Blind, Motor, Hearing, Cognitive. Subject icons (48x48): Math, Science, Language Arts, History, Art, Music, PE, Technology. All with pattern fills for color-blind safety.

**F-284: Error/status illustrations**
404 (lost student+map), 500 (robot fixing), Offline (connection), Loading (learning), Success (subtle ring). 5 SVGs at 400x300.

### Phase 3 — Core Missing Views (P0-CRITICAL) [Week 2]

**F-285: Learning Analytics Dashboard (Teacher)**
Class mastery overview (sorted horizontal BarChart with SVG PatternDefs for color-blind). Individual student progress (AreaChart with confidence intervals). Engagement sparklines per student. Accommodation effectiveness (grouped BarChart). AccessibleTooltip consuming theme tokens. Motor persona: 56px hit-area dots.
AC: Keyboard navigable. All Recharts use CSS custom properties. Data from existing API endpoints.

**F-286: Student Learning View page (NEW route /(app)/learn/[planId])**
Single-column, max-width 65ch. Minimalist top bar (back, progress bar, TTS, settings). Personal mastery map (horizontal BarChart). Active plan with progress checklist. Per-persona: monochrome (ASD), spotlight/ruler (ADHD), font toggle (Dyslexia), visual cues (Hearing). bionicReading/fontSize respected.

**F-287: Parent Progress Report page (NEW route /(app)/parent-report)**
"Stepping Stones" ComposedChart (stepAfter Area, warm tones only, NO red). Natural language tooltips via next-intl. Weekly Growth Digest card. AI-generated conversation starters ("Ask Maria how she solved the fraction puzzle today"). 3-locale i18n.

**F-288: Recharts accessibility infrastructure**
Build `<PatternDefs>` SVG component (hatched/dotted fills for all chart types). Custom `<AccessibleTooltip>` respecting theme tokens. Replace all native ActiveDot with 56px invisible hit-area for motor persona. ASD: stepAfter curves (no smooth). Dyslexia: LabelList on bars (no legends).

### Phase 4 — Page Redesigns & Responsive (P1) [Week 2-3]

**F-289: Landing page redesign — "Soft Clay"**
2-column hero (desktop) with SVG hero illustration / stacked (mobile). Zig-zag features with "How It Works" SVG icons. Horizontal scroll-snap testimonials. ScrollReveal animations (whileInView, once:true, persona-safe easing). Slow ambient gradient (30-60s).

**F-290: Teacher dashboard redesign — 12-column grid**
AI insight row, bento stat cards (from analytics data), 8-col recent plans + 4-col quick actions. Integrates with new analytics BarCharts. Tablet: stack on portrait, 48px targets.

**F-291: Explicit tablet breakpoint (md: 768px)**
Sidebar: off-canvas drawer on tablet. Touch targets ≥48px. 2-col on landscape, 1-col on portrait. Master-Detail split view for iPad.

**F-292: Standard dark theme**
Dark mode for standard theme only. `prefers-color-scheme` + toggle in accessibility panel. Proper contrast ratios verified.

**F-293: Multi-step teacher onboarding flow**
5 steps with SVG illustrations: welcome, class setup, student profiles, accessibility intro, first plan. Encouraging tone. Progressive disclosure. Skippable. State persisted.

### Phase 5 — Emotional Safety & Accessibility Innovation (P0-P1) [Week 2-3]

**F-294: Neutral error states (trauma-informed design)**
Replace ALL red X / aggressive error indicators. Form errors: "Please fill this in so we can continue" with icon + warm background tint. No buzzers. Multi-modal feedback (visual + text + ARIA).
AC: Zero red-only error indicators in student-facing UI.

**F-295: Visual Pie-Chart Timer component (<TimeTimer>)**
Circular depleting colored pie (not numeric countdown). For ADHD time blindness. Works in visual schedules. Respects reduced-motion. Warm Amber accent color.

**F-296: "Quiet Mode" workspace toggle**
Mutes all colors to grayscale, hides social/peer elements, stops ALL animations. Single toggle in accessibility panel. Persists per session. Combines with any persona theme. For sensory processing / anxiety.

**F-297: Improved empty states with SVG illustrations + encouraging microcopy**
Wire SVG-280 illustrations into Dashboard/Plans/Materials/Tutors/Progress/Accessibility pages. Each: illustration + helpful text + primary CTA pill button.

**F-298: ADHD Reading Ruler + Executive Function Support**
Horizontal highlight bar tracking scroll (dimmed periphery). AI plan chunking (20min → 3×6min). Visual Pacing Bar (NOT countdown — triggers anxiety). Progress checklist with check animations. Auto-collapse sidebars via lowDistraction integration.

**F-299: Dyslexia alternating rows + font enhancements**
Subtle alternating background on paragraphs/list items. Evidence-based reading aid. Toggleable in accessibility panel.

### Phase 6 — Engagement Foundation (P2) [Week 3]

**F-300: Drag-and-drop plan reorder**
motion/react Reorder API for plan sections. Keyboard: ArrowUp/Down + Space. aria-roledescription="sortable". Motor persona: 56px grab handles. ASD: no spring physics.

**F-301: ScrollReveal + micro-interactions kit**
ScrollReveal (whileInView, once:true). FormField with persona-aware error shake (disabled for ASD). Staggered skeleton loading. Button press scale(0.97). All respect reducedMotion.

**F-302: PWA foundation (@serwist/next)**
CacheFirst (fonts, illustrations) + NetworkFirst (API, 3s timeout) + NetworkOnly (SSE, auth). useOnlineStatus hook. Read-only offline mode with cached plans. Custom InstallPrompt. Lighthouse PWA >90.

**F-303: "Learning Rhythm" forgiving gamification**
Forgiving momentum metric (decays slowly, rest days boost recovery). "Skill Nodes" mastery badges (geometric SVG, age-agnostic). Streak display with gentle pulse. NO anxiety triggers. i18n 3 locales.

**F-304: Celebration pattern evolution**
Replace confetti with subtle expanding ring + checkmark. Dignified, mentor-like. "Your mind is recharging!" for rest days. Respect reduced-motion.

**F-305: Persona explainer + improved a11y status**
"Why this adaptation?" context banner. Per-persona hints. Encouraging tone. aria-live polite.

### Stretch Goals (if time permits)

**F-306: "The Constellation" progress metaphor**
SVG night-sky curriculum map. Stars light on lesson completion, constellations form on module completion. bionicReading labels. High-contrast dots for low-vision.

**F-307: Push notifications (Web Push API)**
Contextual prompts. Teacher: plan ready. Parent: weekly report. SSE→Push fallback.

**F-308: Multimodal student response capture**
Voice recording (Web Audio), drawing canvas (perfect-freehand, Apple Pencil), photo capture. UDL Principle 3.

**F-309: Classroom Constellation (cooperative social learning)**
Anonymous, asynchronous class progress. No individual leaderboards. Protects social anxiety.

**F-310: Digital Transition Passport**
Export accessibility preferences as "Self-Advocacy Card" (PDF/JSON). Builds self-determination.

---

## Dependencies
- Phase 1 must complete before Phases 2-6 (design tokens are foundation)
- Phase 2 (SVGs) can parallel with Phase 1 (architecture only, not theming)
- Phase 3 (core views) depends on F-288 (Recharts infra)
- Phase 5 (emotional safety) can parallel with Phase 4

## Risks
- 39 stories is aggressive for 3 weeks — Phases 1-5 are must-have, Phase 6 is stretch
- Visual regression tests need re-baselining after aesthetic migration
- 9 themes × new design = extensive visual QA

## Micro-tasks: ~120 (39 stories × ~3 tasks each)
