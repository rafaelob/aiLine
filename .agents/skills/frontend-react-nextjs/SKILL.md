---
name: frontend-react-nextjs
description: "Use when building or changing Next.js App Router features: Server/Client boundary, SSR/SSG/ISR/PPR. LCP/INP tuning -> frontend-performance-web-vitals (catalog). Not framework-neutral fetch/cache or non-Next React setups."
license: Apache-2.0
metadata:
  version: "1.2.1"
---

# React 19+ and Next.js Engineering

React 19+ and Next.js 16+ App Router playbook: Server/Client boundary, React 19 features, data fetching, rendering and caching, hardening. Verify the current supported 16.x patch against the official Next.js releases before pinning.

## Execution playbook

### Step 1 -- Server Components and Client Components
- Default to Server Components; mark `'use client'` only for state, effects, event handlers, browser APIs or client-only libraries, and push the boundary as low in the tree as possible.
- Props passed from server to client are serializable only; never import server-only modules in client components. The `server-only` package turns an accidental import into a build error.

### Step 2 -- React 19+ features
Reach for `use()` (promises and context in render, callable conditionally), `useActionState` / `useFormStatus` / `useOptimistic` for form Actions, `useTransition` for non-form mutations, `ref` as a plain prop (no `forwardRef`), and nested `<Suspense>` for progressive streaming; details in `references/REACT_19_FEATURES.md`. Specifics worth keeping here:
- **`useEffectEvent`** and **`<Activity mode="hidden">`** are React 19.2: the first reads latest props/state from an Effect without a dependency; the second pre-renders hidden UI for instant navigation.
- **React Compiler** adds a dev dependency and a build-time pass, so enable it against a measured re-render cost, not by default: `reactCompiler: true` in `next.config` after installing `babel-plugin-react-compiler`; Next.js applies it only to relevant files via a custom SWC pass.
- **Metadata API**: `generateMetadata()` for dynamic SEO, `metadata` export for static; in dynamic routes `params` and `searchParams` are promises, so await them.

### Step 3 -- Data fetching strategy
- Server Components fetch with `async` functions (no `useEffect`); `fetch()` is deduped per request; wrap slow fetches in `<Suspense>`. TanStack Query or SWR for client state; mutate through `'use server'` functions called from forms or `useTransition`.
- **Revalidation**: `revalidatePath()` is unchanged. `revalidateTag()` now requires a cache profile as its 2nd argument (e.g. `revalidateTag('posts', 'max')`) for stale-while-revalidate. `updateTag()` (Server Actions only) expires a tag immediately so the next request sees fresh data -- reach for it after a mutation the user must see right away.
- Never fetch in `layout.tsx` if the data is route-specific (layouts do not re-render on navigation).

### Step 4 -- Rendering and caching
- **Static (SSG)**: default for pages with no dynamic data; `generateStaticParams()` for dynamic routes (with Cache Components on, it must return at least one param -- an empty array now errors at build).
- **Cache Components** (`cacheComponents: true` in `next.config`, Next.js 16+): static shell + dynamic holes, replacing the Next.js 15 `experimental.ppr` / `experimental.dynamicIO` flags. Once enabled, the route segment configs `dynamic`, `revalidate`, and `fetchCache` **error at build** instead of doing anything -- migrate each:
  - `dynamic = 'force-dynamic'` -> delete; every route is dynamic by default now.
  - `dynamic = 'force-static'` or `revalidate = N` -> wrap the data access in a `'use cache'` function and call `cacheLife('hours')` (or the closest built-in profile: seconds/minutes/hours/days/weeks/max).
  - `fetchCache` -> delete; caching is controlled entirely by `use cache`.
  - Without Cache Components enabled, the legacy `dynamic`/`revalidate`/`fetchCache` segment configs still work as before.
- **Runtime data** (`cookies()`, `headers()`, `searchParams`): read them inside a component wrapped in `<Suspense>` so the rest of the route still prerenders as a static shell.
- **Caching layers** (understand all four): request memoization (per-request dedup), data cache (persistent fetch cache), full route cache (pre-rendered HTML), router cache (client-side prefetch cache).

### Step 5 -- Production hardening
- Configure `next.config.ts` (not `.js`): `output: 'standalone'` for Docker, security headers, image domains.
- Use Proxy for CSP headers, locale detection and early checks or redirects only; enforce authentication and authorization next to the data (a data access layer), in Server Actions and in Route Handlers, because Proxy alone does not protect them (https://nextjs.org/docs/app/guides/authentication, read 2026-10-12).
- Enable `serverExternalPackages` for Node-only dependencies in server components.
- Set the top-level `typedRoutes: true` for type-safe routing (stable; `experimental.typedRoutes` is the old, superseded spelling).
- Configure `instrumentation.ts` for OpenTelemetry or custom server-side init.
- Handle errors gracefully: `error.tsx` per route, `global-error.tsx` for root, `notFound()` for 404s.
- **Next.js 16 removals**: sync access to `cookies()`, `headers()`, `draftMode()`, `params` and `searchParams` is gone, so always `await` them (including dynamic-route props in `generateMetadata`); `middleware` is deprecated and renamed `proxy`; Turbopack is the default for `next dev`.

## Gotchas
Layouts do not re-render on navigation, so keep route-specific data out of them (stale data otherwise). For framework-agnostic patterns see `frontend-design` and `frontend-performance-web-vitals` (catalog-only; confirm installed).

## Version Currency

Verified 2026-04-21, re-checked 2026-10-12 (npm registry: `next@16.4.0`, `react@19.3.0`); re-verify before citing a number. Next.js 16.x is the stable line and `cacheComponents: true` replaces `experimental.ppr` / `experimental.dynamicIO`; `cacheLife` / `cacheTag` are stable (no `unstable_` prefix); `PageProps<'/route/[slug]'>` comes from `npx next typegen`. The route-segment-config errors in Step 4 were verified 2026-09-25 against the official migration guide (`lastUpdated: 2026-09-07`); `typedRoutes` (doc `lastUpdated: 2025-08-19`) and `reactCompiler` are stable top-level `next.config` keys.

- React: https://react.dev
- Next.js: https://nextjs.org/docs
- Next.js 16 upgrade guide: https://nextjs.org/docs/app/guides/upgrading/version-16
- Migrating to Cache Components: https://nextjs.org/docs/app/guides/migrating-to-cache-components

## References
- Read `references/REACT_19_FEATURES.md` before Step 2 for the full detail on React 19 hooks, Actions, and Suspense patterns.
- Read `references/NEXTJS_APP_ROUTER.md` before Step 4, or for App Router file conventions and routing patterns beyond this skill's scope.
