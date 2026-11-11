---
name: frontend-styling-architecture
description: "Use when changing Tailwind CSS, shadcn/ui, cva, tailwind-merge or next-themes setup: token bridge, dark mode, source detection. Not choosing tokens or type -> frontend-design. Not contrast -> accessibility."
license: Apache-2.0
metadata:
  version: "2.0.1"
---

# Frontend styling architecture

This skill wires design tokens into Tailwind CSS and shadcn/ui and keeps the setup consistent. It does not choose
values: typeface, hue, radius and palette belong to `frontend-design` (`references/FAMILIES.md`). The three style
variants `calm`, `cockpit` and `visual` are token files there; the cva axes below are called component variants.

Written against `tailwindcss` 4.x with `tailwind-merge` 3.x and the shadcn/ui Tailwind 4 setup, checked 2026-11-10.
A project still on Tailwind 3.4 follows its own section.

## Procedure

Resolve API facts locally: lockfile version (package.json is only the constraint), installed types and source
(`node_modules/tailwindcss`, `tailwind-merge`), repo call sites. Open a Sources URL only if a contract stays uncertain
and network exists; check the installed major against the written-against line.

### 1. Detect the setup

- Tailwind major from the lockfile; `components.json` for shadcn; an existing family file or `DESIGN.md` for tokens.
  Tailwind 3.x (`tailwind.config.*`, `@tailwind` directives): keep it, see the 3.4 section. Moving to 4 is its own
  change (`npx @tailwindcss/upgrade`).
- A new project copies one family file from `frontend-design` `assets/families/<variant>.css`; an existing one keeps
  its tokens. Never type a hue, typeface or radius into this layer.

### 2. Token flow: family roles, shadcn tokens, utilities

Three layers, each referencing the one before. The family file declares plain `:root` roles (`--color-canvas`,
`--color-ink`, `--color-accent`, `--color-series-*`, `--font-*`, `--text-*`, `--radius-*`) and stays the source of
truth. shadcn tokens point at roles under different names; `@theme inline` exposes them as utilities.

```css
@import "tailwindcss";
@import "./families/calm.css";   /* frontend-design family file, unlayered :root */
@custom-variant dark (&:where(.dark, .dark *));

:root {                           /* outside @layer base */
  --background: var(--color-canvas);   --foreground: var(--color-ink);
  --card: var(--color-surface);        --card-foreground: var(--color-ink);
  --popover: var(--color-surface-raised);  --popover-foreground: var(--color-ink);
  --primary: var(--color-accent);      --primary-foreground: var(--color-on-accent);
  --secondary: var(--color-track);     --secondary-foreground: var(--color-ink);
  --muted: var(--color-track);         --muted-foreground: var(--color-ink-muted);
  --accent: var(--color-accent-wash);  --accent-foreground: var(--color-ink);
  --destructive: var(--color-bad);
  --border: var(--color-rule);  --input: var(--color-input-border);  --ring: var(--color-focus);
  --chart-1: var(--color-series-1);  --chart-2: var(--color-series-2);  --chart-3: var(--color-series-3);
  --chart-4: var(--color-series-4);  --chart-5: var(--color-series-other);
  --radius: var(--radius-md);
}
@theme inline {                   /* one line per token above: --color-X: var(--X) */
  --color-background: var(--background);  --color-foreground: var(--foreground);
  --color-primary: var(--primary);        --color-primary-foreground: var(--primary-foreground);
  --color-border: var(--border);          --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);        --radius-lg: var(--radius);  /* ...and the rest */
}
```

- Map under a different name than the family role. Never redeclare a family name (`--color-canvas`) inside
  `@theme inline`: it is self-referential and the unlayered family `:root` wins by accident.
- `--font-*`, `--text-*` and `--radius-*` in the unlayered family `:root` outrank Tailwind's layered theme defaults,
  so `font-sans`, `text-sm` and `rounded-md` already follow the family (compiled with tailwindcss 4.3.5, 2026-11-10).
  Do not copy them again.
- Family roles reach utilities with the arbitrary-value shorthand: `bg-(--color-rule)`. A role used repeatedly gets a
  semantic token and a `@theme inline` line instead.
- Chart colours stay the family's `--color-series-*`; chart rules are `frontend-design` `references/CHARTS.md` and
  `assets/recharts/chart-tokens.ts`. `--chart-1..5` exist only because shadcn's chart component asks for them.
- Never wrap a token in `hsl()` or `rgb()`: family and shadcn tokens are complete colours (see traps).
- Dual theme: redeclare the family roles under `.dark`. With next-themes the class sits on `<html>`, the same element as
  `:root`, so the bridge needs no second copy. A nested `.dark` wrapper is UNVERIFIED (not rendered). `cockpit` is
  dark-native and needs no `.dark` block.

### 3. Tailwind 4 decisions

- Source detection is automatic. Add `@source` for classes outside the scanned tree, `@source not` to exclude,
  `@source inline()` for class names assembled from strings (a CMS field, a computed key).
- Class-based dark mode is the `@custom-variant dark` line above, and next-themes must use `attribute="class"`; the
  attribute and the variant selector have to agree. Without the variant, `dark:` follows `prefers-color-scheme`.
- Custom animation: `--animate-*` plus its `@keyframes` inside `@theme`. Container queries are built in.
- Legacy JS config and plugins load only through `@config` and `@plugin`; prefer CSS-first `@theme`.

### 4. Components

- One `cn()` = `clsx` + `tailwind-merge`. The `tailwind-merge` major follows the Tailwind major (3.x for Tailwind 4.0
  to 4.3, 2.6.0 for Tailwind 3). Colour classes come from semantic tokens (`bg-primary`), never palette classes
  (`bg-red-100`).
- shadcn/ui copies component source into the project and the project owns it: edit in place, compose domain wrappers
  next to it, and add components through the CLI. On React 19 the components take `ref` as a prop and carry
  `data-slot`; no `forwardRef`.
- Component variants (cva): use cva when a component has three or more visual variants. Say "component variants (cva)"
  in code, PRs and docs so it never reads as the style variants `calm`, `cockpit` and `visual`.
- CSS Modules only for scoped keyframes, third-party overrides or a gradual migration. Do not mix runtime CSS-in-JS
  and Tailwind in one component; a project already on runtime CSS-in-JS keeps it.
- Anti-patterns: 15+ utilities on one element (extract a component), hardcoded hex or rgb outside the token layer,
  `!important` (fix specificity with layers), `@apply` in global CSS for one-offs, a JS `tailwind.config` in a v4 build.

### 5. Dark mode checks

- Both themes render the same hierarchy; contrast and forced-colors audits -> `accessibility`.
- Browser-painted UI follows the theme: open a `<select>`, a date input and a scrollable area in dark mode.
- No flash of the wrong theme on first paint: the preference is applied before paint (next-themes' script), not in
  a `useEffect`. Theme-dependent images and inline SVG switch too.
- Emulate `prefers-color-scheme`, then confirm at OS level: emulation does not exercise `color-scheme` UI the same way.

### Project still on Tailwind 3.4

Detect `tailwindcss` 3.x, a `tailwind.config.*`, and `@tailwind base/components/utilities`. Keep the JS theme, the
`content` array, the plugins array, keyframes in config and the project's existing `darkMode` setting (`'selector'`
replaced `'class'` in 3.4.1). Use `tailwind-merge` 2.6.0 and shadcn components for the Tailwind line the project is on.
Map family roles through the existing config's colour entries. Never add `@theme`, `@custom-variant` or
`@import "tailwindcss"` to a 3.x build; migration to 4 is a separate change.

## Dated traps

| Trap | Symptom, cause, fix |
|---|---|
| `[shadcn@tailwind-v4, 2026-11-10]` HSL and `@layer base` | `hsl(var(--brand-500))` is an invalid colour because tokens are complete OKLCH values. Use `var(--token)` directly; declare `:root` and `.dark` outside `@layer base`. |
| `[shadcn@tailwind-v4, 2026-11-10]` copied old snippets | `text-destructive-foreground` and `forwardRef` come from the old setup: `--destructive` has no foreground pair now, and components take `ref` as a prop. |
| `[tailwindcss@4, 2026-11-10]` `darkMode` and `content` keys | The JS config is not read unless loaded with `@config`. Dark mode is `@custom-variant`; scanning is automatic plus `@source`. |
| `[tailwindcss@4, 2026-11-10]` keyframes in JS config | The animation never defined. Put `@keyframes` inside `@theme` beside `--animate-*`. |
| `[tailwindcss@4, 2026-11-10]` `@apply` in a CSS Module | Utilities and theme values are unknown there. `@reference` the main stylesheet at the top of the module. |
| `[tailwindcss@4, 2026-11-10]` classes missing from `node_modules` or CMS text | Detection skips `node_modules` and cannot read strings built at runtime. Add `@source` or `@source inline()`. |
| `[light-dark(), 2026-11-10]` ignores the user's preference | It needs `color-scheme: light dark` on `:root`; with a class toggle also set `.dark { color-scheme: dark }`. next-themes sets `color-scheme` by default. |
| `[@font-face, 2026-11-10]` silent fallback | A family named in `@font-face` or `--font-*` that is not loaded falls back to a system font with no error. Confirm the exact family name in the loaded file. |

## Validation: Done check

- No hue, typeface or radius was introduced here; values trace to a family file or the project's tokens.
- Light and dark were rendered at 1440, 390 and 320 wide; browser-painted controls follow the theme.
- A utility from every new semantic token compiles (build output contains the class), and `dark:` follows the toggle.
- No `hsl()` around a token, no palette class for a semantic role, no second `cn()`.

## Sources

| Topic | Official entry URL | Read when | Content checked |
|---|---|---|---|
| Tailwind upgrade guide | https://tailwindcss.com/docs/upgrade-guide | moving 3 to 4, Node version, the upgrade tool | 2026-11-10 |
| Theme variables | https://tailwindcss.com/docs/theme | `@theme`, `inline`, `static`, namespaces | 2026-11-10 |
| Source detection | https://tailwindcss.com/docs/detecting-classes-in-source-files | a class is missing from the build | 2026-11-10 |
| Dark mode (Tailwind 4) | https://tailwindcss.com/docs/dark-mode | class or selector toggling | 2026-11-10 |
| Dark mode (Tailwind 3.4) | https://v3.tailwindcss.com/docs/dark-mode | the project is on Tailwind 3 | 2026-11-10 |
| Directives and compatibility | https://tailwindcss.com/docs/functions-and-directives | `@reference`, `@plugin`, `@config`, `@source` | 2026-11-10 |
| Animation | https://tailwindcss.com/docs/animation | custom `--animate-*` and keyframes | 2026-11-10 |
| Container queries, breakpoints | https://tailwindcss.com/docs/responsive-design | `@container`, custom breakpoints | 2026-11-10 |
| shadcn/ui on Tailwind 4 | https://ui.shadcn.com/docs/tailwind-v4 | token form, `data-slot`, new components | 2026-11-10 |
| shadcn/ui theming | https://ui.shadcn.com/docs/theming | `:root`, `.dark`, `@theme inline` | 2026-11-10 |
| shadcn/ui CLI | https://ui.shadcn.com/docs/cli | adding or updating a component | 2026-11-10 |
| cva | https://cva.style/docs | component variants, compound variants | 2026-11-10 |
| tailwind-merge | https://github.com/dcastil/tailwind-merge | the Tailwind major and its supported line | 2026-11-10 |
| next-themes | https://github.com/pacocoursey/next-themes | provider setup, `attribute`, hydration warning | 2026-11-10 |
| `light-dark()` | https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/light-dark | one value per scheme in plain CSS | 2026-11-10 |

## Works with

| Skill | Owns | Load when |
|---|---|---|
| `frontend-design` | the visual standard: families, tokens, chart rules, compositions | choosing or changing a value, a variant or a chart |
| `accessibility` | accessible interaction: semantics, keyboard, focus, contrast, forced colors | a UI has a semantic, keyboard, focus or contrast barrier |
| `frontend-delivery-checklist` | the done gate: real browser, states, real backend | a UI change is about to be called done |
| `testing-e2e-playwright` | browser tests: fixtures, locators, waits | writing or fixing a Playwright test |
| `pwa-engineering` | install and offline: manifest, service worker, update | the surface is installable or works offline |
