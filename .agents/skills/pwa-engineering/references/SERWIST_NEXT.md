# Serwist on Next.js (App Router) — worked example

Load this when implementing or reviewing a service worker in a Next.js App Router
project that uses `@serwist/next`. For plain Workbox strategy code, see `PWA_GUIDE.md`
instead.

Versions verified **2026-11-03**: `@serwist/next`, `serwist` and `@serwist/turbopack`
all **9.5.13** (npm registry `latest`, published 2026-10-04). This guide is the webpack
path: the Serwist getting-started page says "This quick guide is meant for webpack" and
sends Turbopack users to a separate guide (https://serwist.pages.dev/docs/next/getting-started,
read 2026-11-03). Next 16 builds with Turbopack by default, so pin `next build --webpack`
in every script that must emit the worker. Serwist is a maintained Workbox-derived toolchain with first-class
Next.js/Vite/Nuxt integrations; the caching *strategies* are the same concepts as
Workbox, so strategy selection still comes from `PWA_GUIDE.md`.

## 1. Install

```bash
npm i @serwist/next && npm i -D serwist
```

`serwist` is a devDependency because the service worker source is compiled at build
time; only the built `public/sw.js` ships.

## 2. `next.config.mjs` — build-time precache manifest injection

```js
import { spawnSync } from "node:child_process";
import withSerwistInit from "@serwist/next";

// Optional: a revision versions a precached page so a stale precached response
// is not reused. Any stable per-build value works; a content hash is finer-grained.
const revision = spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).stdout ?? crypto.randomUUID();

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",                                        // SW source (Pages Router: e.g. "service-worker/index.ts")
  swDest: "public/sw.js",                                    // built output
  additionalPrecacheEntries: [{ url: "/~offline", revision }],
  // register: false,                                        // see section 5
  // disable: process.env.NODE_ENV === "development",         // see section 5
  // reloadOnOnline: false,                                   // default true; see section 5
});

export default withSerwist({
  // your Next.js config
});
```

The plugin computes the precache manifest from the build output and substitutes it
into the SW bundle at the injection point (default: the string `self.__SW_MANIFEST`).
That is why the SW source declares the global rather than importing a manifest file.

## 3. `app/sw.ts` — the service worker source

```ts
import type { PrecacheEntry, SerwistGlobalConfig, SerwistPlugin } from "serwist";
import { CacheFirst, ExpirationPlugin, NetworkFirst, NetworkOnly, Serwist, StaleWhileRevalidate } from "serwist";

// Declares the injection point to TypeScript.
declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}
declare const self: ServiceWorkerGlobalScope;

const PUBLIC_PAGES = new Set(["/", "/pricing"]);  // identical for every visitor
const noStore = new NetworkOnly({ fetchOptions: { cache: "no-store" } });
const bounded = (maxEntries: number) => new ExpirationPlugin({ maxEntries, maxAgeSeconds: 30 * 24 * 60 * 60 });

// Fail closed: opaque, private and streamed responses never enter a cache.
const publicOnly: SerwistPlugin = {
  cacheWillUpdate: async ({ response }) => {
    const cacheControl = response.headers.get("cache-control") ?? "";
    const contentType = response.headers.get("content-type") ?? "";
    const refused = /no-store|private/i.test(cacheControl) || contentType.includes("text/event-stream");
    return response.status === 200 && !refused ? response : null;
  },
};

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  runtimeCaching: [
    // 1. Private exclusions, before any caching route.
    {
      matcher: ({ request, sameOrigin, url }) => sameOrigin && (
        (request.mode === "navigate" && !PUBLIC_PAGES.has(url.pathname))
        || (url.pathname.startsWith("/api/") && !url.pathname.startsWith("/api/public/"))
      ),
      handler: noStore,
    },
    // 2. Identified public resources.
    {
      matcher: ({ sameOrigin, url }) => sameOrigin && url.pathname.startsWith("/_next/static/"),
      handler: new CacheFirst({ cacheName: "next-static", plugins: [publicOnly, bounded(64)] }),
    },
    {
      matcher: ({ request, sameOrigin }) => sameOrigin && request.mode === "navigate",
      handler: new NetworkFirst({ cacheName: "public-pages", networkTimeoutSeconds: 3, plugins: [publicOnly, bounded(16)] }),
    },
    {
      matcher: ({ sameOrigin, url }) => sameOrigin && url.pathname.startsWith("/api/public/"),
      handler: new StaleWhileRevalidate({ cacheName: "public-api", plugins: [publicOnly, bounded(32)] }),
    },
    // 3. Everything else, RSC payloads included, is not cached.
    { matcher: () => true, handler: noStore },
  ],
  fallbacks: {
    entries: [
      {
        url: "/~offline",
        matcher({ request }) {
          return request.destination === "document";
        },
      },
    ],
  },
});

serwist.addEventListeners();
```

Routes follow `references/DATA_AND_PRIVACY.md`, and order decides: the constructor registers
`runtimeCaching` in array order and `findMatchingRoute` returns the first match (`serwist`
9.5.13 `dist/index.mjs`, source read 2026-11-03, not executed). Do not ship `defaultCache` from
`@serwist/next/worker` on an origin with sign-in: its production list caches same-origin
`/api/` GETs in `apis` and RSC payloads and pages in shared caches
(`@serwist/next` 9.5.13 `dist/index.worker.mjs`, source read 2026-11-03), and NetworkOnly routes
appended after it never run. Outside production it is a single `NetworkOnly`, so a dev build
does not show this. `fetchOptions` do not apply to navigations, so signed-in pages also need
`Cache-Control: no-store` from the server. `navigationPreload` stays off here (its default):
a preloaded navigation skips the worker's fetch, so turn it on only with that header in place.

## 4. TypeScript and gitignore

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "types": ["@serwist/next/typings"],
    "lib": ["webworker"]
  },
  "exclude": ["public/sw.js"]
}
```

- `@serwist/next/typings` is what types `window.serwist`.
- `"webworker"` in `lib` adds the `WorkerGlobalScope`/`ServiceWorkerGlobalScope` types.
- Excluding `public/sw.js` keeps the built bundle out of typechecking.

`.gitignore`:

```
# Serwist
public/sw*
public/swe-worker*
```

## 5. Registration and the defaults that bite

- **`register` defaults to `true`.** The plugin injects `window.serwist.register()`
  into the app entrypoints, re-running on every entrypoint load. To control *when*
  registration happens (for example, to own the update prompt), set `register: false`
  and register from a client component:

  ```tsx
  "use client";
  import { useEffect } from "react";

  export default function RegisterPWA() {
    useEffect(() => {
      if ("serviceWorker" in navigator && window.serwist !== undefined) {
        window.serwist.register();
      }
    }, []);
    return <></>;
  }
  ```

- **`disable` defaults to `false`**, so development builds get a service worker too.
  Unless you specifically want to test offline behavior locally, gate it on
  `NODE_ENV` — otherwise a cached dev bundle will masquerade as a code bug.

- **`reloadOnOnline` defaults to `true`**: the injected code calls `location.reload()` on
  every window `online` event (https://serwist.pages.dev/docs/next/configuring/reload-on-online,
  read 2026-11-03). Set `false` where uploads, queued writes or drafts can exist.

## 6. Update policy: choose one

The example above sets `skipWaiting: true` and `clientsClaim: true`: the *silent* policy,
where a new worker takes over open pages at once. It does not combine with an "update
available" prompt, because the prompt never sees a waiting worker. Choose per product
(`SKILL.md` step 4) and record why. For the *prompt* policy, drop `skipWaiting` and
`clientsClaim` here and call `skipWaiting()` from a `SKIP_WAITING` message after the
user confirms.

## 7. The Turbopack path (UNVERIFIED by a build)

Read from https://serwist.pages.dev/docs/next/turbo on 2026-11-11; nothing below was built or run here.

- Packages: `@serwist/turbopack`, `esbuild` and `serwist`. `withSerwist` comes from `@serwist/turbopack` in
  `next.config.mjs`; there is no webpack config, so `next build` needs no `--webpack`.
- The worker is served by a route handler, `app/serwist/[path]/route.ts`, built with `createSerwistRoute`
  (`swSrc: "app/sw.ts"`, `additionalPrecacheEntries`), and registered by `SerwistProvider` from
  `@serwist/turbopack/react` with `swUrl="/serwist/sw.js"` in the root layout.
- That guide's route handler exports `dynamic`, `dynamicParams` and `revalidate`. The Next migration guide
  (https://nextjs.org/docs/app/guides/migrating-to-cache-components, read 2026-11-11) says those exports fail the
  build when `cacheComponents` is on. So the rule in `SKILL.md` is: Turbopack path only while the flag is off and
  `next build` passes; otherwise `@serwist/next` with `--webpack`.
- The private-routes-first runtime caching order of section 3 applies unchanged to `app/sw.ts`.

## Sources

- https://serwist.pages.dev/docs/next/turbo (Turbopack setup)
- https://serwist.pages.dev/docs/next/getting-started (install, `next.config`, `sw.ts`, tsconfig, gitignore)
- https://serwist.pages.dev/docs/next/configuring/register (`register`, default `true`)
- https://serwist.pages.dev/docs/next/configuring/disable (`disable`, default `false`)
- https://serwist.pages.dev/docs/next/configuring/reload-on-online (`reloadOnOnline`, default `true`)
- npm registry `@serwist/next`, `serwist`, `@serwist/turbopack` `latest` (9.5.13, 2026-10-04) — verified 2026-11-03
