---
name: pwa-engineering
description: "Use when changing a web manifest, service worker (Serwist, vite-plugin-pwa, hand-written), install prompt, offline caching, update prompt or Web Push. Not Next.js app code -> frontend-react-nextjs."
license: Apache-2.0
metadata:
  version: "2.0.0"
---

# PWA engineering

A PWA adds three things to a web app: an install surface, a service worker, and push. This skill decides what the
worker may cache, how it updates, what logout deletes, and what each platform allows. A screen's look is
`frontend-design`; Next.js app code (boundaries, caching, `next.config`) is `frontend-react-nextjs`.

Written against `serwist`, `@serwist/next` and `@serwist/turbopack` 9.5.13, `workbox-*` 7.4.1, `vite-plugin-pwa` 2.0.0
and `next` 16.x, checked 2026-11-11. Platform facts in `references/PLATFORM_MATRIX.md` are dated 2026-11-03.

## Procedure

Resolve API facts locally first: the installed version from the lockfile (package.json is only the constraint), the
installed types and source (`node_modules/serwist`, `@serwist/*`, `vite-plugin-pwa`, `workbox-*`) and the repo's own
worker and call sites. Open a Sources URL only when those leave a contract uncertain and network exists, and check the
installed major against the written-against line.

### 1. Detect before choosing

- Find which worker the project ships: a hand-written `sw.js`, Serwist (`@serwist/next` or `@serwist/turbopack`), or
  `vite-plugin-pwa` (read its `strategies` and `registerType`). The project's stack wins; switching is its own change.
- Classify each surface as public, personal or sensitive. The class decides what the worker may cache
  (`references/DATA_AND_PRIVACY.md`). Add a worker only for a stated offline or push need: installability needs none.

### 2. Manifest and install

- Manifest: an `id`, 192 and 512 PNG icons plus a maskable one (keep PNG even when an SVG exists), `display`
  `standalone`. Fields and syntax are in the Sources pages; Next generates it from `app/manifest.ts`.
- Never assume installed means standalone: since iOS 26 a Home Screen site may open in the browser. Detect with
  `matchMedia('(display-mode: standalone)')`.
- `beforeinstallprompt` is Chromium-only progressive enhancement: capture it, call `prompt()` only from the app's own
  click after the user showed interest, remember a dismissal, hide on `appinstalled`. iOS and Firefox get
  browser-provided install paths and written instructions, tested on those browsers (`references/PLATFORM_MATRIX.md`;
  timing: `references/APP_SHELL_UX.md`). Ask for notification permission as a separate step after install. Native
  wrappers (TWA, Capacitor) are out of scope.

### 3. Service worker: one stack per project

| Project | Default | Rules |
|---|---|---|
| Next 16 already on `@serwist/next` | Stay. Pin `next build --webpack` in every script that must emit the worker | Trap 1; worked example `references/SERWIST_NEXT.md` |
| New Next 16 project | `@serwist/turbopack` only while `cacheComponents` is off and `next build` passes; with it on, `@serwist/next` plus `--webpack` | Trap 6; Turbopack path UNVERIFIED by a build, see `references/SERWIST_NEXT.md` section 7 |
| Vite SPA | `vite-plugin-pwa` with `registerType: 'prompt'` (its default), `registerSW` from `virtual:pwa-register`, `updateSW()` after the user's click. Use `strategies: 'injectManifest'` whenever the app has sign-in, so the private-routes-first order below is code you own | Trap 5 |
| Hand-written worker | Stays. Migrate to a library only when a feature touches its cache, never as a side effect | next list |

A hand-written worker carries its own rules: a versioned cache name; an explicit precache list filled on `install`;
`activate` deletes every cache not on the current allowlist; `NetworkOnly` for authenticated requests; the
`SKIP_WAITING` message handler of the prompt policy (step 4). Verify with an offline browser test that the fallback
URL is precached, and with the two-user test of step 7.

Caching decisions, whatever the stack (code: `references/PWA_GUIDE.md`):

- The first registered route wins, so private exclusions (signed-in navigations, `/api/` except identified public
  paths) come first, then identified public resources, then a `NetworkOnly` catch-all.
- Strategy by resource: precache or `CacheFirst` for hashed static assets, `NetworkFirst` for public pages,
  `StaleWhileRevalidate` for public data that tolerates age, `NetworkOnly` for everything personal. Never
  `CacheFirst` or `StaleWhileRevalidate` for decision-bearing reads (balances, statuses, scores).
- Gate every runtime cache write with a fail-closed `cacheWillUpdate`: status 200, no `no-store` or `private`, no
  opaque or streamed response. Bound every cache by entries and age.
- Cache Storage keys are URLs, not users: a cached per-user response reaches the next person on the device.
- `fetchOptions` do not apply to navigations (trap 4): the server sends `Cache-Control: no-store` for signed-in pages.

### 4. Update policy: choose one, write it down

- Prompt: no `skipWaiting` at install; the page posts `SKIP_WAITING` after a click; only the tab that accepted and has
  no unsaved work reloads on `controllerchange`. Use it when a reload can lose state.
- Silent: `skipWaiting()` plus `clients.claim()`. Use it only when no unsaved state can exist.
- A prompt UI over a worker that skips waiting never fires: delete one side (traps 3 and 5).
- An SPA rarely navigates, so call `registration.update()` when the page becomes visible, at most hourly (design).
  Serve `/sw.js` with `Cache-Control: no-cache` and register with `updateViaCache: 'none'`.

### 5. Push

- Request permission from a user action, never on load. Subscribe with `userVisibleOnly: true` and show a
  notification for every push: silent push does not exist.
- The payload carries an id and generic text, never personal content. `notificationclick` opens only same-origin
  paths from an allowlist, whatever the payload says.
- iOS: only for a web app on the Home Screen. Declarative Web Push (iOS 18.4+) needs no worker code, so the server
  sends only allowlisted targets; keep the imperative `push` handler for older browsers.
- Unsubscribe in the browser and on the server at logout and account change.

### 6. Offline data

- IndexedDB holds offline data; browser storage is never the only copy, and `persist()` may be refused. Wrap every
  storage write in `try`/`catch`.
- An offline write queue persists each write before its first send with a stable operation ID; the server
  deduplicates per authenticated owner; every outcome is visible (contract: `references/PWA_GUIDE.md`).
- Background Sync is Chromium-only (trap 7): replay on page start, `online` and `visibilitychange` as the primary path.
- Staleness is a fact about the record, not connectivity: its age reaches the view as data, bound to the region it
  describes (`references/STALENESS_UI.md`).

### 7. Session lifecycle

Session expiry, logout and account change are three events. Only logout may end pending work, only after the user
decides; account change purges like logout, push included (invariants: `references/DATA_AND_PRIVACY.md` section 2).
Two-user test: A signs in, loads data, signs out; B must see none of A's responses (HTTP cache included), pages,
queued writes, drafts or push subscription.

## Dated traps

| Trap | Symptom, cause, fix |
|---|---|
| 1. `[@serwist/next@9.5.13, 2026-11-11]` build under Turbopack | `next build` fails: Next 16 builds with Turbopack by default and `withSerwist` adds a webpack config. Pin `--webpack`, or use the Turbopack guide's setup. |
| 2. `[@serwist/next@9.5.13, 2026-11-11]` page reloads when the network returns | `reloadOnOnline` defaults to `true` and calls `location.reload()` on every `online` event, losing drafts and uploads. Set `false` where they can exist. |
| 3. `[@serwist/next@9.5.13, 2026-11-03]` update prompt never shows | The starter config sets `skipWaiting` and `clientsClaim`, the silent policy. Drop both for the prompt policy. |
| 4. `[serwist@9.5.13 and workbox-strategies@7.4.1, 2026-11-03]` signed-in page cached | `fetchOptions` are dropped for navigations, so `NetworkOnly` cannot add `no-store`. The server sends the header. Source read, not run. |
| 5. `[vite-plugin-pwa@2.0.0, 2026-11-11]` prompt UI inert | `registerType: 'autoUpdate'` forces `skipWaiting` and `clientsClaim` on. Keep the default `'prompt'` when the page asks. |
| 6. `[@serwist/turbopack@9.5.13, 2026-11-11]` `cacheComponents` | The documented route handler exports `dynamic`, `dynamicParams` and `revalidate`; the Next migration guide says they fail the build once the flag is on. Not built here: UNVERIFIED. |
| 7. `[caniuse background-sync, 2026-11-11]` queue never replays | Firefox and Safari (iOS included) lack Background Sync. Replay on `online` and `visibilitychange`. |
| 8. `[@serwist/next@9.5.13, 2026-11-03]` `defaultCache` on a sign-in origin | Its production list caches same-origin `/api/` GETs and RSC payloads in shared caches, and later `NetworkOnly` routes never run. Write the routes of step 3. Source read, not run. |
| 9. `[lighthouse, 2026-11-11]` no PWA audit | Chrome's page says PWA testing in Lighthouse is deprecated. Use DevTools Application and a real device. |

## Validation: Done check

- DevTools Application shows a valid manifest and the expected worker; Network set to Offline loads the shell and the
  fallback page for an uncached route.
- Install verified on Chrome or Edge (`beforeinstallprompt`, `appinstalled`) and the browser-provided path on Firefox
  and Safari. Push round-trips on a real iPhone with the app on the Home Screen.
- The update policy is written down and the worker and page agree. No authenticated response sits in Cache Storage,
  every cache is bounded, and the product's tests pass every scenario in `references/DATA_AND_PRIVACY.md` section 2.

## Sources

| Topic | Official entry URL | Read when | Content checked |
|---|---|---|---|
| Installability criteria | https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable | deciding what makes the app installable | 2026-11-11 |
| Manifest members | https://web.dev/articles/add-manifest | writing `id`, icons, `display_override`, screenshots | 2026-11-11 |
| Promoting install | https://web.dev/articles/promote-install | timing a custom install control | 2026-11-11 |
| `beforeinstallprompt` | https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event | wiring the deferred prompt | 2026-11-11 |
| Service worker lifecycle | https://web.dev/articles/service-worker-lifecycle | update checks, `skipWaiting`, `registration.update()` | 2026-11-11 |
| Workbox routing | https://developer.chrome.com/docs/workbox/modules/workbox-routing | ordering routes in a worker | 2026-11-11 |
| Serwist on Next, webpack | https://serwist.pages.dev/docs/next/getting-started | wiring `@serwist/next` | 2026-11-11 |
| Serwist on Next, Turbopack | https://serwist.pages.dev/docs/next/turbo | a new Next 16 project without `cacheComponents` | 2026-11-11 |
| Serwist `reloadOnOnline` | https://serwist.pages.dev/docs/next/configuring/reload-on-online | the page reloads when the network returns | 2026-11-11 |
| vite-plugin-pwa, prompt update | https://vite-pwa-org.netlify.app/guide/prompt-for-update.html | `registerSW`, `onNeedRefresh`, `updateSW` | 2026-11-11 |
| vite-plugin-pwa, auto update | https://vite-pwa-org.netlify.app/guide/auto-update.html | `registerType: 'autoUpdate'` | 2026-11-11 |
| vite-plugin-pwa, injectManifest | https://vite-pwa-org.netlify.app/guide/inject-manifest.html | owning the worker source | 2026-11-11 |
| Next.js PWA guide | https://nextjs.org/docs/app/guides/progressive-web-apps | manifest file, `web-push`, `sw.js` headers, Serwist examples | 2026-11-11 |
| Cache Components migration | https://nextjs.org/docs/app/guides/migrating-to-cache-components | a segment config fails the build once the flag is on | 2026-11-11 |
| Push subscription | https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe | `userVisibleOnly` | 2026-11-11 |
| Web Push on iOS | https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/ | push or badging on iOS | 2026-11-11 |
| Declarative Web Push | https://webkit.org/blog/16535/meet-declarative-web-push/ | the iOS push payload shape | 2026-11-11 |
| Background Sync support | https://caniuse.com/background-sync | relying on `sync` events | 2026-11-11 |
| Storage quotas and eviction | https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria | sizing or persisting offline data | 2026-11-11 |
| Lighthouse PWA status | https://developer.chrome.com/docs/lighthouse/pwa/ | choosing an audit tool | 2026-11-11 |

## Works with

| Skill | Owns | Load when |
|---|---|---|
| `frontend-design` | the visual standard: variant, composition, text budgets | defining how the installed shell, offline and update states look |
| `accessibility` | accessible interaction: semantics, keyboard, focus, contrast, live regions | a state indicator, prompt or bottom navigation needs a semantic check |
| `frontend-delivery-checklist` | the done gate: real browser, states, real backend | a PWA change is about to be called done |
| `testing-e2e-playwright` | browser tests: fixtures, locators, waits | writing or fixing a Playwright test, including the offline and two-user tests |

## References

`PWA_GUIDE.md` (Workbox route, push and update-prompt code, sync contract), `SERWIST_NEXT.md` (Serwist on Next, the
Turbopack path), `DATA_AND_PRIVACY.md` (cache rules, session invariants, eviction), `PLATFORM_MATRIX.md` (per-platform
limits, dated), `APP_SHELL_UX.md` (prompt timing, safe areas, `display_override`), `STALENESS_UI.md` (cache age in the
view): all under `references/`, read when the step above points there.
