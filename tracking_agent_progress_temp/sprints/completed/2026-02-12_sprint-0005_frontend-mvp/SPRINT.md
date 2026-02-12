# Sprint 0005 — Frontend MVP

**Status:** planned | **Date:** 2026-02-12 to 2026-02-13
**Goal:** Next.js 16 app with pipeline viewer, plan tabs, score gauge, i18n,
WCAG AAA design system with 9 persona modes.

---

## Scope & Acceptance Criteria

Build the complete frontend application for AiLine using Next.js 16 (App Router,
React 19.2, Turbopack). The frontend must implement a WCAG AAA-compliant design
system with 9 persona-specific themes (Standard, High Contrast, TEA/Autism,
TDAH/ADHD, Dyslexia, Low Vision, Hearing, Motor, Screen Reader). It must
include: a responsive layout with sidebar navigation, internationalization in
3 locales (EN/PT-BR/ES), a real-time pipeline viewer with SSE, tabbed plan
views (Teacher/Student/Report/Exports), an animated accessibility score gauge,
and a persona preferences panel. The design system uses CSS custom properties
so all 9 themes can be switched instantly via a single body class.

---

## Key Technology Decisions

Verified against latest documentation (Next.js 16, React 19.2, Tailwind v4):

- **Next.js 16:** App Router (default), React 19.2 support (View Transitions,
  useEffectEvent, Activity component), Turbopack as default bundler, React
  Compiler 1.0 stable (auto-memoization).
- **Tailwind CSS v4:** CSS-first configuration (no `tailwind.config.js`), native
  CSS custom properties, `@theme` directive for token registration.
- **shadcn/ui:** Radix UI primitives + Tailwind styling. Requires significant
  customization to meet AAA contrast ratios (7:1 minimum for normal text).
- **Zustand 5.x:** Lightweight state management with middleware for
  `localStorage` persistence. Used for theme store, pipeline state, plan cache.
- **motion 12.x (formerly framer-motion):** Animation library with first-class
  `prefers-reduced-motion` support via `useReducedMotion()` hook. Package
  renamed from `framer-motion` to `motion`; same API, new canonical name.
- **next-intl 4.x:** Server-component-compatible i18n with ~200 translation
  keys across EN, PT-BR, ES.
- **Recharts 3.7.0:** SVG-based charts (used for score gauge). v3 rewrite with
  hooks API (`useXAxisDomain`, `useYAxisDomain`), custom React components in SVG
  tree, z-index support. Breaking: `CategoricalChartState` removed, `Customized`
  no longer receives internal state. Accessible with ARIA attributes.

**Package versions (pinned):**
```json
{
  "next": "16.x",
  "react": "19.2.x",
  "react-dom": "19.2.x",
  "tailwindcss": "4.x",
  "zustand": "5.x",
  "motion": "12.x",
  "next-intl": "4.x",
  "recharts": "3.x",
  "@microsoft/fetch-event-source": "2.x",
  "radix-ui": "latest",
  "lucide-react": "latest",
  "class-variance-authority": "latest",
  "clsx": "latest",
  "tailwind-merge": "latest"
}
```

---

## Design System Architecture: CSS Variable Theme Engine

The theme engine uses CSS custom properties on `:root` overridden by
`[data-theme]` attribute selectors. This approach enables instant theme
switching without re-rendering the React tree. All shadcn/ui components
reference these variables instead of hardcoded Tailwind colors.

### WCAG AAA Color Palette (Exact Hex Values)

All color values verified for WCAG AAA compliance (7:1 minimum contrast
for normal text, 4.5:1 for large text).

**Light Theme (default):**

| Token | Hex | Source | Usage |
|-------|-----|--------|-------|
| `--canvas` | `#F8FAFC` | Slate 50 | Page background |
| `--surface-1` | `#FFFFFF` | White | Card backgrounds |
| `--surface-2` | `#F1F5F9` | Slate 100 | Hover states, input backgrounds |
| `--surface-3` | `#E2E8F0` | Slate 200 | Active states, borders |
| `--text-body` | `#0F172A` | Slate 900 | Primary text (19:1 contrast on canvas) |
| `--text-muted` | `#475569` | Slate 600 | Secondary text (7:1 contrast on canvas) |
| `--primary` | `#1D4ED8` | Blue 700 | AAA-compliant on white surfaces |
| `--success` | `#15803D` | Green 700 | Success states |
| `--error` | `#B91C1C` | Red 700 | Error states |
| `--warning` | `#B45309` | Amber 700 | Warning states |
| `--info` | `#0369A1` | Sky 700 | Info states |

**Dark Theme:**

| Token | Hex | Source | Usage |
|-------|-----|--------|-------|
| `--canvas` | `#020617` | Slate 950 | Page background |
| `--surface-1` | `#0F172A` | Slate 900 | Card backgrounds |
| `--surface-2` | `#1E293B` | Slate 800 | Hover states, input backgrounds |
| `--surface-3` | `#334155` | Slate 700 | Active states, borders |
| `--text-body` | `#F8FAFC` | Slate 50 | Primary text (16:1 contrast on canvas) |
| `--text-muted` | `#CBD5E1` | Slate 300 | Secondary text (10:1 contrast on canvas) |
| `--primary` | `#60A5FA` | Blue 400 | Primary actions |
| `--success` | `#4ADE80` | Green 400 | Success states |
| `--error` | `#F87171` | Red 400 | Error states |
| `--warning` | `#FBBF24` | Amber 400 | Warning states |
| `--info` | `#38BDF8` | Sky 400 | Info states |

### Typography Scale (Tailwind v4 @theme)

All sizes use rem units for user zoom compatibility. 18px body base ensures
WCAG AAA readability. Scale ratios optimized for hierarchical clarity.

| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `--text-xs` | `0.875rem` (14px) | `1.5` | Captions, badges |
| `--text-sm` | `1rem` (16px) | `1.5` | Labels, metadata |
| `--text-base` | `1.125rem` (18px) | `1.6` | Body text (base) |
| `--text-lg` | `1.25rem` (20px) | `1.6` | Subheadings |
| `--text-xl` | `1.5rem` (24px) | `1.4` | h4 headings |
| `--text-2xl` | `1.875rem` (30px) | `1.3` | h3 headings |
| `--text-3xl` | `2.25rem` (36px) | `1.2` | h2 headings |
| `--text-4xl` | `3rem` (48px) | `1.1` | h1 headings |

**Font loading strategy (next/font/google with CSS variable approach):**

```tsx
// app/layout.tsx
import { Inter } from "next/font/google";
import localFont from "next/font/local";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
});

// Atkinson Hyperlegible for dyslexia/low-vision personas
const atkinson = localFont({
  src: "../public/fonts/AtkinsonHyperlegible-Regular.woff2",
  variable: "--font-atkinson",
  display: "swap",
});

// Applied in layout:
// <body className={`${inter.variable} ${atkinson.variable}`}>
// CSS then picks the right family per [data-theme]:
//   :root { --font-reading: var(--font-inter); }
//   [data-theme="dyslexia"] { --font-reading: var(--font-atkinson); }
```

### 9 Persona Themes (CSS Implementation)

```css
@import "tailwindcss";

/* --- Tailwind v4 @theme: register semantic tokens as Tailwind utilities --- */
@theme {
  --color-canvas: var(--canvas);
  --color-surface-1: var(--surface-1);
  --color-surface-2: var(--surface-2);
  --color-surface-3: var(--surface-3);
  --color-text-body: var(--text-body);
  --color-text-muted: var(--text-muted);
  --color-primary: var(--primary);
  --color-success: var(--success);
  --color-error: var(--error);
  --color-warning: var(--warning);
  --color-info: var(--info);
  --font-reading: var(--font-reading);
  --font-size-base: var(--text-base);
}

/* --- 1. Standard (default) — WCAG AAA Light Theme --- */
:root {
  --canvas: #F8FAFC;
  --surface-1: #FFFFFF;
  --surface-2: #F1F5F9;
  --surface-3: #E2E8F0;
  --text-body: #0F172A;
  --text-muted: #475569;
  --primary: #1D4ED8;
  --success: #15803D;
  --error: #B91C1C;
  --warning: #B45309;
  --info: #0369A1;
  --font-reading: "Inter", system-ui, sans-serif;
  --font-size-base: 1.125rem;
  --line-height: 1.6;
  --letter-spacing: 0;
  --touch-target-min: 48px;
  --spacing-unit: 4px;
  --border-radius: 8px;
  --transition-duration: 200ms;
  --focus-ring: 0 0 0 3px var(--primary);

  /* Typography scale */
  --text-xs: 0.875rem;
  --text-sm: 1rem;
  --text-base: 1.125rem;
  --text-lg: 1.25rem;
  --text-xl: 1.5rem;
  --text-2xl: 1.875rem;
  --text-3xl: 2.25rem;
  --text-4xl: 3rem;
}

/* --- 2. High Contrast — WCAG AAA (7:1+ all text) --- */
[data-theme="high-contrast"] {
  --canvas: #000000;
  --surface-1: #1a1a1a;
  --surface-2: #2a2a2a;
  --surface-3: #3a3a3a;
  --text-body: #ffffff;
  --text-muted: #e0e0e0;
  --primary: #4dabf7;
  --success: #4ADE80;
  --error: #F87171;
  --warning: #FBBF24;
  --info: #38BDF8;
}

/* --- 3. TEA (Autism) — Predictable, low stimulation, geometric shapes --- */
[data-theme="tea"] {
  --canvas: #fefef5;
  --surface-1: #f5f5eb;
  --surface-2: #ededdf;
  --surface-3: #d5d5c5;
  --text-body: #2d2d2d;
  --text-muted: #555555;
  --primary: #4a7c59;
  --transition-duration: 0ms;
  --border-radius: 4px;
}

/* --- 4. TDAH (ADHD) — Structured, chunked, warm tones --- */
[data-theme="tdah"] {
  --canvas: #fffbf0;
  --surface-1: #fff8e8;
  --surface-2: #fff0d0;
  --surface-3: #ffe0a0;
  --text-body: #1a1a1a;
  --text-muted: #4a4a4a;
  --primary: #e67e22;
  --border-radius: 12px;
}

/* --- 5. Dyslexia — Atkinson Hyperlegible font, extra spacing --- */
[data-theme="dyslexia"] {
  --canvas: #fdfbf7;
  --text-body: #1e1e1e;
  --text-muted: #4a4a4a;
  --font-reading: "Atkinson Hyperlegible", sans-serif;
  --font-size-base: 1.25rem;
  --line-height: 2.0;
  --letter-spacing: 0.05em;
}

/* --- 6. Low Vision — Large text, high contrast on warm background --- */
[data-theme="low-vision"] {
  --font-size-base: 1.5rem;
  --line-height: 1.8;
  --canvas: #fffff0;
  --text-body: #000000;
  --text-muted: #333333;
  --touch-target-min: 56px;
}

/* --- 7. Hearing — Visual emphasis, no audio reliance --- */
[data-theme="hearing"] {
  --primary: #1D4ED8;
  /* Visual indicator emphasis: borders thicker, icons over sound cues */
}

/* --- 8. Motor — Extra large touch targets, generous spacing --- */
[data-theme="motor"] {
  --touch-target-min: 64px;
  --spacing-unit: 6px;
  --border-radius: 12px;
}

/* --- 9. Screen Reader — Minimal visual changes; ARIA/semantic focus --- */
[data-theme="screen-reader"] {
  /* Structural: enhanced heading hierarchy, landmark roles */
}

/* --- Dark mode variant (applied via data-color-scheme="dark") --- */
[data-color-scheme="dark"] {
  --canvas: #020617;
  --surface-1: #0F172A;
  --surface-2: #1E293B;
  --surface-3: #334155;
  --text-body: #F8FAFC;
  --text-muted: #CBD5E1;
  --primary: #60A5FA;
  --success: #4ADE80;
  --error: #F87171;
  --warning: #FBBF24;
  --info: #38BDF8;
}

/* --- System-level respect --- */
@media (prefers-reduced-motion: reduce) {
  :root { --transition-duration: 0ms; }
}
@media (prefers-contrast: more) {
  :root { /* Apply high-contrast overrides automatically */ }
}
```

---

## Stories

### S5-001: Scaffold Next.js 16 + Tailwind v4 + shadcn/ui [ ]

**Description:** Initialize the Next.js 16 application with App Router,
TypeScript strict mode, Tailwind CSS v4, and shadcn/ui. Set up the project
directory structure and install all dependencies. Configure Turbopack (default
in Next.js 16). **Enable React Compiler 1.0** (`reactCompiler: true` in
`next.config.ts`) for auto-memoization and up to 12% faster loads (ADR-045).
Add **DOMPurify 3.3.1** for HTML export sanitization (ADR-046). Add
**@microsoft/fetch-event-source 2.0.1** for SSE client with POST support.
Load the typeface families needed across persona themes:
Inter (main body font) + Atkinson Hyperlegible (dyslexia/low-vision persona)
via `next/font/google` with the CSS variable approach.

**Font loading implementation:**

```tsx
// frontend/app/layout.tsx
import { Inter } from "next/font/google";
import localFont from "next/font/local";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
});

const atkinson = localFont({
  src: "../public/fonts/AtkinsonHyperlegible-Regular.woff2",
  variable: "--font-atkinson",
  display: "swap",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.variable} ${atkinson.variable}`}>
        {children}
      </body>
    </html>
  );
}
```

The CSS variable approach allows each `[data-theme]` to select the correct
font family by reassigning `--font-reading`:

```css
:root { --font-reading: var(--font-inter); }
[data-theme="dyslexia"] { --font-reading: var(--font-atkinson); }
```

**Files:**
- `frontend/` -- project root directory
- `frontend/package.json` -- dependencies + scripts
- `frontend/tsconfig.json` -- TypeScript strict mode
- `frontend/next.config.ts` -- Next.js 16 configuration
- `frontend/app/layout.tsx` -- root layout with font loading (Inter + Atkinson Hyperlegible)
- `frontend/app/page.tsx` -- landing/dashboard page (placeholder)

**Project structure:**
```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (fonts, providers, metadata)
│   ├── page.tsx            # Dashboard (landing)
│   ├── plans/              # Plan pages
│   ├── materials/          # Materials pages
│   ├── tutors/             # Tutor pages
│   └── settings/           # Settings pages
├── components/
│   ├── ui/                 # shadcn/ui base components
│   ├── layout/             # Sidebar, TopBar, MainLayout
│   ├── pipeline/           # Pipeline viewer components
│   ├── plans/              # Plan tabs components
│   ├── a11y/               # Accessibility score/checklist
│   ├── settings/           # Preferences panel
│   └── demo/               # Demo/wow components (Sprint 6)
├── hooks/                  # Custom React hooks
├── stores/                 # Zustand stores
├── lib/                    # Utilities (cn, api client, etc.)
├── styles/
│   ├── globals.css         # CSS variables, theme definitions
│   └── themes/             # Per-theme override files (if needed)
├── messages/               # i18n JSON files
│   ├── en.json
│   ├── pt-BR.json
│   └── es.json
├── i18n/
│   └── request.ts          # next-intl getRequestConfig
├── proxy.ts            # next-intl locale middleware
└── public/                 # Static assets (fonts, icons)
    └── fonts/
        └── AtkinsonHyperlegible-Regular.woff2
```

**Acceptance Criteria:**
- [ ] `pnpm create next-app@latest` with App Router, TypeScript, Tailwind v4, ESLint
- [ ] shadcn/ui initialized via `pnpm dlx shadcn@latest init`
- [ ] Turbopack enabled (Next.js 16 default)
- [ ] TypeScript strict mode (`"strict": true` in tsconfig.json)
- [ ] All package versions pinned per the versions table above
- [ ] `@microsoft/fetch-event-source` added as dependency for SSE
- [ ] Inter loaded via `next/font/google` with `variable: "--font-inter"`
- [ ] Atkinson Hyperlegible loaded via `next/font/local` with `variable: "--font-atkinson"`
- [ ] Both font CSS variables applied on `<body>` classname
- [ ] `pnpm dev` starts without errors, renders placeholder page
- [ ] `pnpm build` succeeds with zero TypeScript/ESLint errors
- [ ] `pnpm lint` and `pnpm exec tsc --noEmit` pass clean

---

### S5-002: Design System (WCAG AAA, 9 Persona Modes) [ ]

**Description:** Implement the token-based design system with the CSS variable
theme engine described in the Design System Architecture section. Create all 9
persona themes using the exact WCAG AAA hex values specified above. Register
semantic tokens via Tailwind v4's `@theme` directive so utilities like
`bg-canvas`, `text-text-body`, `text-primary` work natively. Customize shadcn/ui
components to reference CSS variables instead of hardcoded Tailwind colors.
Build a Zustand theme store that persists the user's preference to localStorage
and applies the corresponding `data-theme` attribute.

**Exact `globals.css` with @theme integration:**

```css
@import "tailwindcss";

@theme {
  --color-canvas: var(--canvas);
  --color-surface-1: var(--surface-1);
  --color-surface-2: var(--surface-2);
  --color-surface-3: var(--surface-3);
  --color-text-body: var(--text-body);
  --color-text-muted: var(--text-muted);
  --color-primary: var(--primary);
  --color-success: var(--success);
  --color-error: var(--error);
  --color-warning: var(--warning);
  --color-info: var(--info);
  --font-reading: var(--font-reading);
}

:root {
  --canvas: #F8FAFC;
  --surface-1: #FFFFFF;
  --surface-2: #F1F5F9;
  --surface-3: #E2E8F0;
  --text-body: #0F172A;
  --text-muted: #475569;
  --primary: #1D4ED8;
  --success: #15803D;
  --error: #B91C1C;
  --warning: #B45309;
  --info: #0369A1;
  --font-reading: "Inter", system-ui, sans-serif;
  --font-size-base: 1.125rem;
  --line-height: 1.6;
  --letter-spacing: 0;
  --touch-target-min: 48px;
  --spacing-unit: 4px;
  --border-radius: 8px;
  --transition-duration: 200ms;
  --focus-ring: 0 0 0 3px var(--primary);
}

/* Then all 9 [data-theme="..."] blocks as shown in the
   Design System Architecture section above. */
```

This produces Tailwind utilities: `bg-canvas`, `bg-surface-1`, `text-text-body`,
`text-text-muted`, `text-primary`, `bg-success`, `bg-error`, etc. All driven by
CSS variables, all theme-switchable at runtime.

**Files:**
- `frontend/styles/globals.css` -- all CSS variable definitions for 9 themes +
  @theme directive
- `frontend/stores/theme-store.ts` -- Zustand store for persona/theme state
- `frontend/components/ui/button.tsx` -- customized shadcn button (example)
- `frontend/components/ui/card.tsx` -- customized shadcn card (example)
- `frontend/components/ui/input.tsx` -- customized shadcn input (example)
- `frontend/lib/cn.ts` -- className merge utility (clsx + tailwind-merge)

**Theme store API:**
```typescript
interface ThemeStore {
  persona: PersonaMode;  // 'standard' | 'high-contrast' | 'tea' | 'tdah' | 'dyslexia' | 'low-vision' | 'hearing' | 'motor' | 'screen-reader'
  fontSize: number;      // 14-32px
  lineHeight: number;    // 1.2-2.5
  animationsEnabled: boolean;
  setPersona: (mode: PersonaMode) => void;
  setFontSize: (size: number) => void;
  setLineHeight: (height: number) => void;
  toggleAnimations: () => void;
}
```

**Theme switching mechanism (data-theme attribute, not CSS class):**
`document.body.setAttribute('data-theme', 'dyslexia')` — pure CSS cascade,
no React re-render for styling changes. The `data-theme` attribute approach
is preferred over body class toggling because it keeps the attribute namespace
separate from utility classes and enables cleaner CSS specificity rules.

**Acceptance Criteria:**
- [ ] CSS variables defined for all 9 themes using exact hex values from the
      WCAG AAA Color Palette tables above (Light: canvas #F8FAFC, text-body
      #0F172A 19:1 contrast, text-muted #475569 7:1 contrast, primary #1D4ED8;
      Dark: canvas #020617, text-body #F8FAFC 16:1 contrast, text-muted #CBD5E1
      10:1 contrast, primary #60A5FA)
- [ ] Typography scale implemented per the Typography Scale table: text-xs
      0.875rem/1.5 through text-4xl 3rem/1.1, with 18px (1.125rem) body base
- [ ] Tailwind v4 `@theme` directive registers all semantic tokens
      (`--color-canvas`, `--color-surface-1`, `--color-surface-2`,
      `--color-surface-3`, `--color-text-body`, `--color-text-muted`,
      `--color-primary`, `--color-success`, `--color-error`, `--color-warning`,
      `--color-info`, `--font-reading`) so Tailwind utilities like `bg-canvas`
      and `text-text-body` work natively
- [ ] Theme switching uses `data-theme` attribute on `<body>` (not CSS class)
- [ ] Theme store (Zustand) persists persona preference to localStorage
- [ ] Changing persona immediately applies the correct `data-theme` attribute
      (e.g., `document.body.setAttribute('data-theme', 'tea')`)
- [ ] `prefers-reduced-motion` media query respected: when enabled, all
      transitions use 0ms duration
- [ ] `prefers-contrast: more` media query respected: auto-applies high
      contrast overrides
- [ ] All shadcn/ui components reference `var(--color-*)` variables, not
      hardcoded hex values or Tailwind color classes
- [ ] 18px minimum base font size enforced across all themes
- [ ] 48px minimum touch target enforced for all interactive elements
- [ ] Focus indicators visible on all interactive elements: 3px ring using
      `var(--focus-ring)` on `:focus-visible`
- [ ] WCAG AAA contrast ratio (7:1) verified for all theme/text combinations
      using a contrast checker (manual or automated)
- [ ] Unit test: theme store persists and restores from localStorage

---

### S5-003: Layout (Sidebar + TopBar + Responsive) [ ]

**Description:** Build the responsive application layout with three components:
sidebar navigation (desktop), top bar with user menu and controls, and mobile
navigation via shadcn Sheet component. The layout must adapt between desktop
(sidebar + content) and mobile (sheet overlay) breakpoints. Includes
skip-to-content link, ARIA landmarks, and keyboard navigation.

**Sidebar implementation (Desktop):**

```tsx
// frontend/components/layout/sidebar.tsx
// Desktop: aside element, 64px wide (icon-only), border-right, sticky top-0
// Expands to 280px on hover or toggle

const NAV_ITEMS = [
  { href: "/", label: "nav.dashboard", icon: LayoutDashboard },
  { href: "/plans", label: "nav.plans", icon: ClipboardList },
  { href: "/materials", label: "nav.materials", icon: BookOpen },
  { href: "/tutors", label: "nav.tutors", icon: GraduationCap },
  { href: "/settings", label: "nav.settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-16 flex-col border-r border-surface-3 sticky top-0 h-screen">
      <nav aria-label="Main navigation">
        <ul role="list">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={pathname === item.href ? "page" : undefined}
                className="touch-target flex items-center justify-center min-h-12 min-w-12"
              >
                <item.icon className="h-5 w-5" aria-hidden="true" />
                <span className="sr-only">{t(item.label)}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
```

**Mobile navigation (shadcn Sheet):**

```tsx
// frontend/components/layout/mobile-nav.tsx
// Uses shadcn Sheet component with Menu trigger button
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu } from "lucide-react";

export function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          className="lg:hidden touch-target min-h-12 min-w-12"
          aria-label={t("nav.openMenu")}
        >
          <Menu className="h-6 w-6" />
        </button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 bg-surface-1">
        <nav aria-label="Main navigation">
          {/* Same NAV_ITEMS rendered as full-width links */}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
```

**Touch target utility class:**

```css
/* Ensures WCAG minimum touch target size across all themes */
.touch-target {
  min-height: var(--touch-target-min, 48px);
  min-width: var(--touch-target-min, 48px);
}
```

**Files:**
- `frontend/components/layout/main-layout.tsx` -- orchestrates sidebar + topbar + content area
- `frontend/components/layout/sidebar.tsx` -- desktop sidebar (64w border-r sticky top-0)
- `frontend/components/layout/topbar.tsx` -- top bar (user menu, language, persona)
- `frontend/components/layout/mobile-nav.tsx` -- mobile navigation via shadcn Sheet
- `frontend/components/layout/skip-link.tsx` -- skip-to-content accessibility link

**Navigation items (NAV_ITEMS array with icon components):**
1. Dashboard (`LayoutDashboard` icon) -- `/`
2. Plans (`ClipboardList` icon) -- `/plans`
3. Materials (`BookOpen` icon) -- `/materials`
4. Tutors (`GraduationCap` icon) -- `/tutors`
5. Settings (`Settings` icon) -- `/settings`

**Acceptance Criteria:**
- [ ] Desktop (>=1024px): 64px sidebar (icon-only, `aside` element, `border-r`,
      `sticky top-0 h-screen`) + topbar
- [ ] Sidebar can expand to 280px on hover or explicit toggle; collapse state
      persisted to localStorage
- [ ] Sidebar shows: navigation items with Lucide icons, persona mode
      mini-switcher, app logo
- [ ] Topbar shows: breadcrumb, language switcher, persona indicator, user menu
- [ ] Mobile (<1024px): shadcn Sheet component with Menu trigger button,
      sliding overlay from left, 72-wide content area
- [ ] All navigation links use `aria-current="page"` when route matches
- [ ] All interactive elements use `.touch-target` class ensuring minimum
      `var(--touch-target-min)` dimensions (48px default, 64px in motor theme)
- [ ] Skip-to-content link: visually hidden, appears on focus, jumps to
      `<main id="main-content">`
- [ ] ARIA landmarks: `<nav aria-label="Main navigation">`,
      `<main role="main">`, `<aside>` for sidebar
- [ ] Keyboard navigation: Tab through nav items, Enter/Space to activate
- [ ] Layout renders correctly in all 9 persona themes

---

### S5-004: i18n (EN/PT-BR/ES, ~200 keys) [ ]

**Description:** Set up internationalization with next-intl v4 for 3 locales.
Create ~200 translation keys covering all UI elements. Default locale is PT-BR
(primary target audience is Brazilian educators). Language switcher in the
topbar allows changing locale. All date and number formatting respects locale.

**next-intl v4 setup (exact implementation):**

```typescript
// frontend/i18n/request.ts
import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const locale = cookieStore.get("NEXT_LOCALE")?.value ?? "pt-BR";

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
```

```typescript
// frontend/proxy.ts (Next.js 16 renamed middleware.ts to proxy.ts)
import createMiddleware from "next-intl/middleware";

export default createMiddleware({
  locales: ["en", "pt-BR", "es"],
  defaultLocale: "pt-BR",
  localePrefix: "as-needed",  // No /pt-BR prefix for default locale
});

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
```

**Messages structure:**

```
messages/
├── en.json       # English (~200 keys)
├── pt-BR.json    # Brazilian Portuguese (~200 keys, default)
└── es.json       # Spanish (~200 keys)
```

**Files:**
- `frontend/i18n/request.ts` -- next-intl v4 getRequestConfig reading locale
  from cookie
- `frontend/proxy.ts` -- next-intl createMiddleware with locales
  `["en", "pt-BR", "es"]`, defaultLocale `"pt-BR"`, localePrefix `"as-needed"`
  (Next.js 16 renamed middleware.ts to proxy.ts)
- `frontend/messages/en.json` -- English translations (~200 keys)
- `frontend/messages/pt-BR.json` -- Brazilian Portuguese translations (~200 keys)
- `frontend/messages/es.json` -- Spanish translations (~200 keys)
- `frontend/components/layout/language-switcher.tsx` -- locale selector dropdown

**Translation key categories (~200 total):**
```
common.*       (30 keys)  -- buttons, labels, status words
nav.*          (10 keys)  -- navigation item labels
pipeline.*     (20 keys)  -- stage names, status messages
plans.*        (40 keys)  -- tab labels, plan fields, instructions
a11y.*         (30 keys)  -- checklist items, score labels, recommendations
settings.*     (20 keys)  -- preferences panel labels
materials.*    (15 keys)  -- upload, search, metadata
tutors.*       (15 keys)  -- session labels, chat interface
errors.*       (10 keys)  -- error messages, retry prompts
demo.*         (10 keys)  -- demo mode labels
```

**Acceptance Criteria:**
- [ ] next-intl v4 configured with `getRequestConfig` in `i18n/request.ts`
      reading locale from cookie
- [ ] Proxy uses `createMiddleware` in `proxy.ts` (Next.js 16 pattern) with
      `localePrefix: "as-needed"` (no URL prefix for default pt-BR locale)
- [ ] Language switcher in topbar (dropdown: EN / PT-BR / ES)
- [ ] All visible UI text uses `t("key")` -- zero hardcoded strings in components
- [ ] PT-BR set as default locale
- [ ] Date formatting per locale (e.g., DD/MM/YYYY for PT-BR, MM/DD/YYYY for EN)
- [ ] Number formatting per locale (e.g., 1.000,50 for PT-BR, 1,000.50 for EN)
- [ ] Locale persisted in cookie (`NEXT_LOCALE`) and optionally in URL path
      prefix for non-default locales
- [ ] RTL-ready layout structure: all layout uses logical CSS properties
      (`margin-inline-start` over `margin-left`) for future Arabic/Hebrew support
- [ ] Missing key fallback: shows key name in development, falls back to EN in
      production
- [ ] All 3 locale files have identical key sets (build-time validation)

---

### S5-005: Pipeline Run Viewer (SSE Stepper) [ ]

**Description:** Build a real-time pipeline progress visualization that shows
the 6 stages of the AiLine plan generation pipeline. This is the "Glass Box"
AI pattern -- the single most impressive feature for hackathon judges. Instead
of a black-box spinner, show the internal reasoning steps of the AI pipeline in
real time. Connected to the backend via Server-Sent Events (SSE) using
`@microsoft/fetch-event-source` for auto-reconnect and POST method support.

**Pipeline stages (6):**
1. **Context** -- Gather context and requirements
2. **Planner** -- DeepAgents generates the lesson plan outline
3. **Quality** -- Accessibility checklist scores the draft
4. **Refine** -- Plan iterates if score is below threshold
5. **Execute** -- Claude expands into full teacher + student plans
6. **Format** -- Export variants generated, results ready

**SSE Hook implementation (useSSE with @microsoft/fetch-event-source):**

```typescript
// frontend/hooks/use-sse.ts
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { usePipelineStore } from "@/stores/pipeline-store";

interface UseSSEOptions {
  url: string;
  payload: Record<string, unknown>;
  onOpen?: () => void;
  onError?: (err: Error) => void;
}

export function useSSE({ url, payload, onOpen, onError }: UseSSEOptions) {
  const { handleEvent } = usePipelineStore();
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "error">("idle");

  const connect = useCallback(() => {
    setStatus("connecting");
    const ctrl = new AbortController();

    fetchEventSource(url, {
      method: "POST",                    // POST for initial payload
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,

      onopen: async (res) => {
        if (res.ok) {
          setStatus("connected");
          onOpen?.();
        }
      },
      onmessage: (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data);              // Dispatch to Zustand store
      },
      onerror: (err) => {
        setStatus("error");
        onError?.(err);
        // Auto-reconnect is built into @microsoft/fetch-event-source
      },
      onclose: () => {
        setStatus("idle");
      },
    });

    // Cleanup on unmount
    return () => ctrl.abort();
  }, [url, payload, handleEvent, onOpen, onError]);

  return { connect, status };
}
```

**Zustand Pipeline Store:**

```typescript
// frontend/stores/pipeline-store.ts
import { create } from "zustand";

interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "active" | "done" | "error";
  details: string | null;
  startedAt: number | null;
  completedAt: number | null;
}

// Stage name mapping: backend event names -> UI labels
const STAGE_MAP: Record<string, string> = {
  context_gathering: "context",
  planning: "planner",
  quality_check: "quality",
  refinement: "refine",
  execution: "execute",
  formatting: "format",
};

const INITIAL_STEPS: PipelineStep[] = [
  { id: "context", label: "pipeline.context", status: "pending", details: null, startedAt: null, completedAt: null },
  { id: "planner", label: "pipeline.planner", status: "pending", details: null, startedAt: null, completedAt: null },
  { id: "quality", label: "pipeline.quality", status: "pending", details: null, startedAt: null, completedAt: null },
  { id: "refine",  label: "pipeline.refine",  status: "pending", details: null, startedAt: null, completedAt: null },
  { id: "execute", label: "pipeline.execute", status: "pending", details: null, startedAt: null, completedAt: null },
  { id: "format",  label: "pipeline.format",  status: "pending", details: null, startedAt: null, completedAt: null },
];

interface PipelineStore {
  steps: PipelineStep[];
  currentStepId: string | null;
  error: string | null;
  handleEvent: (event: SSEEvent) => void;
  reset: () => void;
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  steps: [...INITIAL_STEPS],
  currentStepId: null,
  error: null,

  handleEvent: (event) => {
    set((state) => {
      const stageId = STAGE_MAP[event.stage] ?? event.stage;

      switch (event.type) {
        case "stage_start":
          return {
            steps: state.steps.map((s) =>
              s.id === stageId
                ? { ...s, status: "active", startedAt: Date.now() }
                : s
            ),
            currentStepId: stageId,
          };

        case "stage_progress":
          return {
            steps: state.steps.map((s) =>
              s.id === stageId ? { ...s, details: event.message } : s
            ),
          };

        case "stage_complete":
          return {
            steps: state.steps.map((s) =>
              s.id === stageId
                ? { ...s, status: "done", completedAt: Date.now(), details: event.message }
                : s
            ),
          };

        case "stage_error":
          return {
            steps: state.steps.map((s) =>
              s.id === stageId
                ? { ...s, status: "error", details: event.message }
                : s
            ),
            error: event.message,
          };

        default:
          return state;
      }
    });
  },

  reset: () => set({ steps: [...INITIAL_STEPS], currentStepId: null, error: null }),
}));
```

**Glass Box Pipeline Viewer (Stage Cards with scanning animation):**

```tsx
// frontend/components/pipeline/stage-card.tsx
import { AnimatePresence, motion } from "motion/react";

interface StageCardProps {
  step: PipelineStep;
  isActive: boolean;
}

export function StageCard({ step, isActive }: StageCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-lg border p-4 bg-surface-1",
        isActive && "border-primary ring-2 ring-primary/20"
      )}
    >
      {/* Scanning animation gradient sweep for active state */}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-lg overflow-hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/10 to-transparent"
            animate={{ x: ["-100%", "100%"] }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
          />
        </motion.div>
      )}

      {/* Stage content */}
      <div className="relative z-10">
        <StageIcon status={step.status} />
        <span className="text-text-body font-medium">{t(step.label)}</span>
        <StatusBadge status={step.status} />
      </div>

      {/* Glass Box: reasoning text reveal with AnimatePresence */}
      <AnimatePresence>
        {step.details && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-2 text-sm text-text-muted overflow-hidden"
          >
            {step.details}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Files:**
- `frontend/components/pipeline/pipeline-viewer.tsx` -- main stepper component
- `frontend/components/pipeline/stage-card.tsx` -- individual stage card with
  scanning animation and AnimatePresence reasoning text reveal
- `frontend/hooks/use-sse.ts` -- SSE hook using `@microsoft/fetch-event-source`
  with POST method, auto-reconnect, and Zustand dispatch
- `frontend/stores/pipeline-store.ts` -- Zustand store with 6 initial steps,
  handleEvent reducer, stage name mapping, and reset()

**SSE event → store flow:**
1. `useSSE` connects to backend via `fetchEventSource` (POST method with payload)
2. Each SSE message is parsed and dispatched via `handleEvent` to the Zustand store
3. Store maps backend stage names to UI step IDs via `STAGE_MAP`
4. `handleEvent` reducer handles: `stage_start`, `stage_progress`,
   `stage_complete`, `stage_error`
5. Components subscribe to store slices and re-render on step status changes
6. Connection status tracked in hook state (idle/connecting/connected/error)
7. Cleanup: `AbortController.abort()` on component unmount

**Acceptance Criteria:**
- [ ] 6-stage horizontal stepper (desktop) / vertical stepper (mobile)
- [ ] Stage IDs: context, planner, quality, refine, execute, format
- [ ] Each stage shows: Lucide icon, localized label, status badge
      (pending/active/done/error), elapsed time
- [ ] Active stage has scanning animation (gradient sweep via framer-motion) --
      respects `prefers-reduced-motion` (no animation when reduced motion enabled)
- [ ] Completed stages show green checkmark and elapsed time
- [ ] Error stages show red X icon and error message
- [ ] Glass Box detail panel: AnimatePresence-driven expandable area beneath
      each stage card showing reasoning/progress text streamed via SSE
- [ ] LLM model badge on each stage card showing active model name + icon
- [ ] SSE hook uses `@microsoft/fetch-event-source` with POST method for
      initial payload
- [ ] Auto-reconnect built into fetch-event-source
- [ ] SSE connection to `POST /api/v1/plans/{run_id}/events`
- [ ] Zustand store with 6 initial steps (INITIAL_STEPS), stage name mapping
      (STAGE_MAP), handleEvent reducer, and reset() function
- [ ] Connection status tracking (idle/connecting/connected/error) in SSE hook
- [ ] Cleanup: AbortController.abort() on component unmount
- [ ] Pipeline state persisted in Zustand store (survives component remount)
- [ ] Screen reader: `aria-live="polite"` region announces stage transitions
- [ ] Stepper uses `role="progressbar"` with `aria-valuenow` (current stage index)
- [ ] Loading skeleton shown while waiting for first SSE event
- [ ] Works in all 9 persona themes

---

### S5-006: Plan Tabs (Teacher/Student/Report/Exports) [ ]

**Description:** Build a tabbed interface for viewing plan generation results.
Four tabs present different perspectives on the same plan: Teacher Plan (full
pedagogical detail), Student Plan (simplified/adapted), Accessibility Report
(score + checklist), and Exports (9 format variants). Uses Radix UI Tabs
primitive for full keyboard accessibility.

**Files:**
- `frontend/components/plans/plan-tabs.tsx` -- tab container (Radix Tabs)
- `frontend/components/plans/teacher-plan.tsx` -- teacher-facing plan view
- `frontend/components/plans/student-plan.tsx` -- student-facing plan view
- `frontend/components/plans/a11y-report.tsx` -- accessibility report tab
- `frontend/components/plans/exports-view.tsx` -- export variants grid

**Teacher Plan tab content:**
- Structured steps with: sequence number, title, duration, instruction text
- Assessment criteria per step
- Curriculum alignment indicators (BNCC/CCSS codes shown)
- Materials/resources list
- Accessibility adaptations highlighted

**Student Plan tab content:**
- Simplified language (adapted to student reading level)
- Visual step indicators (icons + colors)
- Self-regulation prompts ("How are you feeling about this?")
- Break reminders
- Accessibility adaptations applied (persona-specific)

**A11y Report tab content:**
- Score gauge component (see S5-007)
- Checklist organized by category: Structure, Cognitive, Predictability, Media
- Each checklist item: pass/warn/fail status + description + recommendation
- Overall summary with key findings
- "Fix with AI" button (see S5-007 for implementation)

**Exports tab content:**
- 3x3 grid of export variants (9 total)
- Each card: variant name, preview thumbnail, download button
- Variants: standard_html, low_distraction_html, large_print_html,
  high_contrast_html, dyslexia_friendly_html, screen_reader_html,
  visual_schedule_html, student_plain_text, audio_script

**Acceptance Criteria:**
- [ ] 4 tabs with Radix UI Tabs primitive
- [ ] Keyboard navigation: Arrow Left/Right between tabs, Home/End to first/last
- [ ] Tab panels lazy-loaded (only render active panel content)
- [ ] Teacher Plan: all structured fields rendered with clear hierarchy
- [ ] Student Plan: simplified language with visual cues
- [ ] A11y Report: integrates score gauge + expandable checklist + "Fix with AI"
      button
- [ ] Exports: 3x3 responsive grid with preview/download for each variant
- [ ] All text content uses `t()` for i18n
- [ ] Tab labels have ARIA: `role="tablist"`, `role="tab"`, `role="tabpanel"`,
      `aria-selected`, `aria-controls`
- [ ] Empty state: meaningful message when plan data is not yet loaded
- [ ] Loading state: skeleton placeholders per tab

---

### S5-007: Score Gauge (framer-motion SVG) + Checklist [ ]

**Description:** Build an animated circular score gauge (0-100) showing the
plan's accessibility score, and an expandable checklist showing individual
accessibility criteria results. The gauge uses SVG ring animation via
framer-motion with `useMotionValue` + `useTransform` for smooth animated
counting and dynamic color interpolation without React state re-renders.
Includes a "Fix with AI" call-to-action button with Sparkles icon and
pulse animation.

**Exact framer-motion Score Gauge implementation:**

```tsx
// frontend/components/a11y/score-gauge.tsx
"use client";

import { useEffect } from "react";
import {
  motion,
  useMotionValue,
  useTransform,
  animate,
  useReducedMotion,
} from "motion/react";
import { Sparkles } from "lucide-react";

interface ScoreGaugeProps {
  score: number;  // 0-100
}

export function ScoreGauge({ score }: ScoreGaugeProps) {
  const prefersReducedMotion = useReducedMotion();

  // Motion value for animated counter (avoids React state re-renders)
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));

  // Color interpolation across score ranges
  const color = useTransform(
    count,
    [0, 50, 80, 100],
    ["#ef4444", "#f59e0b", "#10b981", "#14b8a6"]
  );

  // Animate on mount or score change
  useEffect(() => {
    const controls = animate(count, score, {
      duration: prefersReducedMotion ? 0 : 1.5,
      ease: "circOut",
    });
    return controls.stop;
  }, [score, count, prefersReducedMotion]);

  // SVG parameters
  const size = 200;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div
      role="meter"
      aria-valuenow={score}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Accessibility score: ${score} out of 100`}
      className="relative inline-flex items-center justify-center"
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-3)"
          strokeWidth={strokeWidth}
        />
        {/* Animated foreground ring */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          pathLength={1}
          style={{
            pathLength: useTransform(count, [0, 100], [0, 1]),
            rotate: "-90deg",
            transformOrigin: "center",
          }}
        />
      </svg>

      {/* Centered score number */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-4xl font-bold text-text-body"
          style={{ color }}
        >
          {rounded}
        </motion.span>
        <span className="text-sm text-text-muted">/100</span>
      </div>
    </div>
  );
}
```

**"Fix with AI" button (shown when score < 80):**

```tsx
// Inside a11y-report.tsx, below the ScoreGauge
{score < 80 && (
  <motion.button
    className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-white font-medium"
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
  >
    <motion.span
      animate={{ opacity: [1, 0.5, 1] }}
      transition={{ repeat: Infinity, duration: 2 }}
    >
      <Sparkles className="h-4 w-4" />
    </motion.span>
    {t("a11y.fixWithAI")}
  </motion.button>
)}
```

**Score ranges and colors:**
| Range | Color | Label |
|-------|-------|-------|
| 0-39 | `#ef4444` (Red) | Needs Improvement |
| 40-69 | `#f59e0b` (Amber) | Acceptable |
| 70-89 | `#10b981` (Emerald) | Good |
| 90-100 | `#14b8a6` (Teal) | Excellent |

**Checklist categories:**
1. **Structure** (5-8 items): headings hierarchy, logical reading order, clear
   sections, table accessibility
2. **Cognitive** (5-8 items): reading level, sentence complexity, vocabulary,
   chunking, visual aids
3. **Predictability** (3-5 items): consistent layout, clear instructions,
   transition warnings, timing
4. **Media** (3-5 items): alt text, captions, audio descriptions, color-only info

**Files:**
- `frontend/components/a11y/score-gauge.tsx` -- SVG ring gauge with
  `useMotionValue` + `useTransform` for counter, color interpolation via
  `[0,50,80,100] -> ["#ef4444","#f59e0b","#10b981","#14b8a6"]`,
  `motion.circle` with `pathLength`, 1.5s `circOut` easing
- `frontend/components/a11y/a11y-checklist.tsx` -- expandable checklist sections
- `frontend/components/a11y/checklist-item.tsx` -- individual checklist row

**Acceptance Criteria:**
- [ ] SVG ring gauge: 200px diameter, 12px stroke, animated fill via
      framer-motion `motion.circle` with `pathLength` animation
- [ ] Score counter uses `useMotionValue` + `useTransform` for smooth
      animated counting without React state re-renders
- [ ] Color interpolation via `useTransform` with breakpoints
      `[0, 50, 80, 100]` mapping to `["#ef4444", "#f59e0b", "#10b981", "#14b8a6"]`
- [ ] Animation uses 1.5s duration with `circOut` easing
- [ ] Animation respects `prefers-reduced-motion` via `useReducedMotion()`:
      duration set to 0 when reduced motion is enabled
- [ ] Color changes per score range (red -> amber -> emerald -> teal)
- [ ] Score number centered inside ring, large readable font
      (text-4xl using `var(--font-reading)`)
- [ ] "Fix with AI" button shown when score < 80, with Sparkles icon from
      lucide-react and pulse animation (`opacity: [1, 0.5, 1]`, repeat Infinity,
      duration 2s)
- [ ] Screen reader: `role="meter"`, `aria-valuenow={score}`,
      `aria-valuemin={0}`, `aria-valuemax={100}`,
      `aria-label="Accessibility score: {score} out of 100"`
- [ ] Checklist: 4 expandable sections (Structure, Cognitive, Predictability, Media)
- [ ] Each section header shows: category name, pass/total count, expand/collapse chevron
- [ ] Each item shows: status icon (green check / yellow warning / red X),
      criterion description, recommendation text (on warn/fail)
- [ ] Checklist items use `role="list"` + `role="listitem"`
- [ ] Works in all 9 persona themes (icons/colors adapt to theme variables)

---

### S5-008: Accessibility Preferences Panel [ ]

**Description:** Build a settings panel where users select their persona mode
and fine-tune accessibility preferences. Shows 9 persona cards with live
preview: switching a persona immediately applies the corresponding theme.
Includes sliders for font size and line height, and an animation toggle. All
preferences persist to localStorage.

**Files:**
- `frontend/components/settings/a11y-preferences.tsx` -- main preferences panel
- `frontend/components/settings/persona-card.tsx` -- individual persona selection card
- `frontend/app/settings/page.tsx` -- settings page (wraps preferences panel)

**Persona cards (9):**
| Persona | Icon | Short Description |
|---------|------|-------------------|
| Standard | Monitor | Default experience for all users |
| High Contrast | Eye | Maximum contrast (7:1+ ratio) for visibility |
| TEA (Autism) | Brain | Predictable, low stimulation, no animations |
| TDAH (ADHD) | Zap | Structured, chunked, warm focus tones |
| Dyslexia | BookOpen | OpenDyslexic font, extra spacing |
| Low Vision | ZoomIn | Large text, high contrast, big targets |
| Hearing | Ear | Visual emphasis, no audio dependencies |
| Motor | Hand | Extra large touch targets, generous spacing |
| Screen Reader | Speaker | Optimized for assistive technology |

**Acceptance Criteria:**
- [ ] 9 persona cards in a responsive grid (3x3 desktop, 2-col tablet, 1-col mobile)
- [ ] Each card: Lucide icon, persona name, 1-line description
- [ ] Active persona card has highlighted border/ring
- [ ] Live preview: clicking a persona card immediately applies the theme
      (no "Save" button needed; instant effect)
- [ ] Font size slider: range 14px-32px, step 2px, shows current value
- [ ] Line height slider: range 1.2-2.5, step 0.1, shows current value
- [ ] Animation toggle: on/off switch (off sets `--transition-duration: 0ms`)
- [ ] All preferences persisted to localStorage via Zustand theme store
- [ ] Preferences survive page reload and navigation
- [ ] Sliders use Radix UI Slider: keyboard accessible (Arrow keys adjust value)
- [ ] Switch uses Radix UI Switch: keyboard accessible (Space to toggle)
- [ ] Reset button: restores all preferences to defaults
- [ ] Settings page uses `t()` for all labels

---

## Dependencies

- **Sprint 0 (Foundation):** Backend API must be reachable for SSE pipeline viewer.
  Frontend can work with mock data initially but must connect to real SSE endpoint.
- **No hard backend dependency for most stories:** Stories S5-001 through S5-004,
  S5-007, and S5-008 are pure frontend and can be built independently.
- **S5-005 (Pipeline Viewer):** Requires the SSE endpoint from `api/streaming/sse.py`.
  Can be developed with a mock SSE server initially. Uses
  `@microsoft/fetch-event-source` for POST method support and auto-reconnect.
- **S5-006 (Plan Tabs):** Requires plan data schema alignment with backend
  `StudyPlanDraft`/`AccessibilityPackDraft` entities.

---

## Decisions

- **ADR-008 (confirmed):** Next.js 16 + Tailwind v4. Latest stable versions
  providing App Router, React 19.2 features, and CSS-first Tailwind config.
- **CSS variables over Tailwind theme:** CSS custom properties enable runtime
  theme switching without class regeneration. Tailwind v4's native CSS variable
  support makes this seamless.
- **9 persona modes over 3 generic themes:** Inclusive design is the core value
  proposition. Each disability type has specific UX needs that a generic
  "dark mode" / "high contrast" toggle cannot address.
- **Zustand over React Context:** Zustand provides built-in localStorage
  middleware, simpler API, and no provider nesting. Better for cross-component
  state like themes and pipeline status.
- **next-intl over react-i18next:** next-intl has first-class Next.js App Router
  support, server component compatibility, and simpler setup.
- **ADR: data-theme attribute over CSS class for theme switching
  (Gemini-3-Pro-Preview):** Use `[data-theme="..."]` attribute selectors instead
  of body class toggling (`.theme-*`). Rationale: (1) keeps theme namespace
  separate from Tailwind utility classes, avoiding accidental specificity
  collisions; (2) enables pure CSS cascade without React re-renders for styling
  changes; (3) cleaner attribute-based selector specificity compared to class
  chains. Implementation: `document.body.setAttribute('data-theme', 'dyslexia')`
  triggers all `[data-theme="dyslexia"] { ... }` rules instantly.
- **ADR: "Glass Box" AI pattern as primary demo differentiator
  (GPT-5.2 + Gemini-3-Pro-Preview consensus):** The Pipeline Viewer must expose
  internal AI reasoning steps (Planner outline, Quality Gate scoring,
  Refinement iterations) in the UI rather than showing a black-box spinner.
  This transparency builds user trust, demonstrates technical sophistication
  to hackathon judges, and is the single most impressive feature according to
  both external model consultations. Includes LLM model badges on each stage
  card to show the multi-model architecture at a glance.
- **ADR: WCAG AAA color palette (Gemini-3-Pro-Preview verified):** Light theme
  uses Slate 900 (#0F172A) for body text at 19:1 contrast ratio and Slate 600
  (#475569) for muted text at 7:1 contrast ratio on Slate 50 (#F8FAFC) canvas.
  Dark theme uses Slate 50 (#F8FAFC) for body text at 16:1 contrast ratio and
  Slate 300 (#CBD5E1) for muted text at 10:1 contrast ratio on Slate 950
  (#020617) canvas. All semantic colors (success, error, warning, info) use
  700-weight variants in light theme and 400-weight variants in dark theme
  to maintain AAA compliance.
- **ADR: @microsoft/fetch-event-source for SSE (Gemini-3-Pro-Preview):** Chosen
  over native EventSource because it supports POST method (needed to send
  initial payload), automatic reconnection, and AbortController-based cleanup.
- **ADR: next-intl v4 locale detection via cookie + localePrefix "as-needed"
  (Gemini-3-Pro-Preview):** Locale read from `NEXT_LOCALE` cookie in
  `getRequestConfig`. Middleware uses `localePrefix: "as-needed"` so the
  default locale (pt-BR) has no URL prefix while non-default locales
  (en, es) get prefixed paths.
- **ADR: Sidebar navigation pattern (Gemini-3-Pro-Preview):** Desktop uses
  64px-wide `aside` element with `border-r`, `sticky top-0`. Mobile uses
  shadcn Sheet component (Radix Dialog-based drawer) with Menu trigger instead
  of bottom tab bar. NAV_ITEMS array with icon components enables consistent
  rendering. All items use `aria-current="page"` for active state and
  `.touch-target` class for minimum 48px hit areas.
- **ADR: framer-motion score gauge using useMotionValue + useTransform
  (Gemini-3-Pro-Preview):** Avoids React state updates during animation by
  using motion values. Color interpolation breakpoints: [0, 50, 80, 100] ->
  ["#ef4444", "#f59e0b", "#10b981", "#14b8a6"]. SVG motion.circle uses
  pathLength for ring fill. 1.5s circOut easing. "Fix with AI" button uses
  Sparkles icon with pulse animation.

---

## Architecture Impact

```
frontend/
├── app/
│   ├── layout.tsx              # Root: fonts (Inter + Atkinson), providers, metadata, theme init
│   ├── page.tsx                # Dashboard
│   ├── [locale]/               # Locale-prefixed routes (next-intl, as-needed)
│   │   ├── plans/
│   │   │   ├── page.tsx        # Plans list
│   │   │   └── [id]/page.tsx   # Plan detail (tabs)
│   │   ├── materials/page.tsx
│   │   ├── tutors/page.tsx
│   │   └── settings/page.tsx   # Accessibility preferences
│   └── globals.css             # -> styles/globals.css
├── components/
│   ├── ui/                     # Customized shadcn/ui (CSS var references)
│   ├── layout/                 # Sidebar (64w sticky), TopBar, MobileNav (Sheet), SkipLink
│   ├── pipeline/               # PipelineViewer, StageCard (scanning animation, AnimatePresence)
│   ├── plans/                  # PlanTabs, TeacherPlan, StudentPlan, A11yReport, ExportsView
│   ├── a11y/                   # ScoreGauge (useMotionValue), A11yChecklist, ChecklistItem
│   └── settings/               # A11yPreferences, PersonaCard
├── hooks/
│   └── use-sse.ts              # @microsoft/fetch-event-source with POST + auto-reconnect
├── stores/
│   ├── theme-store.ts          # Persona, font size, line height, animations
│   └── pipeline-store.ts       # 6 steps, STAGE_MAP, handleEvent reducer, reset()
├── i18n/
│   └── request.ts              # getRequestConfig reading locale from cookie
├── proxy.ts                # createMiddleware (locales: en, pt-BR, es; localePrefix: as-needed)
├── lib/
│   ├── cn.ts                   # clsx + tailwind-merge
│   └── api.ts                  # API client (fetch wrapper)
├── styles/
│   └── globals.css             # @theme directive + 9 themes via [data-theme] + AAA palette
├── messages/
│   ├── en.json                 # ~200 keys
│   ├── pt-BR.json              # ~200 keys (default)
│   └── es.json                 # ~200 keys
└── public/
    └── fonts/
        └── AtkinsonHyperlegible-Regular.woff2
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| shadcn/ui AAA customization effort | Significant CSS overrides needed for 7:1 contrast | Use verified AAA palette (Slate 900/600 light, Slate 50/300 dark); override component styles systematically |
| 9 themes = extensive CSS work | Possible inconsistencies across themes | Use CSS variables consistently; test each theme with a visual checklist; exact hex values documented |
| Next.js 16 breaking changes | Build failures or runtime errors | Pin version, check migration guide, test early |
| Atkinson Hyperlegible font performance | Font file may slow initial load | Use `font-display: swap` via next/font/local, subset only Latin + Latin Extended |
| SSE reconnection reliability | Missed events during reconnection | @microsoft/fetch-event-source handles auto-reconnect; client-side state reconciliation on reconnect via REST |
| i18n key drift between locales | Missing translations in PT-BR or ES | Build-time script validates identical key sets across all locale files |
| next-intl v4 cookie-based locale | Cookie may not be set on first visit | Default to pt-BR in getRequestConfig when cookie is absent |

---

## Test Plan

- **Component tests:** Each component tested with React Testing Library
  - Theme store: persist/restore, persona switching, font size bounds
  - Pipeline store: handleEvent for all event types, stage name mapping, reset
  - Pipeline viewer: stage transitions, SSE mock, error states, scanning animation
  - Plan tabs: keyboard navigation, tab switching, content rendering
  - Score gauge: score ranges, color mapping (useTransform breakpoints), ARIA attributes
  - "Fix with AI" button: visibility based on score threshold, Sparkles icon
  - Preferences panel: slider interactions, toggle state
  - Sidebar: aria-current on active route, touch-target sizing
  - Mobile nav: Sheet open/close, navigation items
- **Accessibility tests:** axe-core integration tests for each persona theme
  - Verify contrast ratios (7:1+ for AAA compliance) using exact palette values
  - Verify focus management and keyboard navigation
  - Verify ARIA attributes on all interactive elements
  - Verify touch-target minimum sizes per theme
- **SSE integration test:** Mock @microsoft/fetch-event-source, verify
  handleEvent dispatch flow, connection status transitions, cleanup on unmount
- **Visual regression:** Screenshot comparison across 9 themes (manual for MVP)
- **i18n tests:** Verify all 3 locales render correctly, no missing keys,
  cookie-based locale detection works
- **E2E smoke test:** Load dashboard, switch persona, navigate to plans, verify
  layout adapts, verify SSE connection and stage transitions
