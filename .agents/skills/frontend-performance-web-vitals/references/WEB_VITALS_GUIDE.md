# Core Web Vitals and Performance Guide

> Freshness: reflects CWV as of June 2026 (INP replaced FID in March 2024). Verify current thresholds at https://web.dev/vitals/ and Speculation Rules support at https://caniuse.com/speculation-rules. Top levers reference: https://web.dev/articles/top-cwv (instant navigations for LCP; "avoid unnecessary JavaScript" for INP).

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor | What it measures |
|--------|------|--------------------|------|-----------------|
| LCP | <= 2.5s | <= 4.0s | > 4.0s | Loading -- time until largest content element is visible |
| INP | <= 200ms | <= 500ms | > 500ms | Responsiveness -- worst interaction latency in the session |
| CLS | <= 0.1 | <= 0.25 | > 0.25 | Visual stability -- cumulative layout shift score |

Measured at the **75th percentile** of real user data (field metrics).

## INP Deep Dive

INP (Interaction to Next Paint) measures the delay between a user interaction (click, tap, keypress) and the next visual update. It replaced FID because FID only measured *first* input delay while INP captures *all* interactions.

### INP breakdown
```
Total interaction latency = Input delay + Processing time + Presentation delay
```
- **Input delay**: time from interaction to event handler start (blocked by long tasks).
- **Processing time**: event handler execution time.
- **Presentation delay**: time from handler completion to next paint (layout, paint, compositing).

### Optimization techniques
1. **Break long tasks**: no task should block the main thread for > 50ms.
   ```js
   // scheduler.yield() is preferred but Chromium-only (NOT Baseline 2026):
   // feature-detect and fall back to setTimeout(0) for Firefox/Safari.
   const yieldToMain = () =>
     globalThis.scheduler?.yield?.() ?? new Promise((r) => setTimeout(r));
   async function processItems(items) {
     for (const item of items) {
       processItem(item);
       await yieldToMain(); // let browser handle pending interactions
     }
   }
   ```
   Source: https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield
2. **Debounce rapid interactions**: throttle scroll, input, and resize handlers.
3. **Move computation off main thread**: use Web Workers for heavy processing.
4. **Virtualize long lists**: render only visible items (TanStack Virtual, react-window).
5. **Minimize DOM size**: large DOM trees slow down style recalculation and layout.
6. **Use `requestAnimationFrame`** for visual updates, not `setTimeout`.

### Diagnosing INP issues
- Chrome DevTools > Performance panel > record interactions > look for long tasks.
- Use `PerformanceObserver` with `'event'` type to log slow interactions:
  ```js
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.duration > 200) {
        console.warn('Slow interaction:', entry.name, entry.duration);
      }
    }
  }).observe({ type: 'event', buffered: true });
  ```

## LCP Quick Reference

### Common LCP elements
- Hero images, background images, video poster frames, large text blocks.

### Optimization checklist
1. **Discover early**: LCP resource must be in the initial HTML (not behind JS).
2. **Preload**: `<link rel="preload" as="image" href="hero.avif" fetchpriority="high">`.
3. **fetchpriority="high"**: on the LCP `<img>` element (and the preload link). Preload fixes *late discovery*; fetchpriority fixes *low priority* -- they are complementary, set both. Only ~17% of pages do this (easy win), but don't over-apply `high` or the signal cancels out. Support: Chrome/Edge 101+, Safari 17.2+, Firefox 132+. Source: https://web.dev/articles/fetch-priority
4. **Reduce TTFB**: CDN, edge caching, streaming SSR.
5. **No lazy-load on LCP**: never use `loading="lazy"` on the LCP image.
6. **Optimize format**: AVIF > WebP > JPEG. Use responsive `srcset`.
7. **Critical CSS**: inline above-the-fold CSS to avoid render-blocking.
8. **Font preload**: preload the primary display font if it affects LCP text.
9. **Instant navigations (highest-leverage win for repeat/sequential visits)**: bfcache eligibility + Speculation Rules prerender. Prerendered p75 LCP ~320ms vs ~1800ms standard (~82% faster); a bfcache restore also zeroes CLS. Source: https://web.dev/articles/top-cwv

## CLS Quick Reference

### Common CLS causes and fixes
| Cause | Fix |
|-------|-----|
| Images without dimensions | Add `width` and `height` attributes; use CSS `aspect-ratio` |
| Font swap causing reflow | Use `size-adjust` on fallback `@font-face`; `font-display: optional` |
| Ads/embeds without reserved space | Use `min-height` placeholder or `aspect-ratio` container |
| Dynamic content injection | Reserve space; use CSS `contain` on dynamic regions |
| Late-loading components | Use skeleton placeholders with matching dimensions |

## Speculation Rules API

Enables declarative prefetching and prerendering for instant navigations.

### Syntax
```html
<script type="speculationrules">
{
  "prerender": [
    {
      "where": { "href_matches": "/product/*" },
      "eagerness": "moderate"
    }
  ],
  "prefetch": [
    {
      "where": { "selector_matches": "a.nav-link" },
      "eagerness": "conservative"
    }
  ]
}
</script>
```

### Eagerness levels
- **`immediate`**: speculate as soon as the rule is observed.
- **`eager`**: speculate as soon as possible (browser-determined).
- **`moderate`**: speculate on hover (desktop) or pointerdown (mobile). Recommended default.
- **`conservative`**: speculate only on pointerdown/touchstart.

### Prefetch vs prerender
- **Prefetch**: fetches the document (and subresources with `requires: ["anonymous-client-ip-when-cross-origin"]`). Cheaper; good for many URLs.
- **Prerender**: fully renders the page in a hidden tab. Instant navigation but higher cost. Limit to high-confidence targets.

### Constraints
- Same-origin only for prerender (cross-origin prefetch is supported).
- Respects `Speculation-Rules` HTTP header for server-controlled rules.
- **Browser support (2026)**: Chromium-only by default (~79% of traffic; Chrome 121+ for document rules). Safari 26.2 supports it behind a flag; Firefox has not shipped it (positive position). It is an Interop 2026 focus area. Treat as pure progressive enhancement -- unsupported browsers silently ignore the rules. Verify at https://caniuse.com/speculation-rules and https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API.

## View Transitions API

### Same-document transitions (SPA)
```js
document.startViewTransition(() => {
  // Update DOM here
  updateContent();
});
```
```css
::view-transition-old(root) { animation: fade-out 200ms ease-out; }
::view-transition-new(root) { animation: fade-in 200ms ease-in; }
```

### Cross-document transitions (MPA)
```css
@view-transition { navigation: auto; }
```
Works with standard navigation and speculation rules for near-instant page transitions.

## Measurement Tools

| Tool | Type | Best for |
|------|------|----------|
| Chrome DevTools Performance | Lab | Detailed trace analysis, interaction debugging |
| Lighthouse | Lab | Audit scores, opportunities, CI integration |
| WebPageTest | Lab | Filmstrip, waterfall, cross-location testing |
| CrUX (Chrome UX Report) | Field | Real-user p75 metrics by origin/URL |
| web-vitals library | Field (RUM) | Custom real-user metric collection |
| PageSpeed Insights | Both | CrUX field data + Lighthouse lab audit |

## Official Documentation
- Core Web Vitals: https://web.dev/vitals/
- INP guide: https://web.dev/articles/inp
- Speculation Rules: https://developer.chrome.com/docs/web-platform/prerender-pages
- View Transitions: https://developer.chrome.com/docs/web-platform/view-transitions/
- web-vitals library: https://github.com/GoogleChrome/web-vitals
