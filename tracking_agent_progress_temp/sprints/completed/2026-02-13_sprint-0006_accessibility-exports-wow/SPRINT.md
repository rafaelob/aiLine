# Sprint 0006 — Accessibility Exports + Visual Wow

**Status:** planned | **Date:** 2026-02-13
**Goal:** Export comparison side-by-side viewer, visual schedule renderer,
persona toggle demo, simulate disability mode, accessibility twin
(before/after slider), and VLibras integration. These are the "wow factor"
components that demonstrate AiLine's inclusive design philosophy during the
hackathon presentation.

---

## Scope & Acceptance Criteria

Build six interactive demo/presentation components that showcase AiLine's
accessibility capabilities. These components serve dual purposes: (1) real
utility for educators comparing and evaluating accessible content variants, and
(2) visual impact for the hackathon judges demonstrating the depth of
accessibility consideration in the platform.

The Export Comparison Viewer lets educators place two export variants side by
side with diff highlights. The Visual Schedule Renderer turns plan steps into a
timeline. The Persona Toggle Demo is an interactive toolbar for instant theme
switching with a sliding pill animation. The Accessibility Twin is a slider-based
before/after comparison of standard vs. accessible content. The Simulate
Disability mode applies CSS/SVG/JS-based approximations of visual/motor
impairments as an "Empathy Bridge for Educators." VLibras integration provides
Brazilian Sign Language (Libras) avatar rendering via the government CDN widget.

All components must work within the design system established in Sprint 5
(9 persona themes, WCAG AAA compliance, full i18n).

---

## Persona Theme Definitions (Gemini-3-Pro-Preview Expert Consultation)

These are the exact CSS custom property definitions for the 9 accessibility
personas. All Sprint 6 components must render correctly under every theme.
These definitions live in the design system established in Sprint 5 and are
referenced here for implementor convenience.

```css
/* TEA (Autism) - Muted, Soft, Low Stimulation */
[data-theme="tea"] {
  --canvas: #FDFBF7;
  --primary: #576F72;
  --text-body: #2D3436;
  --font-family: "Verdana", sans-serif;
  --animation-scale: 0.5;
}

/* TDAH (ADHD) - High Focus, Sectioning */
[data-theme="tdah"] {
  --canvas: #F1F5F9;
  --primary: #2563EB;
  --border-width: 2px;
  --line-height: 1.8;
}

/* Low Vision - Max Contrast */
[data-theme="low-vision"] {
  --canvas: #000000;
  --text-body: #FFFF00;
  --primary: #00FFFF;
  --text-h1: 3.5rem;
  --text-body-size: 1.5rem;
  --border-width: 4px;
}

/* Dyslexia */
[data-theme="dyslexia"] {
  --font-family: "OpenDyslexic", "Comic Sans MS", sans-serif;
  --letter-spacing: 0.05em;
  --word-spacing: 0.1em;
  --line-height: 2.0;
}

/* Hearing - Visual Cues */
[data-theme="hearing"] {
  --visual-cue-opacity: 1;
}

/* Cognitive - Simplified */
[data-theme="cognitive"] {
  --font-family: "Arial", sans-serif;
  --text-body-size: 1.25rem;
  --primary: #059669;
  --layout-gap: 2rem;
}

/* Motor - Large Targets */
[data-theme="motor"] {
  --touch-target-min: 64px;
  --layout-gap: 1.5rem;
}

/* Color Blindness */
[data-theme="color-blind"] {
  --primary: #0077BB;
  --error: #D55E00;
  --success: #009E73;
  --warning: #F0E442;
}

/* Standard and High Contrast themes already defined in Sprint 5 base */
```

Implementation notes:
- `--animation-scale` is consumed by framer-motion via a `useAnimationScale()`
  hook that reads the CSS variable and multiplies all durations/distances.
- `--visual-cue-opacity` controls visibility of visual notification indicators
  (flash-on-sound, captions overlay) for hearing-impaired users.
- `--touch-target-min` enforces minimum interactive element sizing for motor
  persona, consumed by a Tailwind utility class `.touch-target-min`.

---

## Stories

### S6-001: Export Viewer (Side-by-Side Comparison with Diff Highlights) [ ]

**Description:** Build an interactive split-pane viewer that displays two export
variants side by side for comparison. Each pane has a dropdown selector to choose
from the 9 export variants. Teachers use this to compare how the same lesson plan
looks across different accessibility formats (e.g., standard HTML vs.
dyslexia-friendly HTML vs. large-print HTML).

HTML variants render in sandboxed iframes to isolate their styles from the main
app. Plain text and audio script variants render in styled containers within the
app. All HTML content is sanitized with DOMPurify before rendering.

**Files:**
- `frontend/components/exports/export-comparison.tsx` -- split-pane container with resizable divider
- `frontend/components/exports/export-renderer.tsx` -- renders a single export variant (iframe or styled container)
- `frontend/components/exports/variant-selector.tsx` -- dropdown to choose variant
- `frontend/components/exports/diff-highlight.tsx` -- diff annotation layer

**9 export variants (from backend `ExportVariantArgs`):**
1. `standard_html` -- clean semantic HTML
2. `low_distraction_html` -- minimal styling, no decorative elements
3. `large_print_html` -- 24px+ base font, generous spacing
4. `high_contrast_html` -- black bg, white text, AAA compliant
5. `dyslexia_friendly_html` -- OpenDyslexic font, 2.0 line height
6. `screen_reader_html` -- ARIA landmarks, heading hierarchy, skip links
7. `visual_schedule_html` -- timeline-based visual representation
8. `student_plain_text` -- plain text, simplified language
9. `audio_script` -- narration-ready script with timing markers

**Split-pane design:**
- Default: 50/50 split
- Resizable divider (drag handle): 4px wide, 48px+ drag target (invisible
  larger hit area)
- Minimum pane width: 320px
- Responsive: stacks vertically on mobile (<768px) with full-width panes
  and a toggle to switch between Left/Right

**Diff highlights (Gemini-3-Pro-Preview expert insight):**
When comparing two HTML variants, annotate structural differences visually:
- Green highlight (`bg-green-100/50`) = content added in right variant
  (not present in left)
- Blue highlight (`bg-blue-100/50`) = content modified between variants
  (same element, different content/attributes)
- Use a lightweight DOM diffing utility to identify added/modified nodes
  between the two variant DOMs. Compare at the element level (tag + text
  content), not character level.

**HTML sanitization (Gemini-3-Pro-Preview expert insight):**
All HTML variant content MUST be sanitized with DOMPurify before rendering
in iframes or containers. This is a security requirement since variant HTML
is generated by LLMs:

```tsx
import DOMPurify from "dompurify";

function sanitizeVariantHtml(rawHtml: string): string {
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: [
      "h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "div",
      "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td",
      "strong", "em", "a", "img", "figure", "figcaption",
      "section", "article", "nav", "header", "footer", "main",
      "blockquote", "pre", "code", "br", "hr",
    ],
    ALLOWED_ATTR: [
      "class", "id", "href", "src", "alt", "role",
      "aria-label", "aria-labelledby", "aria-describedby",
      "aria-hidden", "tabindex", "lang", "dir",
    ],
    ALLOW_DATA_ATTR: false,
  });
}
```

**Acceptance Criteria:**
- [ ] Split-pane layout with resizable divider (CSS `resize` or pointer events)
- [ ] Dropdown selector on each pane listing all 9 variants
- [ ] HTML variants (1-7) rendered in sandboxed `<iframe sandbox="allow-same-origin">`
      to isolate variant CSS from app CSS
- [ ] All HTML content sanitized with DOMPurify before rendering
- [ ] Plain text variant (8) rendered in a `<pre>` block with proper font/spacing
- [ ] Audio script variant (9) rendered with timing markers highlighted
- [ ] Diff highlights: green for added content, blue for modified content
- [ ] Divider drag: smooth, constrained to min pane width, visual feedback
- [ ] Responsive: stacks vertically on mobile with toggle buttons ("Left" / "Right")
- [ ] Keyboard accessible: Tab to divider, Arrow Left/Right to resize (10px steps)
- [ ] Divider has `role="separator"`, `aria-orientation="vertical"`,
      `aria-valuenow` (current position percentage)
- [ ] Default selection: Left = `standard_html`, Right = last-selected persona variant
- [ ] All labels use `t()` for i18n
- [ ] Works in all 9 persona themes

---

### S6-002: Visual Schedule Renderer [ ]

**Description:** Build a timeline-based visual schedule that displays plan steps
as colored cards along a horizontal (desktop) or vertical (mobile) axis. Each
step card shows the time allocation, title, step type icon, and key details.
Step types are color-coded for quick visual scanning. Supports a teacher editing
mode with drag-to-reorder, and a print-friendly CSS layout.

**Files:**
- `frontend/components/schedule/visual-schedule.tsx` -- main timeline container
- `frontend/components/schedule/timeline-step.tsx` -- individual step card on timeline
- `frontend/components/schedule/timeline-connector.tsx` -- line/arrow connecting steps
- `frontend/components/schedule/schedule-legend.tsx` -- color-coded legend

**Step types and colors:**
| Step Type | Color | Lucide Icon |
|-----------|-------|-------------|
| Instruction | Blue (`var(--color-primary)`) | BookOpen |
| Activity | Green (`var(--color-success)`) | PlayCircle |
| Assessment | Orange (`var(--color-warning)`) | ClipboardCheck |
| Break | Gray (`var(--color-text-secondary)`) | Coffee |
| Transition | Purple (`var(--color-accent)`) | ArrowRight |

**Step card content:**
- Duration badge (e.g., "15 min")
- Step title (bold)
- Step type icon + label
- Brief description (truncated to 2 lines, expandable)
- Accessibility adaptations indicator (icon if adaptations present)

**Acceptance Criteria:**
- [ ] Horizontal timeline layout on desktop (>=1024px): steps flow left-to-right
      with connecting lines between cards
- [ ] Vertical timeline layout on mobile (<1024px): steps flow top-to-bottom
      with connecting lines
- [ ] Each step card: 200-280px wide (desktop), full width (mobile)
- [ ] Step type color-coding using theme CSS variables (adapts to persona theme)
- [ ] Duration badge: pill-shaped, positioned at top-right of card
- [ ] Color-coded legend below timeline showing step type meanings
- [ ] Teacher editing mode: drag-to-reorder steps (framer-motion `Reorder` component)
- [ ] Drag respects `prefers-reduced-motion`: instant position swap instead of
      animated drag when reduced motion is enabled
- [ ] Print-friendly: `@media print` styles render timeline as a vertical list
      with all descriptions expanded, no interactive elements
- [ ] Lucide icons for each step type
- [ ] Screen reader: timeline uses `role="list"`, each step is `role="listitem"`
      with descriptive `aria-label` (e.g., "Step 3 of 8: Group Activity, 15 minutes")
- [ ] All text uses `t()` for i18n
- [ ] Works in all 9 persona themes

---

### S6-003: Persona Toggle Demo (Sliding Pill Animation) [ ]

**Description:** Build an interactive horizontal toolbar with 9 persona buttons
that instantly switch the design system theme. This component is designed for
live demonstrations: a presenter clicks through personas and the audience sees
the entire UI transform in real time. Each button has an icon and label. The
active persona is highlighted with a sliding pill animation. Transition between
themes is animated (respecting reduced-motion preferences).

**Theme switching uses direct DOM manipulation** (no React re-render) for
instant visual feedback.

**Files:**
- `frontend/components/demo/persona-toggle-bar.tsx` -- horizontal bar of 9 buttons
- `frontend/components/demo/persona-button.tsx` -- individual persona button
- `frontend/components/demo/persona-icons.tsx` -- icon components per persona

**Button layout (9 buttons):**
```
[Standard] [TEA] [TDAH] [Low Vision] [Hearing] [Dyslexia] [Motor] [Cognitive] [Color Blind]
```

**Sliding pill animation (Gemini-3-Pro-Preview expert insight -- exact pattern):**

The active persona indicator uses framer-motion `layoutId` to create a smooth
sliding pill that animates between buttons. This avoids a hard cut between
active states and gives a polished, fluid feel during live demos:

```tsx
import { motion } from "motion/react";

interface PersonaButtonProps {
  persona: PersonaConfig;
  isActive: boolean;
  onSelect: (id: string) => void;
}

function PersonaButton({ persona, isActive, onSelect }: PersonaButtonProps) {
  return (
    <button
      role="radio"
      aria-checked={isActive}
      onClick={() => onSelect(persona.id)}
      className="relative z-10 flex items-center gap-2 px-4 py-2 rounded-full
                 text-sm font-medium transition-colors"
    >
      {/* Sliding pill -- only rendered on the active button */}
      {isActive && (
        <motion.div
          layoutId="active-pill"
          className="absolute inset-0 bg-primary rounded-full shadow-md"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
      <span className="relative z-10 flex items-center gap-1.5">
        <persona.Icon className="w-4 h-4" />
        {persona.label}
      </span>
    </button>
  );
}
```

Spring physics: `stiffness: 300, damping: 30` produces a snappy but not
jarring transition (~250ms settle time). The `layoutId="active-pill"` causes
framer-motion to animate the pill from the previous button position to the
new one using shared layout animation.

**Direct DOM theme switching (Gemini-3-Pro-Preview expert insight):**

Theme switching bypasses React state to avoid a full tree re-render. The
`data-theme` attribute is set directly on `document.body`:

```tsx
function handleThemeSwitch(personaId: string) {
  // Direct DOM mutation -- instant visual feedback, no React re-render
  document.body.setAttribute("data-theme", personaId);

  // Persist to Zustand store (for SSR cookie sync and other consumers)
  // This happens asynchronously and does not block the visual update
  useThemeStore.getState().setTheme(personaId);
}
```

This two-phase approach ensures:
1. **Instant visual response** -- the CSS variables switch immediately via
   `data-theme` attribute selector, no waiting for React reconciliation
2. **State consistency** -- Zustand store is updated for cookie persistence
   (SSR, per ADR-019) and any components that read theme state

**Icon components per persona:**

Each persona has a dedicated icon (Lucide-based or custom SVG). Define a
`PersonaConfig` type and a `PERSONA_CONFIGS` array:

```tsx
import {
  User, Brain, Focus, Eye, Ear, BookType,
  Hand, Lightbulb, Palette,
} from "lucide-react";

interface PersonaConfig {
  id: string;
  label: string;       // i18n key resolved at render time
  Icon: LucideIcon;
  description: string; // i18n key for tooltip
}

const PERSONA_CONFIGS: PersonaConfig[] = [
  { id: "standard",    label: "Standard",     Icon: User,      description: "..." },
  { id: "tea",         label: "TEA",          Icon: Brain,     description: "..." },
  { id: "tdah",        label: "TDAH",         Icon: Focus,     description: "..." },
  { id: "low-vision",  label: "Low Vision",   Icon: Eye,       description: "..." },
  { id: "hearing",     label: "Hearing",      Icon: Ear,       description: "..." },
  { id: "dyslexia",    label: "Dyslexia",     Icon: BookType,  description: "..." },
  { id: "motor",       label: "Motor",        Icon: Hand,      description: "..." },
  { id: "cognitive",   label: "Cognitive",    Icon: Lightbulb, description: "..." },
  { id: "color-blind", label: "Color Blind",  Icon: Palette,   description: "..." },
];
```

**Acceptance Criteria:**
- [ ] Horizontal scrollable bar of 9 persona buttons
- [ ] Each button: Lucide icon (per `PERSONA_CONFIGS`) + short label
- [ ] Active persona indicated by a sliding pill using framer-motion
      `layoutId="active-pill"` with spring physics (`stiffness: 300, damping: 30`)
- [ ] Clicking a button applies theme via direct DOM manipulation:
      `document.body.setAttribute('data-theme', id)` -- NO React re-render
- [ ] Zustand theme store updated asynchronously for persistence/SSR
- [ ] Animated transition between themes: background/color transitions over
      200ms using `var(--transition-duration)`
- [ ] When `prefers-reduced-motion` is active or animations are disabled:
      instant switch (0ms transition), pill teleports instead of sliding
- [ ] Horizontal scroll on narrow screens with fade indicators at edges
      (gradient overlay indicating more buttons available)
- [ ] Keyboard: Tab to bar, Arrow Left/Right between buttons, Enter/Space to
      activate; uses `role="radiogroup"` + `role="radio"` + `aria-checked`
- [ ] Responsive: wraps to 2 rows on tablet, 3 rows on mobile (grid layout)
- [ ] All labels use `t()` for i18n
- [ ] Visually distinct enough from the Settings persona cards (S5-008) --
      this is a compact toolbar, not a grid of cards

---

### S6-004: Accessibility Twin (Tabbed View with Diff Highlights) [ ]

**Description:** Build a tabbed comparison view showing the same educational
content rendered in two different accessibility modes. Tab 1 shows the standard
(default) version; Tab 2 shows the selected persona's accessible version.
Diff highlights use color + texture + icons to show what changed between versions.

**IMPORTANT: ADR-044 decision — clip-path slider was rejected by Gemini-3-Pro
consultation as a WCAG AAA trap (keyboard-inaccessible slider interaction,
screen reader cannot convey split content). Tabbed View is fully accessible.**

This is a high-impact demo component: it viscerally shows judges how AiLine
adapts content for different disabilities.

**Files:**
- `frontend/components/demo/a11y-twin.tsx` -- main tabbed comparison component
- `frontend/components/demo/twin-pane.tsx` -- renders content with a specific theme applied
- `frontend/components/demo/diff-highlights.tsx` -- highlights added/modified content

**Implementation approach:**
- Two tabs: "Standard" and "{Persona Name}" using shadcn Tabs component
- Persona selector dropdown above tabs (choose which persona to compare)
- Diff highlights on the adapted tab:
  - Green background + "+" icon for added elements (e.g., visual schedule, glossary)
  - Blue background + "~" icon for modified elements (e.g., simplified text)
  - Strikethrough + gray for removed elements (e.g., complex diagrams replaced)
- Diff uses color + texture (patterns) + icons for colorblind safety
- Optional "overlay" toggle: show both versions stacked with diff markers

**Acceptance Criteria:**
- [ ] Two tabs: "Standard" and "{Persona Name}" with smooth transition
- [ ] Standard tab: default theme rendering of the content
- [ ] Persona tab: selected persona theme rendering with diff highlights
- [ ] Persona selector dropdown above tabs (choose which persona to compare)
- [ ] Diff highlights: added (green+icon), modified (blue+icon), removed (gray+strikethrough)
- [ ] Diff uses color + texture + icons (not color alone) for colorblind safety
- [ ] Full keyboard navigation between tabs (arrow keys, standard tab pattern)
- [ ] Screen reader announces tab changes and diff summary
- [ ] `aria-label` on tabs, `aria-live="polite"` for diff summary
- [ ] Labels: "Standard" (tab 1), "{Persona Name}" (tab 2)
- [ ] All text uses `t()` for i18n

---

### S6-005: Simulate Disability Mode -- "Empathy Bridge for Educators" [ ]

**Description:** Build CSS, SVG, and JS-based disability simulations that
approximate what content looks like under various visual and motor impairments.
This feature is for empathy and training: non-disabled educators experience an
approximation of how their students perceive content, motivating them to create
more accessible materials.

Simulations apply ONLY to a designated content area (the export comparison
viewer), NOT to the full application UI. This ensures the app itself remains
usable while the simulation is active.

**IMPORTANT: Ethical considerations.** Disability simulations are approximations,
not lived experience. They must be framed as educational tools, not entertainment.
A prominent disclaimer must be shown before activating any simulation.

**Strategic framing (Gemini-3-Pro-Preview expert insight -- "Empathy Bridge for
Educators"):** Do NOT present this as a "feature for users." Present it as an
**educational tool for teachers** -- a bridge that helps educators *feel* why
accessible content matters, before they create it. This is a killer demo feature
for hackathon judges: it instantly justifies WHY the platform exists. During the
demo, the narrative should be: "Before a teacher creates a single lesson plan,
AiLine lets them *experience* what their students experience -- and that
empathy changes everything."

**Files:**
- `frontend/components/demo/simulate-disability.tsx` -- toggle bar + simulation overlay
- `frontend/styles/simulate.css` -- CSS filters and animations for simulations
- `frontend/components/demo/simulation-disclaimer.tsx` -- ethical notice modal
- `frontend/hooks/use-dyslexia-simulator.ts` -- letter-shuffling hook

**SVG filter definitions (Gemini-3-Pro-Preview expert insight -- exact markup):**

These SVG filters must be defined in `app/layout.tsx` (root layout) so they are
available globally. They use scientifically accurate color matrices:

```tsx
// In app/layout.tsx -- rendered once, hidden, available to all pages
<svg className="hidden" aria-hidden="true" style={{ position: "absolute", width: 0, height: 0 }}>
  <defs>
    {/* Deuteranopia (green-blind) -- Brettel et al. 1997 */}
    <filter id="deuteranopia">
      <feColorMatrix type="matrix"
        values="0.625 0.375 0   0 0
                0.7   0.3   0   0 0
                0     0.3   0.7 0 0
                0     0     0   1 0"/>
    </filter>

    {/* Protanopia (red-blind) */}
    <filter id="protanopia">
      <feColorMatrix type="matrix"
        values="0.567 0.433 0   0 0
                0.558 0.442 0   0 0
                0     0.242 0.758 0 0
                0     0     0   1 0"/>
    </filter>

    {/* Tritanopia (blue-blind) */}
    <filter id="tritanopia">
      <feColorMatrix type="matrix"
        values="0.95 0.05  0     0 0
                0    0.433 0.567 0 0
                0    0.475 0.525 0 0
                0    0     0     1 0"/>
    </filter>

    {/* Low vision blur */}
    <filter id="blur-vision">
      <feGaussianBlur stdDeviation="2"/>
    </filter>
  </defs>
</svg>
```

**Tunnel vision CSS (Gemini-3-Pro-Preview expert insight -- exact pattern):**

```css
/* Tunnel Vision -- fixed overlay with radial gradient */
.simulate-tunnel::after {
  content: "";
  position: fixed;
  inset: 0;
  background: radial-gradient(
    circle at var(--cursor-x, 50%) var(--cursor-y, 50%),
    transparent 30%,
    black 90%
  );
  pointer-events: none;
  z-index: 9999;
}
```

The cursor position is tracked via `mousemove` and applied as CSS custom
properties `--cursor-x` and `--cursor-y` on the simulation container. Use
`requestAnimationFrame` to throttle updates to 60fps.

**Dyslexia letter shuffling hook (Gemini-3-Pro-Preview expert insight):**

A custom hook that shuffles inner letters of words while keeping first and last
characters fixed. This produces a visceral "words look right but are wrong"
experience faithful to the dyslexia reading experience:

```tsx
// frontend/hooks/use-dyslexia-simulator.ts

import { useState, useEffect, useCallback } from "react";

function shuffleInnerLetters(word: string): string {
  if (word.length <= 3) return word;
  const first = word[0];
  const last = word[word.length - 1];
  const inner = word.slice(1, -1).split("");
  // Fisher-Yates shuffle on inner characters
  for (let i = inner.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [inner[i], inner[j]] = [inner[j], inner[i]];
  }
  return first + inner.join("") + last;
}

function shuffleText(text: string): string {
  return text.replace(/\b\w{4,}\b/g, (word) => shuffleInnerLetters(word));
}

export function useDyslexiaSimulator(
  isActive: boolean,
  originalText: string,
): string {
  const [displayText, setDisplayText] = useState(originalText);

  useEffect(() => {
    if (!isActive) {
      setDisplayText(originalText);
      return;
    }
    // Shuffle immediately on activation
    setDisplayText(shuffleText(originalText));

    // Re-shuffle on 500ms interval
    const interval = setInterval(() => {
      setDisplayText(shuffleText(originalText));
    }, 500);

    return () => clearInterval(interval);
  }, [isActive, originalText]);

  return displayText;
}
```

The 500ms interval keeps the text shifting just frequently enough to create
disorientation without triggering photosensitive reactions (well below 3Hz
threshold). Combine with the character swap pairs (b/d, p/q, m/w) for a
layered effect.

**Simulations (6):**

1. **Low Vision (Blur)**
   - CSS: `filter: url(#blur-vision) contrast(0.7)`
   - Uses the SVG `<filter id="blur-vision">` defined above
   - Effect: softened, unclear content; simulates uncorrected refractive error

2. **Color Blindness (3 types via SVG filters)**
   - Protanopia (red-blind): `filter: url(#protanopia)`
   - Deuteranopia (green-blind): `filter: url(#deuteranopia)`
   - Tritanopia (blue-blind): `filter: url(#tritanopia)`
   - Sub-selector dropdown to choose type
   - Uses scientifically accurate color matrices (Brettel et al. 1997)

3. **Tunnel Vision (Glaucoma)**
   - CSS: radial gradient mask limiting visible area to a ~200px diameter circle
     that follows the cursor position via CSS custom properties
   - Uses `.simulate-tunnel::after` pattern defined above
   - JS `mousemove` handler updates `--cursor-x` and `--cursor-y`
   - Throttled to 60fps via `requestAnimationFrame`
   - Effect: only a small area around the cursor is visible

4. **Dyslexia Simulation**
   - JS: `useDyslexiaSimulator` hook (defined above) shuffles inner letters
     of words on a 500ms interval, keeping first/last characters fixed
   - Additional layer: character swap pairs (b/d, p/q, m/w) applied randomly
   - CSS: subtle `letter-spacing` variation on text nodes
   - Effect: text appears to shift and become harder to decode
   - Example: "education" becomes "eudcaiton", "accessible" becomes "acesscible"

5. **Motor Impairment**
   - JS: adds cursor jitter (random offset on `mousemove`), delayed click
     response (300ms delay before click event fires), occasional "missed" clicks
   - Effect: simulates difficulty with precise cursor control
   - Implementation: event listener wrappers on the simulation area only

6. **Hearing Impairment** (visual-only simulation)
   - CSS: dims/removes any audio player controls, adds a "No audio available"
     overlay on media elements
   - Effect: shows what content looks like when audio information is inaccessible

**Overlay architecture (Gemini-3-Pro-Preview expert insight):** All simulation
overlays (tunnel vision mask, color blindness filter, etc.) must be rendered via
**React Portal** to `document.body` with `pointer-events: none`. This ensures
overlays are visually on top of content but do not intercept user interactions
(clicks, scrolls, keyboard) with the underlying UI. Only the simulation toggle
bar itself should have `pointer-events: auto`.

**Toggle bar design:**
- Horizontal bar of 6 simulation buttons (similar layout to persona toggle)
- Each button: icon + label + on/off state
- Only one simulation active at a time (radio behavior)
- "Off" button to disable all simulations

**Ethical disclaimer:**
- Modal dialog shown on first activation of any simulation
- Content: "These simulations are rough approximations of certain aspects of
  disability. They do not represent the full lived experience of people with
  disabilities. Their purpose is educational: to help educators understand
  why accessible content matters. Created with guidance from disability
  advocacy resources."
- "I understand" button to proceed; "Cancel" to abort
- Disclaimer shown once per session (stored in sessionStorage)

**Acceptance Criteria:**
- [ ] Low Vision: `filter: url(#blur-vision) contrast(0.7)` applied to simulation area
- [ ] Color Blindness: 3 SVG filter definitions (protanopia, deuteranopia,
      tritanopia) with scientifically accurate Brettel et al. color matrices;
      dropdown to select type
- [ ] SVG filters defined in `app/layout.tsx` as hidden `<svg>` block
- [ ] Tunnel Vision: radial gradient mask follows cursor via CSS custom
      properties (`--cursor-x`, `--cursor-y`) within simulation area;
      uses `.simulate-tunnel::after` pseudo-element pattern
- [ ] Dyslexia Simulation: `useDyslexiaSimulator` hook shuffles inner letters
      on 500ms interval (keeps first/last chars); layered with b/d, p/q, m/w
      character swaps
- [ ] Motor Impairment: cursor jitter (+-5px random offset) + 300ms click delay
      active within simulation area only
- [ ] Hearing Impairment: audio/video controls dimmed with "No audio" overlay
- [ ] Toggle bar with 6 simulation buttons + "Off" button (radio group behavior)
- [ ] Simulations apply ONLY to the export comparison area (`#simulation-target`),
      NOT the full UI
- [ ] All overlays rendered via React Portal with `pointer-events: none`
- [ ] Ethical disclaimer modal on first activation per session
- [ ] Disclaimer text uses `t()` for i18n (available in EN/PT-BR/ES)
- [ ] "Off" button immediately removes all simulation effects
- [ ] Keyboard accessible: Tab to toggle bar, Arrow keys between simulations,
      Enter/Space to activate; `role="radiogroup"` + `role="radio"`
- [ ] All simulation effects are purely visual/interactive -- no permanent
      changes to content or state
- [ ] Performance: simulations do not cause layout thrashing or drop below 30fps
- [ ] Works within all 9 persona themes (simulations layer on top of theme)

---

### S6-006: VLibras Integration (Brazilian Sign Language Widget) [ ]

**Description:** Integrate the VLibras government widget to provide automatic
Brazilian Sign Language (Libras) avatar rendering of all text content. VLibras
translates on-screen text into a 3D animated Libras interpreter avatar, making
the platform accessible to Deaf and hard-of-hearing users who use Libras.

This is a strategic differentiator for the hackathon: it demonstrates compliance
with Brazilian accessibility law (LBI - Lei Brasileira de Inclusao) and provides
real-world inclusive technology, not just theoretical accessibility.

**Files:**
- `frontend/components/accessibility/vlibras-widget.tsx` -- VLibras wrapper component
- `frontend/app/layout.tsx` -- script tag and DOM structure additions

**VLibras integration (Gemini-3-Pro-Preview expert insight -- exact pattern):**

VLibras is loaded from the official government CDN as an external script. It
requires specific DOM structure to initialize:

```tsx
// frontend/components/accessibility/vlibras-widget.tsx

"use client";

import Script from "next/script";

export function VLibrasWidget() {
  return (
    <>
      {/* Required DOM structure for VLibras */}
      <div vw="true" className="enabled">
        <div vw-access-button="true" className="active" />
        <div vw-plugin-wrapper="true">
          <div className="vw-plugin-top-wrapper" />
        </div>
      </div>

      {/* VLibras script -- lazy loaded, does not block page render */}
      <Script
        src="https://vlibras.gov.br/app/vlibras-plugin.js"
        strategy="lazyOnload"
        onLoad={() => {
          // Initialize VLibras widget after script loads
          // @ts-expect-error -- VLibras global not typed
          new window.VLibras.Widget("https://vlibras.gov.br/app");
        }}
      />
    </>
  );
}
```

**Placement in layout.tsx:**

The `VLibrasWidget` component is rendered in the root layout (`app/layout.tsx`)
so it is available on every page. It must be placed at the end of the `<body>`
before the closing tag:

```tsx
// In app/layout.tsx -- at end of body
<VLibrasWidget />
```

**Implementation notes:**
- `strategy="lazyOnload"` ensures the VLibras script does not block initial
  page load or compete with critical resources (per Next.js Script component)
- The `vw="true"` div and its children are required by the VLibras SDK to
  render the floating access button and plugin wrapper
- VLibras automatically detects page language and translates visible text
  content to Libras when the user activates the widget
- The widget renders a 3D avatar that signs the selected text in real-time
- No backend changes required -- VLibras operates entirely client-side

**Acceptance Criteria:**
- [ ] VLibras script loaded from `https://vlibras.gov.br/app/vlibras-plugin.js`
      via `next/Script` with `strategy="lazyOnload"`
- [ ] Required DOM structure rendered: `div[vw="true"]` containing
      `div[vw-access-button="true"]` and `div[vw-plugin-wrapper="true"]`
- [ ] `VLibras.Widget` initialized on script load with correct app URL
- [ ] VLibras floating button visible on all pages (renders in bottom-right)
- [ ] User can select text and trigger Libras translation via the widget
- [ ] Widget does not block initial page load (lazy loaded)
- [ ] Widget z-index does not conflict with simulation overlays or modals
- [ ] Works within all 9 persona themes
- [ ] Component renders only on client side (`"use client"` directive)

---

## Dependencies

- **Sprint 5 (Frontend MVP):** All stories depend on Sprint 5 being complete:
  - Design system with 9 persona themes (CSS variables, theme store)
  - Layout components (Sidebar, TopBar)
  - i18n infrastructure (next-intl, translation keys)
  - Plan tabs structure (S6-001 integrates with exports tab)
  - Score gauge and checklist (S6-004 uses plan content)
- **Backend `export_variant` tool:** S6-001 renders variants generated by the
  backend's `export_variant_handler`. The component must handle the variant
  data format returned by `render_export()`.
- **DOMPurify:** New dependency for S6-001 HTML sanitization. Add to
  `package.json`: `dompurify@^3.x` + `@types/dompurify`.
- **VLibras CDN:** S6-006 depends on the government CDN at
  `vlibras.gov.br/app/vlibras-plugin.js` being available. No npm package;
  loaded via `next/Script`.
- **OpenDyslexic font:** Required for dyslexia persona theme. Must be
  self-hosted or loaded from a CDN in the design system.
- **No additional backend changes required:** All Sprint 6 stories are
  purely frontend.

---

## Decisions

- **Tabbed View for A11y Twin over clip-path slider (ADR-044):** clip-path slider
  rejected as WCAG AAA trap (keyboard-inaccessible, screen reader can't convey
  split content). Tabbed View with diff highlights (color+texture+icons) provides
  full accessibility while maintaining high demo impact.
- **SVG filters for color blindness over CSS-only:** SVG color matrix filters
  provide scientifically accurate color transformations (Brettel et al. 1997)
  for protanopia, deuteranopia, and tritanopia. CSS `hue-rotate` or similar is
  not sufficient for accurate simulation. Filters defined in `layout.tsx` for
  global availability.
- **DOMPurify for HTML sanitization:** LLM-generated HTML variants could
  contain unsafe content. DOMPurify with a strict allowlist prevents XSS while
  preserving semantic structure and ARIA attributes needed for accessibility.
- **Direct DOM for theme switching over React state:** Setting
  `document.body.setAttribute('data-theme', id)` provides instant visual
  feedback without waiting for React reconciliation. Zustand store is updated
  asynchronously for persistence (cookie sync per ADR-019).
- **framer-motion layoutId pill over CSS transition:** The sliding pill
  animation using `layoutId="active-pill"` with spring physics provides a
  significantly more polished demo experience than a simple CSS
  `background-color` transition. The spring parameters (stiffness=300,
  damping=30) were validated by Gemini-3-Pro-Preview for optimal feel.
- **useDyslexiaSimulator hook over inline letter-spacing:** Shuffling inner
  letters (keeping first/last fixed) on a 500ms interval produces a more
  faithful representation of the dyslexia reading experience than simple
  letter-spacing or opacity changes.
- **Simulation scoped to content area, not full UI:** Applying simulations to
  the full UI would make the app unusable. Scoping to the content area
  demonstrates the effect while keeping the controls accessible.
- **Ethical disclaimer as a hard requirement:** Disability simulation without
  proper framing can be harmful. The disclaimer is not optional.
- **One simulation at a time:** Combining simulations (e.g., low vision +
  motor) creates unpredictable interactions and poor UX. Single-selection
  (radio behavior) is clearer.
- **VLibras via government CDN:** Using the official VLibras CDN ensures
  compliance with Brazilian accessibility standards and avoids maintaining a
  self-hosted copy of the widget. `lazyOnload` strategy prevents blocking.

---

## Architecture Impact

```
frontend/
├── app/
│   └── layout.tsx                       # SVG filter defs + VLibras widget added
├── components/
│   ├── exports/
│   │   ├── export-comparison.tsx        # Split-pane viewer (S6-001)
│   │   ├── export-renderer.tsx          # Single variant renderer
│   │   ├── variant-selector.tsx         # Variant dropdown
│   │   └── diff-highlight.tsx           # Diff annotation layer (S6-001)
│   ├── schedule/
│   │   ├── visual-schedule.tsx          # Timeline container (S6-002)
│   │   ├── timeline-step.tsx            # Individual step card
│   │   ├── timeline-connector.tsx       # Line/arrow between steps
│   │   └── schedule-legend.tsx          # Color-coded legend
│   ├── demo/
│   │   ├── persona-toggle-bar.tsx       # 9-button persona switcher (S6-003)
│   │   ├── persona-button.tsx           # Individual toggle button
│   │   ├── persona-icons.tsx            # Icon components per persona (S6-003)
│   │   ├── a11y-twin.tsx               # Before/after slider (S6-004)
│   │   ├── twin-pane.tsx               # Themed content pane
│   │   ├── simulate-disability.tsx      # Simulation toggle bar (S6-005)
│   │   └── simulation-disclaimer.tsx    # Ethical notice modal
│   └── accessibility/
│       └── vlibras-widget.tsx           # VLibras wrapper (S6-006)
├── hooks/
│   └── use-dyslexia-simulator.ts        # Letter-shuffling hook (S6-005)
└── styles/
    └── simulate.css                     # SVG filter refs + tunnel vision CSS
```

**New i18n keys added (~50):**
```
exports.*                (12 keys) -- variant names, comparison labels, diff legends
schedule.*               (8 keys)  -- step types, legend, edit mode
demo.persona.*           (10 keys) -- toggle bar labels, persona descriptions
demo.twin.*              (5 keys)  -- before/after labels
demo.simulate.*          (10 keys) -- simulation names, disclaimer text, ethical notice
accessibility.vlibras.*  (5 keys)  -- VLibras labels, loading state
```

**New dependencies:**
| Name | Version | Official Link | Date Added | Rationale |
|------|---------|---------------|------------|-----------|
| dompurify | ^3.x | github.com/cure53/DOMPurify | 2026-02-13 | HTML sanitization for LLM-generated export variants |
| @types/dompurify | ^3.x | npmjs.com/package/@types/dompurify | 2026-02-13 | TypeScript types for DOMPurify |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ethical concerns about disability simulation | Negative perception from judges or community | Prominent disclaimer, educational framing ("Empathy Bridge"), optional feature, scoped to content area only |
| iframe sandboxing blocks variant rendering | Variants with external resources fail to load | Use `sandbox="allow-same-origin"` and inline all variant CSS/assets |
| Drag interactions conflict with touch scrolling | Mobile users cannot scroll within simulation area | Use `touch-action: none` only on drag handles, not on content areas |
| SVG filter performance on low-end devices | Color blindness simulation causes frame drops | Test on low-end hardware; provide graceful fallback (static filter application) |
| Tunnel vision cursor tracking performance | `mousemove` handler on every pixel causes jank | Throttle handler to 60fps using `requestAnimationFrame`; use CSS custom properties for GPU-composited updates |
| Motor impairment simulation confuses users | Users think the app is broken | Clear "Simulation Active" indicator banner at top of simulation area; prominent "Turn Off" button |
| Dyslexia simulation accessibility | Simulation itself may trigger reactions in photosensitive users | 500ms shuffle interval well below 3Hz threshold; no flashing; respect `prefers-reduced-motion` |
| VLibras CDN unavailability | Widget fails to load; Libras inaccessible | `next/Script` with `lazyOnload` handles gracefully; show fallback message if script fails to load; does not block page |
| DOMPurify stripping necessary ARIA attributes | Accessible HTML variants lose semantic meaning | Explicit ARIA allowlist in DOMPurify config; test all 9 variants post-sanitization |
| Direct DOM theme switching causes hydration mismatch | SSR/client mismatch warning in Next.js | Cookie-based SSR theme (ADR-019) ensures server-rendered theme matches; `data-theme` set in both SSR and client |

---

## Test Plan

- **Component tests (React Testing Library):**
  - Export comparison: variant selection, pane rendering, divider keyboard
    control, DOMPurify sanitization, diff highlight rendering
  - Visual schedule: step rendering, type color mapping, print layout
  - Persona toggle: button activation, sliding pill animation (mock
    framer-motion layout), radio behavior, direct DOM `data-theme` switching
  - A11y twin: tab switching, diff highlight rendering, persona selector,
    screen reader announcements, ARIA attributes
  - Simulate disability: simulation activation, disclaimer flow, scoped
    application, SVG filter references, `useDyslexiaSimulator` hook behavior
  - VLibras widget: DOM structure rendering, script loading, client-only rendering

- **Hook tests (unit):**
  - `useDyslexiaSimulator`: shuffles inner letters correctly, preserves
    first/last chars, 500ms interval fires, deactivation restores original text

- **Accessibility tests (axe-core):**
  - All components pass axe-core with zero violations
  - Keyboard navigation verified for all interactive elements
  - ARIA roles and labels verified on slider, radiogroup, separator
  - VLibras widget does not introduce accessibility violations

- **Visual tests:**
  - Each simulation type screenshot-verified (manual for MVP)
  - Split-pane renders correctly at various divider positions
  - Timeline renders in both horizontal and vertical layouts
  - All 9 themes tested with each component
  - Sliding pill animation verified (stiffness/damping feel check)
  - Diff highlights visible in export comparison

- **Performance tests:**
  - Tunnel vision: cursor tracking stays at 60fps (RAF throttle)
  - Motor simulation: no perceptible lag outside the intentional 300ms delay
  - Dyslexia simulation: no layout shifts or reflows outside simulation area
  - VLibras: does not impact Largest Contentful Paint (lazy loaded)
  - Theme switching: no visible frame drop (direct DOM, no React re-render)

- **Security tests:**
  - DOMPurify sanitization: verify XSS payloads in variant HTML are stripped
  - DOMPurify allowlist: verify ARIA attributes preserved, data-* stripped

- **Ethical review:**
  - Disclaimer text reviewed for accuracy and sensitivity
  - Simulation scoping verified: no effects leak outside `#simulation-target`
  - "Off" button immediately and completely removes all effects
  - Dyslexia simulation frequency verified below 3Hz photosensitivity threshold
