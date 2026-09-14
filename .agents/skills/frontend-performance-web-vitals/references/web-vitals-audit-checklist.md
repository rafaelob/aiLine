# Web Vitals Audit Checklist

## Measure first (no guesswork)
- Capture baseline:
  - Lighthouse (local + CI)
  - Real User Monitoring (if available)
  - Synthetic tests (WebPageTest) for representative pages
- Segment by device/network (mobile/slow 4G matters).

## Common levers
### LCP
- Optimize critical image and fonts (preload critical, avoid blocking).
- Reduce server TTFB (cache, CDN, server performance).
- Avoid render-blocking CSS/JS.

### INP / interaction latency
- Reduce long tasks (split bundles, defer non-critical work).
- Avoid heavy synchronous work in input handlers.
- Use memoization and virtualization for large lists.

### CLS
- Reserve space for media/ads.
- Avoid late-loading fonts without fallback strategy.
- Stabilize layout with predictable component sizing.

## Budgets
- Set bundle and performance budgets (JS, CSS, image total).
- Enforce budgets in CI (fail builds on regressions).

## Evidence to capture
- Before/after traces (DevTools Performance)
- Bundle diffs
- RUM deltas by route/device
