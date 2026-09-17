---
name: frontend-performance-web-vitals
description: >-
  Tune Core Web Vitals (LCP, INP, CLS): lab/field, images, fonts, JS
  budgets, long tasks, caching. Use when Lighthouse/PageSpeed/CrUX is
  over budget, or "site lento", "a página trava ao clicar", "nota do
  Lighthouse caiu". Pair with diagnosing-bugs for non-browser slowness.
context: fork
agent: frontend
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.0.7
  category: content-production
  subcategory: technical-writing
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - frontend
  - performance
  - web
  - vitals
  - project_level
  audience: developer
  output_format: markdown
  modality: text
---

# Web Performance and Core Web Vitals

Production playbook for measurable performance improvements: Core Web Vitals optimization (LCP, INP, CLS), JavaScript budgets, image and font delivery, caching strategies, and modern navigation APIs.

## Scope
- Core Web Vitals scores are below targets (LCP > 2.5s, INP > 200ms, CLS > 0.1).
- A feature is increasing bundle size or introducing render-blocking resources.
- Setting up performance budgets and CI regression guards.
- Optimizing perceived performance with streaming, prefetching, or prerendering.
- Investigating real-user performance data from field metrics.

## Inputs to collect
- Current Core Web Vitals baseline (lab and field data if available).
- Target pages and user journeys to optimize.
- Framework and rendering model (SSR, SSG, SPA, streaming).
- CDN and hosting setup; caching configuration.
- Browser support policy (evergreen only vs legacy).

## Execution playbook

### Step 1 -- Measure baseline (no guesswork)
- Capture lab metrics: Lighthouse CI, Chrome DevTools Performance panel, WebPageTest.
- Capture field metrics: Chrome UX Report (CrUX), Real User Monitoring (RUM) via web-vitals library.
- Segment by device type (mobile vs desktop), connection speed, and geographic region.
- Identify the specific pages and elements driving poor scores (LCP element, INP handlers, CLS sources).
- Record baseline metrics as evidence; all changes measured against this baseline.

### Step 2 -- LCP optimization (target: under 2.5s)
- Identify the LCP element (usually hero image, heading, or video poster).
- **Resource discovery**: ensure LCP resource is discoverable in initial HTML (not lazy-loaded or behind JS).
- **Preload**: `<link rel="preload">` for LCP image/font; use `fetchpriority="high"` on the LCP `<img>`.
- **Server response**: reduce TTFB with CDN, edge caching, streaming SSR, or static generation.
- **Render-blocking resources**: inline critical CSS; defer non-critical CSS with `media` attribute or async loading.
- **Image optimization**: serve AVIF/WebP with fallback; use responsive `srcset` and `sizes`; set explicit `width`/`height`.
- **Font loading**: use `font-display: swap` or `optional`; preload critical fonts; use `next/font` or `size-adjust` fallbacks.
- **Third-party scripts**: defer or lazy-load non-essential scripts; load analytics after first paint.
- **Instant navigations (highest-leverage LCP win for repeat/sequential visits)**: making pages bfcache-eligible and prerendering likely next navigations via Speculation Rules makes LCP near-instant. Field data shows prerendered p75 LCP ~320ms vs ~1800ms standard (~82% improvement), and a bfcache restore also zeroes CLS. web.dev ranks instant navigations as another effective way to dramatically improve LCP. Mechanics in Step 8. Source: https://web.dev/articles/top-cwv

### Step 3 -- INP optimization (target: under 200ms)
- INP (Interaction to Next Paint) replaced FID as the responsiveness Core Web Vital in March 2024. It measures the longest interaction latency across the page lifecycle (discarding outliers). Thresholds: good < 200ms, needs improvement 200-500ms, poor > 500ms. INP remains the most commonly failed Core Web Vital.
- **Identify slow handlers**: use Chrome DevTools Performance panel to find long tasks triggered by user interactions. Use RUM tools for field data attribution.
- **Break long tasks**: split synchronous work so no task blocks the main thread > 50ms. `scheduler.yield()` is the preferred yielding primitive (it resumes ahead of other queued work), but it is **Chromium-only, not Baseline 2026** (no Firefox/Safari), so feature-detect and fall back: `await (globalThis.scheduler?.yield?.() ?? new Promise(r => setTimeout(r)))`. `requestIdleCallback` and `setTimeout(0)` are the cross-browser fallbacks. Source: https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield
- **Event handler efficiency**: debounce/throttle rapid-fire handlers; avoid layout thrashing (read-then-write patterns).
- **Reduce main thread work**: move heavy computation to Web Workers; use `requestAnimationFrame` for visual updates.
- **Virtualize long lists**: render only visible items with libraries like TanStack Virtual or react-window.
- **Minimize re-renders**: use React Compiler (automatic) or `React.memo`, `useMemo`, `useCallback` where profiling shows unnecessary re-renders.
- **Avoid forced synchronous layouts**: batch DOM reads before writes; use `transform` instead of `top`/`left` for animations.
- **Code splitting**: load only the JS needed for the current page; use dynamic imports for heavy libraries.

### Step 4 -- CLS optimization (target: under 0.1)
- **Explicit dimensions**: set `width` and `height` on images, videos, iframes, and ads.
- **Aspect ratio boxes**: use CSS `aspect-ratio` property for responsive media containers.
- **Font loading**: prevent layout shift from font swapping with `size-adjust`, `ascent-override`, `descent-override` on fallback fonts.
- **Dynamic content**: reserve space for late-loading content (ads, embeds, cookie banners).
- **Animations**: only animate `transform` and `opacity`; never animate geometric properties that cause layout.
- **Inject above-the-fold content carefully**: avoid inserting banners or notifications that push content down.

### Step 5 -- JavaScript optimization
- **Payload budget (top efficiency lever)**: shipping less JS is the dominant INP win, since INP is the most-failed CWV and unnecessary JavaScript is its #1 cause. Target long tasks < 50ms and cap critical-path JS per route (a practical budget is ~150-170KB compressed). Prefer platform features over libraries, remove unused code, and code-split before adding more. Source: https://web.dev/articles/top-cwv
- **Code splitting**: route-based splitting (automatic in Next.js); dynamic `import()` for heavy components.
- **Tree shaking**: ensure `sideEffects: false` in package.json; avoid barrel files that prevent tree shaking.
- **Bundle analysis**: use webpack-bundle-analyzer or `@next/bundle-analyzer` to find large dependencies.
- **Bundle budgets**: set size limits in CI (bundlesize, size-limit, or Lighthouse CI budget assertions).
- **Lazy loading**: defer non-critical components with `React.lazy` + `Suspense` or `next/dynamic`.
- **Module/nomodule**: serve modern ES modules to capable browsers; avoid transpiling for dead browsers.

### Step 6 -- CSS optimization
- **Critical CSS**: inline above-the-fold CSS; load remaining CSS asynchronously.
- **CSS containment**: use `contain: layout style paint` on independent widgets to limit rendering scope.
- **`content-visibility: auto`**: skip rendering of off-screen sections until they approach the viewport.
- **Reduce specificity wars**: prefer utility classes (Tailwind) or CSS Modules over deep selectors.
- **Scroll-driven animations**: use CSS `animation-timeline: scroll()` for GPU-accelerated scroll effects (no JS).

### Step 7 -- Image and media optimization
- **Modern formats**: AVIF (best compression) with WebP fallback; use `<picture>` with `<source>` elements.
- **Responsive images**: `srcset` with width descriptors + `sizes` attribute matching layout.
- **Lazy loading**: `loading="lazy"` on below-the-fold images; never lazy-load the LCP image.
- **`decoding="async"`**: prevent image decode from blocking the main thread.
- **`fetchpriority="high"` on the LCP image (under-used easy win)**: only ~17% of pages set it, yet it's broadly supported (Chrome/Edge 101+, Safari 17.2+, Firefox 132+). Pair it with `preload` -- they fix different problems: preload solves *late discovery*, fetchpriority solves *low priority*; set both on the `<img>` and on the preload link. Do **not** over-apply `high` (marking many resources high cancels the benefit and can hurt performance). Source: https://web.dev/articles/fetch-priority
- **Video**: use `poster` attribute; `preload="none"` or `preload="metadata"` for non-hero videos.

### Step 8 -- Caching and navigation
- **Cache-Control**: set appropriate `max-age`, `s-maxage`, `stale-while-revalidate` headers per resource type.
- **CDN caching**: cache static assets aggressively (immutable for hashed filenames); short TTL for HTML.
- **bfcache**: ensure pages are bfcache-eligible (no `unload` handlers, no `Cache-Control: no-store` on HTML).
- **Speculation Rules API**: use `<script type="speculationrules">` to declare prefetch and prerender rules for likely navigations. Treat as pure progressive enhancement: Chromium-only by default in 2026 (~79% of traffic); Safari 26.2 supports it behind a flag, Firefox has not shipped it; unsupported browsers silently ignore the tag. It is an Interop 2026 focus area. Source: https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API
  ```json
  { "prerender": [{ "where": { "href_matches": "/product/*" }, "eagerness": "moderate" }] }
  ```
- **View Transitions API**: use `document.startViewTransition()` for smooth same-document transitions; use `@view-transition` in CSS for cross-document transitions (MPA).

### Step 9 -- Performance monitoring and budgets
- **CI integration**: run Lighthouse CI on PRs; fail on regressions against budget.
- **Bundle budgets**: enforce JS/CSS size limits per route or entry point.
- **RUM monitoring**: deploy web-vitals library to track field performance; alert on p75 regressions.
- **Performance budget file**: maintain a `budget.json` or Lighthouse CI config with thresholds.
- **Before/after evidence**: capture traces, filmstrips, and metric deltas for every optimization.

## Common Pitfalls / Gotchas
- Optimizing lab scores without checking field (CrUX) data.
- Lazy-loading the LCP image (delays the most important metric).
- Adding preloads for everything (over-preloading hurts overall performance).
- Ignoring INP (interaction latency) and focusing only on load metrics.
- Using `will-change` or `transform: translateZ(0)` as blanket GPU "fixes" (wastes memory).
- Not measuring after each change to confirm actual improvement.

## References
- Read `references/WEB_VITALS_GUIDE.md` for deeper coverage of CWV metrics, INP optimization, and the Speculation Rules API than the steps above give.
- Use [the audit checklist](references/web-vitals-audit-checklist.md) when running a full Core Web Vitals audit end to end.

## Invocation
- Prefer implicit selection.
- To explicitly request: **Use the `frontend-performance-web-vitals` skill**.

## Official sources
- Core Web Vitals overview and current thresholds (LCP, INP, CLS): https://web.dev/articles/vitals
- INP metric reference (replaced FID, March 2024): https://web.dev/articles/inp
- Top CWV levers (instant navigations for LCP, "avoid unnecessary JavaScript" for INP): https://web.dev/articles/top-cwv
- `fetchpriority` -- adoption ~17% on LCP images; pair with preload; do not over-apply `high`: https://web.dev/articles/fetch-priority
- Speculation Rules API -- Chromium-only by default in 2026; Safari 26.2 flagged, Firefox not shipped; Interop 2026 focus; progressive enhancement: https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API
- View Transitions API (same-document + cross-document): https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
- `scheduler.yield()` -- preferred yielding primitive but Chromium-only, NOT Baseline 2026; feature-detect with setTimeout(0)/requestIdleCallback fallback: https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield
- Chrome UX Report (CrUX) field data: https://developer.chrome.com/docs/crux
