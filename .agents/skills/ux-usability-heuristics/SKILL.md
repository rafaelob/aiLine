---
name: ux-usability-heuristics
description: >-
  Evaluate UX flows and information architecture with Nielsen's heuristics, interaction
  principles, and AI-specific checks. Use when reviewing navigation, forms, onboarding,
  error recovery, or a complete product flow. Pair with ui-density-refactor for one
  overloaded screen, accessibility for WCAG, and ai-trust-transparency-ux for AI
  trust UX.
context: fork
agent: frontend
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.2.8
  category: design-ux
  subcategory: ui-design
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - ux
  - usability
  - heuristics
  - user_level
  audience: developer
  output_format: markdown
  modality: text
---

# UX & Usability Heuristics (Product-Quality UI)

Production playbook for evaluating and improving user experience through heuristic analysis, interaction design principles, information architecture, microcopy writing, and modern patterns for mobile and AI interfaces. Converts abstract heuristics into concrete, implementable UI improvements.

## Scope
<!-- FRONTEND_DESIGN_PAIRING_START -->
- **Pairs well with `frontend-design` (look vs usability):** Let `frontend-design` drive the visual point-of-view; use this skill to ensure flows, copy, IA, and interaction patterns maximize task success and reduce cognitive load.
- **Conflict resolution:** If a visual choice harms usability (legibility, discoverability, error recovery), propose a redesign that preserves the aesthetic direction while improving clarity and user outcomes.
<!-- FRONTEND_DESIGN_PAIRING_END -->

- **Tactical density refactor:** when one specific screen is overloaded and needs a structural refactor -- not a broad audit -- hand off to `ui-density-refactor` for the diagnosis-to-refactor playbook (action hierarchy, progressive-disclosure pattern selection, refactor moves).
- A feature works but users report confusion, high error rates, or low completion.
- Improving conversion funnels, onboarding flows, or retention.
- Redesigning navigation, forms, settings, or error handling.
- Reviewing AI/LLM-powered features for trust, transparency, and usability.
- Conducting a heuristic evaluation before usability testing.

## Inputs to collect
- Scope: specific flow/page, full product audit, or comparative analysis.
- Platform: web (desktop/mobile), native mobile (iOS/Android), or cross-platform.
- User context: who are the users, what are their goals, what devices/environments.
- Available data: analytics (funnel drop-offs, click maps), support tickets, prior research.
- Business metrics: conversion rate, task completion time, error rate, NPS, or other KPIs.

## Execution playbook

### Step 1 -- Nielsen's 10 usability heuristics evaluation
Evaluate each heuristic with modern examples. Rate severity: 0 (not a problem) to 4 (catastrophic). For a formal evaluation (not a quick pass), read `references/UX_HEURISTICS_GUIDE.md` before scoring: it has the preparation checklist, the finding template, the severity rating scale, and the report structure used in Deliverables below.

**H1: Visibility of system status**
- The system must keep users informed about what is happening through timely, appropriate feedback.
- Modern examples: progress indicators for uploads/AI generation, skeleton loaders not spinners, real-time save status ("Saved" / "Saving..."), streaming LLM output showing generation in progress.
- Violation: form submits with no feedback; user does not know if the action worked.

**H2: Match between system and real world**
- Use language, concepts, and conventions familiar to the user, not developer jargon.
- Modern examples: "Sign in" not "Authenticate", shopping cart metaphor, natural date formats.
- Violation: error messages showing stack traces or HTTP status codes to end users.

**H3: User control and freedom**
- Provide undo, redo, cancel, and "emergency exits" for mistakes.
- Modern examples: undo send in email/chat, edit/delete sent messages, "Back" works correctly in SPAs, easily cancel subscriptions.
- Violation: irreversible delete without confirmation; no way to go back.

**H4: Consistency and standards**
- Follow platform conventions and be internally consistent.
- Modern examples: consistent icon meanings, same button placement across pages, standard gesture patterns on mobile, respecting OS-level settings (dark mode, text size).
- Violation: primary action button changes position between pages.

**H5: Error prevention**
- Prevent errors before they happen through constraints, confirmations, and smart defaults.
- Modern examples: inline validation as user types, disabled submit until valid, type-ahead suggestions, date picker instead of free text, confirmation for destructive actions.
- Violation: allowing invalid email format to submit; no confirmation before permanent deletion.

**H6: Recognition rather than recall**
- Make options, actions, and information visible or easily retrievable.
- Modern examples: recent searches, autocomplete, breadcrumbs, persistent navigation, command palette (Cmd+K) with search.
- Violation: requiring users to memorize codes/IDs; navigation hidden behind a hamburger menu on desktop.

**H7: Flexibility and efficiency of use**
- Accelerators for expert users that do not burden novices.
- Modern examples: keyboard shortcuts (with discoverable hints), bulk actions, saved filters/presets, drag-and-drop alongside button alternatives, templates for common tasks.
- Violation: no keyboard shortcuts in a productivity tool.

**H8: Aesthetic and minimalist design**
- Every visual element must earn its place. Remove noise to elevate signal.
- Modern examples: progressive disclosure (show basics first, reveal details on demand), clean dashboards with drill-down, whitespace as a design element.
- Violation: dashboard showing 50 metrics when user needs 5.

**H9: Help users recognize, diagnose, and recover from errors**
- Error messages must explain WHAT happened, WHY, and HOW to fix it.
- Modern examples: inline field errors pointing to the exact problem, "Try again" buttons, suggested corrections, link to help article.
- Violation: "An error occurred" with no explanation.

**H10: Help and documentation**
- Provide contextual help that is easy to search and focused on the user's task.
- Modern examples: tooltips on complex fields, onboarding tours (skippable), contextual help panels, searchable help center, AI-powered help chat.
- Violation: a 200-page manual with no search; help docs not matching current UI.

### Step 2 -- User research methods
- **Usability testing (moderated):** a first pass may observe 5-8 users completing tasks, but choose
  the sample from the research question, risk, audience diversity, and desired confidence. Best for
  discovering why users struggle.
- **Unmoderated remote testing:** scalable, asynchronous (UserTesting, Maze, Lyssna). Best for validating across geographies.
- **Task analysis:** decompose user goals into step-by-step task flows. Map happy path, error paths, and edge cases.
- **A/B testing:** compare implementations with real traffic. Requires sufficient volume for statistical significance.
- **Heuristic evaluation:** expert review using this playbook. Fast, cheap, catches obvious issues before involving users.
- **Analytics review:** funnel analysis, click/heat maps, session recordings.

### Step 3 -- Information architecture
- **Card sorting:** discover how users group and label content. Treat 15-30 participants as a
  starting heuristic and adjust for the method, audience, and analysis plan.
- **Tree testing:** validate navigation structure against findability. Treat 50+ participants as a
  planning example, not a universal minimum; set the sample for the decision being made.
- **Navigation design:** flat over deep, consistent primary navigation, breadcrumbs for hierarchy, descriptive link text, search for content-heavy apps.
- **Dense-screen execution:** to restructure an overloaded screen (cluttered dashboard, data table, admin panel) into a task-oriented layout with progressive disclosure, hand off to `ui-density-refactor`.

### Step 4 -- Interaction design principles
- **Fitts's Law:** make frequently used targets large and close to cursor rest position.
- **Hick's Law:** reduce option count, use progressive disclosure, provide defaults.
- **Affordances:** interactive elements must look interactive. Flat design without affordance cues causes usability problems.
- **Feedback:** every user action gets an immediate response -- visual state change, loading, error at point of failure.
- **Error prevention over recovery:** constraints, input masks, inline validation, smart defaults, undo.
- **Direct manipulation:** drag, resize, reorder, edit inline -- always provide a non-drag alternative for accessibility.

### Step 5 -- Accessibility as UX
- Accessible design improves UX for everyone (curb-cut effect).
- **Cognitive load:** reduce memory demands, provide context, use plain language, chunk information.
- **Motor diversity:** use the target platform's guidance for touch targets and provide sufficient
  spacing and alternatives to precise gestures. For web WCAG checks, `2.5.8` uses a 24x24 CSS-pixel
  minimum with exceptions; mobile platform guidance often uses 48x48dp on Android and 44x44pt on
  iOS, so do not treat those values as interchangeable.
- **Visual diversity:** sufficient contrast, resizable text, not relying on color alone.
- **Situational impairments:** one-handed use, bright sunlight, noisy environments, slow networks.
- See the `accessibility` skill for detailed WCAG implementation.

### Step 6 -- Microcopy and content design
- **Error messages:** state WHAT happened + WHY + HOW to fix. Not: "Invalid input" or "Error in field 2."
- **Empty states:** explain what will appear, why it is empty, and what action to take. Never show a blank page.
- **Loading states:** skeleton screens for predictable layouts, progress bars for known duration, activity indicators for unknown.
- **CTAs:** use specific verbs describing the outcome. "Create account" not "Submit". One primary CTA per view.
- **Destructive actions:** require explicit confirmation with specific consequence stated. Use danger styling.
- **Tone:** match the product personality. Professional for B2B/finance. Never cute during error recovery.

### Step 7 -- Mobile UX patterns
- **Thumb zones:** primary actions in the bottom third of the screen. Bottom navigation for top-level sections.
- **Gestures:** swipe to delete/archive, pull to refresh, pinch to zoom. Always provide button alternatives.
- **Bottom sheets:** use for contextual actions and filters. Prefer over modals on mobile.
- **Navigation:** bottom tab bar for 3-5 destinations. Stack navigation for drill-down.
- **Touch targets:** verify the current platform guidance (often 48x48dp for Android and 44x44pt for
  iOS) and add spacing between adjacent targets. For web conformance, use the WCAG 2.2 target-size
  criterion and its exceptions.
- **Offline:** show cached content, queue actions, indicate sync status, provide clear offline indicators.
- **Spatial/immersive UX** (visionOS, WebXR): depth, gaze, and hand-tracking introduce new UX paradigms. For the technical WebXR session/controller integration, see `webxr-immersive` -- this catalog has no dedicated skill for native visionOS/RealityKit UX yet.

### Step 8 -- AI and conversational UX
- **Streaming output:** show LLM responses as they generate. Use a typing indicator before the first token.
- **Confidence display:** communicate uncertainty with phrases like "I think..." or confidence scores when appropriate.
- **Edit and retry:** allow users to edit their prompt and regenerate. Provide "Regenerate" and "Edit" buttons.
- **Trust signals:** cite sources, show reasoning steps, indicate when information might be outdated.
- **Graceful degradation:** when the AI cannot answer, explain why and suggest alternatives or human fallback.
- **Setting expectations:** communicate what the AI can and cannot do upfront.
- **Multi-turn context:** show conversation history, provide "New conversation" to reset context.
- **Agentic UX:** for AI features that take autonomous actions (tool calls, multi-step workflows), provide transparency into what the AI is doing and why. Show tool-use activity, allow users to approve/reject actions, and provide clear handoff points between AI and human control. Bound autonomous loops with visible progress and cancellation controls.
- **Supplementary frameworks for AI UX:** Nielsen's heuristics are necessary but not sufficient for AI interfaces. Also apply **Microsoft's Guidelines for Human-AI Interaction** (18 guidelines covering initial interaction through errors) and **Apple's Machine Learning Human Interface Guidelines** (covering suggestions, confidence, corrections, and privacy) when evaluating AI-powered features.

## Deliverables / Definition of Done
- Heuristic evaluation report: each heuristic scored with specific findings, severity, and recommended fixes.
- Prioritized improvement list: severity x impact matrix, effort estimates, quick wins identified.
- Concrete UI changes implemented or specified with enough detail for implementation.
- Success metrics defined for each improvement (measurable before/after comparison).
- Microcopy reviewed for error states, empty states, loading states, and CTAs.

## Common pitfalls
- Running a heuristic evaluation as the only research method -- it finds usability problems but not user needs.
- Fixing symptoms (changing button color) without addressing root cause (confusing information architecture).
- Ignoring mobile context: testing only on desktop, forgetting thumb reach zones, not handling offline.
- Over-designing empty/error/loading states separately -- they need to feel like part of the same product.
- Assuming AI features need no UX design -- AI interactions need more UX design than deterministic features.
- Treating accessibility as a post-launch audit instead of a design constraint.

## Example prompts
- "Run a heuristic evaluation on our checkout flow and propose prioritized fixes."
- "Audit our error states across the app: messages, empty states, loading, and offline handling."
- "Redesign the mobile navigation to follow thumb zone best practices."
- "Review our AI chat feature for trust signals, error handling, and conversation UX."

## Validation

Before delivering a heuristic-evaluation report, verify each of these -- an evaluation that skips them is opinion, not evidence:

- [ ] Every one of the 10 heuristics was checked against the actual scope (screen/flow/product), not assumed from memory.
- [ ] Every finding has a severity (0-4), a concrete location, and observed evidence (screenshot, recording, or specific interaction) -- not just "feels off."
- [ ] Every severity 3-4 finding has a specific, actionable recommendation, not just "improve this."
- [ ] States were checked, not only the happy path: loading, empty, error, and disabled states for every flow in scope.
- [ ] Mobile/touch was evaluated, not just desktop -- thumb zones, touch target size, offline behavior if applicable.
- [ ] Accessibility-as-UX items (contrast, motor/visual diversity, cognitive load) were checked, not deferred silently to a separate audit.
- [ ] If AI/conversational surfaces are in scope, Step 8's AI-specific checks (streaming, confidence, trust signals, agentic transparency) were run in addition to the 10 heuristics.
- [ ] Findings are prioritized (severity x impact), not just listed in the order they were found.
- [ ] If this hands off to `ui-density-refactor` or `ux-copy-patterns` for tactical execution, that handoff is stated explicitly with the specific findings it covers.

## Reference files

- Read `references/UX_HEURISTICS_GUIDE.md` when running a formal heuristic evaluation (not a quick pass): preparation checklist, evaluator process, severity rating scale, finding template, and report structure.

## Invocation
- Prefer implicit selection.
- To explicitly request: **Use the `ux-usability-heuristics` skill**.

## Dependency Currency

- Nielsen's 10 heuristics are stable, but platform conventions evolve; verify iOS HIG and Material Design 3 for current mobile patterns: https://developer.apple.com/design/human-interface-guidelines/ ; https://m3.material.io/
- AI/conversational UX sources for Step 8: Microsoft's Guidelines for Human-AI Interaction (https://www.microsoft.com/en-us/research/project/guidelines-for-human-ai-interaction/); Apple's Machine Learning HIG (https://developer.apple.com/design/human-interface-guidelines/machine-learning).
- WCAG 2.2 AA remains the technical accessibility bar: https://www.w3.org/WAI/standards-guidelines/wcag/. See `accessibility`.
- Record UX tooling decisions in the consuming repo's own design doc (an ADR or `docs/`).
