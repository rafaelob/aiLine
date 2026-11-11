# Caching models

Two models exist per project, selected by `cacheComponents` in `next.config`. Read the config first; never mix
examples from the two. Official pages (checked 2026-11-10): Caching https://nextjs.org/docs/app/getting-started/caching,
previous model https://nextjs.org/docs/app/guides/caching-without-cache-components, migration
https://nextjs.org/docs/app/guides/migrating-to-cache-components.

## Cache Components on

- Uncached data and request-time APIs run at request time; Next.js prerenders the static or cached UI around them.
- `use cache` plus `cacheLife` and `cacheTag` replace `fetch` cache options and route segment configs.
- Migration map for a config the build now rejects:

| Before | After |
|---|---|
| `dynamic = 'force-dynamic'` | delete it; request-time is already the default for uncached data |
| `dynamic = 'force-static'` | delete it; cache the data with `use cache` and a `cacheLife` profile; `cookies()` and `headers()` now return real values |
| `dynamic = 'error'` | delete it; wrap the fetches that relied on the cached default in `use cache` |
| `revalidate = N` (N above 0) | `use cache` around the data plus `cacheLife` (built-in profiles: seconds, minutes, hours, days, weeks, max) |
| `revalidate = 0` | delete it |
| `fetchCache` | delete it; cache with `use cache` or leave the data outside a cache scope |
| `fetch(url, { next: { revalidate, tags } })` | a `use cache` function with `cacheLife` and `cacheTag` |
| `dynamicParams` | delete it; unlisted params render on request; `notFound()` replaces `dynamicParams = false` |
| `runtime` | delete it, even `'nodejs'`; use Proxy for edge behaviour |

- Adopt incrementally: enable the flag, fix each rejected config, set `instant = false` on segments that are not ready,
  then convert one route at a time. `instant = false` does not clear synchronous IO in a prerender (`new Date()`,
  `Math.random()`, `crypto.randomUUID()`): move it to request time behind `<Suspense>` and `connection()`.
- `unstable_cache` and `fetch` caching keep working; migrating them is optional.
- `React.cache` still deduplicates within a render, but each cache function has its own scope.

## Cache Components off (previous model)

- `fetch` is not cached unless `cache: 'force-cache'` or `next.revalidate` says so; `fetch` is memoized within a
  render. Non-`fetch` work uses `unstable_cache` or React `cache`.
- The segment configs `dynamic`, `fetchCache` and `revalidate` are valid only in this model.
- Trap `[next@16, 2026-11-10]`: `revalidate` must be statically analyzable, so `600` works and `60 * 10` does not.
- Trap `[next@16, 2026-11-10]`: across a route's layouts and pages the lowest `revalidate` governs the whole route.
- Pages are always rendered on demand in development, so a revalidation bug shows only in `next build` plus `next start`.
- Invalidation: `revalidateTag(tag, 'max')` and `revalidatePath(path)` from a Server Action or Route Handler.
- The client router cache has its own lifetimes, set by `staleTimes`; read the option page for the current defaults
  and never quote a number from memory.
- React `cache` has no effect inside a Server Action or Route Handler, which are outside a render pass.
