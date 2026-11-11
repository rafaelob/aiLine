---
name: frontend-react-nextjs
description: "Use when changing Next.js App Router code: Server/Client boundary, rendering and caching, request-time auth, next.config. Vite SPA -> frontend-react-vite-spa. Client server state -> frontend-data-fetching-caching."
license: Apache-2.0
metadata:
  version: "2.0.2"
---

# Next.js App Router engineering

Scope: Next.js projects that use the App Router and React Server Components. React + Vite single-page apps are out
of scope here -> `frontend-react-vite-spa`. A screen's look is `frontend-design`; this skill decides where code
runs, what is cached, and where authorization lives.

Written against `next` 16.x and `react` 19.x, checked 2026-11-10. The installed versions decide.

## Procedure

Resolve API facts locally: lockfile version (package.json is only the constraint), installed types and source
(`node_modules/next`, `node_modules/react`), repo call sites. Open a Sources URL only if a contract stays uncertain
and network exists; check the installed major against the written-against line. A rule below that names an API
applies only where the installed version exports it; the dated traps say which release changed what.

### 1. Detect before choosing

- Read the lockfile for `next` and `react`, and `next.config.*` for `cacheComponents`, `reactCompiler` and any
  `webpack` function. The project's configured caching model wins over this skill's preference; never mix examples
  from the two models. Switching a project to Cache Components is its own change, never a side effect of a feature.
- Bundler: read which one the installed `next` runs by default for `dev` and `build` and whether the scripts pass
  `--webpack` or `--turbopack`; a webpack config under a Turbopack default is the first trap.

### 2. Server and Client boundary

- Default to Server Components. Add `'use client'` to the file that holds state, effects, event handlers or browser
  APIs, and keep the boundary at the leaf, never above a subtree that only needs one interactive child.
- Mark modules that hold secrets or the data access layer with `import 'server-only'`, so a client import fails the
  build. Props from server to client must be serializable (official page below).
- Context providers are Client Components that take `children`; render them as deep as the tree allows.

### 3. Data and mutations

- Fetch in async Server Components, never in `useEffect`; wrap slow work in `<Suspense>` so the shell streams first.
- Never fetch route-specific data in a layout: layouts do not re-render on navigation, so the data goes stale.
- Server state that must live on the client (polling, optimistic lists, shared cache) -> `frontend-data-fetching-caching`.
- Mutate through Server Actions. Treat each one as a public endpoint: it performs its own authorization check.
- Metadata: a static `metadata` export unless the value depends on request information; a segment cannot export both
  `metadata` and `generateMetadata`; both run in Server Components only.

### 4. Rendering and caching

- Cache Components on (the installed `next` has the `cacheComponents` key and the project sets it): nothing is
  cached unless a `use cache` scope says so, with `cacheLife` and `cacheTag` for lifetime and invalidation. Runtime data (`cookies()`, `headers()`, `searchParams`, and `params` on routes without
  `generateStaticParams`) is read inside a `<Suspense>` boundary so the rest prerenders as a static shell.
  `connection()` marks deliberate request-time work.
- Cache Components off or absent: read `references/CACHING_MODELS.md` before touching a route; it holds the migration map.
- After a mutation: read-your-own-write invalidation (`updateTag`, Server Actions only, where exported) when the user
  must see their change at once; `revalidateTag` for stale-while-revalidate (its signature changed: trap);
  `revalidatePath` for a path.
- Under Cache Components, `use cache` stores in memory and per deployment by default; use `use cache: remote` or a
  cache handler when entries must outlive the instance.

### 5. Authorization and errors

- The request interceptor (`proxy`, or `middleware` on releases before the rename: trap) is for optimistic checks
  (read the cookie, redirect) plus CSP and locale. It is never the only defence:
  verify the session next to the data in a data access layer (`server-only`), in every Server Action and in every
  Route Handler. Do not put the check in a layout.
- Expected errors (validation, failed request) are return values read with `useActionState`; unexpected ones throw to
  the nearest `error` boundary, and `global-error` defines its own `html` and `body`. Error boundaries do not catch
  errors in event handlers: catch them and keep them in state.

### 6. Build and configuration

- `serverExternalPackages` for Node-only dependencies; `instrumentation` for server-start observability; the
  config reference owns `output`, headers and image settings.
- Enable the React Compiler only against a measured re-render cost: it adds a dev dependency and a build step.
- Offline, install and service workers -> `pwa-engineering` (a service-worker plugin often adds a webpack config,
  see the first trap).

## Dated traps

| Trap | Symptom, cause, fix |
|---|---|
| `[next@16, 2026-11-10]` webpack config | `next build` fails because Turbopack is the default and a webpack config exists, including one a plugin adds. Pass `--webpack` or migrate the config to Turbopack. |
| `[next@16, 2026-11-10]` segment configs under `cacheComponents` | `dynamic`, `dynamicParams`, `revalidate` and `fetchCache` exports fail the build, and `runtime` is unsupported even as `'nodejs'`. Delete `force-dynamic`, `fetchCache`, `dynamicParams`, `runtime`; replace `force-static` and `revalidate = N` with `use cache` plus `cacheLife`; call `notFound()` where `dynamicParams = false` rejected a param. |
| `[next@16, 2026-11-10]` empty `generateStaticParams` | Returning `[]` errors under Cache Components. Return at least one real param. |
| `[next@16, 2026-11-10]` removed flags | `experimental.ppr`, `experimental_ppr` and `experimental.dynamicIO` are replaced by `cacheComponents`. `typedRoutes` and `reactCompiler` are top-level keys, not `experimental.*`. |
| `[next@16, 2026-11-10]` synchronous request APIs | `cookies()`, `headers()`, `draftMode()`, `params` and `searchParams` are asynchronous; `await` them, including in `generateMetadata`. |
| `[next@16, 2026-11-10]` `middleware` | Renamed `proxy`, Node.js runtime only. |
| `[next@16, 2026-11-10]` `revalidateTag('x')` | A single argument is the old form; pass a cache profile (`'max'`). `updateTag` throws outside a Server Action; use `revalidateTag` in Route Handlers. |
| `[next@16, 2026-11-10]` state survives navigation | With Cache Components, routes are kept with `<Activity>` in hidden mode, so form values, open dropdowns and `useActionState` messages persist when the user returns. Add explicit reset logic. |
| `[next@16, 2026-11-10]` `generateMetadata` and runtime data | Reading `cookies()` or uncached data there while the page could otherwise prerender is a build error. Cache it with `use cache`, or add a Suspense-wrapped `connection()` marker. |

## Validation: Done check

- `next build` passes and the route summary shows the intended static or dynamic mode for every route you touched.
- Every Server Action and Route Handler you added or changed checks authorization itself.
- No `'use client'` sits above a subtree that needs only a leaf; no secret-bearing module lacks `server-only`.
- The changed screen was verified in a real browser (`frontend-delivery-checklist`).

## Sources

| Topic | Official entry URL | Read when | Content checked |
|---|---|---|---|
| Server and Client Components | https://nextjs.org/docs/app/getting-started/server-and-client-components | placing a `'use client'` boundary, passing props, providers | 2026-11-10 |
| Caching (Cache Components) | https://nextjs.org/docs/app/getting-started/caching | choosing `use cache`, `cacheLife`, `cacheTag` | 2026-11-10 |
| Caching, previous model | https://nextjs.org/docs/app/guides/caching-without-cache-components | `cacheComponents` is off | 2026-11-10 |
| Migrating to Cache Components | https://nextjs.org/docs/app/guides/migrating-to-cache-components | turning the flag on, any segment-config error | 2026-11-10 |
| Upgrading to version 16 | https://nextjs.org/docs/app/guides/upgrading/version-16 | Turbopack, async request APIs, `proxy`, removed flags | 2026-11-10 |
| Authentication | https://nextjs.org/docs/app/guides/authentication | sessions, Proxy, data access layer, Actions, Route Handlers | 2026-11-10 |
| Error handling | https://nextjs.org/docs/app/getting-started/error-handling | `error`, `global-error`, `notFound`, Action errors | 2026-11-10 |
| Metadata | https://nextjs.org/docs/app/api-reference/functions/generate-metadata | `metadata`, `generateMetadata`, streaming | 2026-11-10 |
| next.config options | https://nextjs.org/docs/app/api-reference/config/next-config-js | any `next.config` key (`output`, `typedRoutes`, `staleTimes`) | 2026-11-10 |
| serverExternalPackages | https://nextjs.org/docs/app/api-reference/config/next-config-js/serverExternalPackages | a Node-only dependency fails to bundle | 2026-11-10 |
| Instrumentation | https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation | server-start observability | 2026-11-10 |
| React hooks | https://react.dev/reference/react/hooks | `useActionState`, `useOptimistic`, `useTransition`, `useEffectEvent` | 2026-11-10 |
| React `use` | https://react.dev/reference/react/use | reading a promise or context in render | 2026-11-10 |

## Works with

| Skill | Owns | Load when |
|---|---|---|
| `frontend-design` | the visual standard: variant, composition, text budgets | defining or changing how a screen looks |
| `accessibility` | accessible interaction: semantics, keyboard, focus, contrast | a UI has a semantic, keyboard or focus barrier |
| `frontend-delivery-checklist` | the done gate: real browser, states, real backend | a UI change is about to be called done |
| `testing-e2e-playwright` | browser tests: fixtures, locators, waits | writing or fixing a Playwright test |
| `pwa-engineering` | install and offline: manifest, service worker, update | the surface is installable or works offline |
