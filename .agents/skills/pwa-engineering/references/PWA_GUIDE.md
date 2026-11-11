# Progressive Web App Reference Guide

> Freshness: code patterns, re-read 2026-11-03. Browser support and dated platform facts live in `PLATFORM_MATRIX.md`; verify at https://caniuse.com and the Workbox API at https://developer.chrome.com/docs/workbox/. The manifest fields and the official links are in the `## Sources` table of `SKILL.md`.

## Service Worker Lifecycle

```
Registration -> Installing -> Waiting -> Activating -> Activated (controlling)
```

1. Browser checks for SW updates on an in-scope navigation, on functional events such as `push` and `sync` unless it checked within the previous 24 hours, and on `registration.update()` ([web.dev service-worker-lifecycle](https://web.dev/articles/service-worker-lifecycle), undated, read 2026-11-03).
2. New SW installs alongside the old one, enters `waiting` until all tabs using old SW close.
3. `skipWaiting()` forces immediate activation. The new worker then "is likely controlling pages that were loaded with an older version" ([web.dev service-worker-lifecycle](https://web.dev/articles/service-worker-lifecycle), undated, read 2026-11-03). Choose prompt or silent updates per product (`SKILL.md` step 4).

## Workbox Caching Strategies

"The Route that is registered first will be used to respond to the request" ([workbox-routing, undated, read 2026-11-03](https://developer.chrome.com/docs/workbox/modules/workbox-routing)), so private exclusions come first and only identified public resources are cached.

```js
// sw-routes.js: bundled with injectManifest, which fills in self.__WB_MANIFEST.
import { matchPrecache, precacheAndRoute } from 'workbox-precaching';
import { registerRoute, setCatchHandler } from 'workbox-routing';
import { CacheFirst, NetworkFirst, NetworkOnly, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

precacheAndRoute(self.__WB_MANIFEST);  // include /offline

const PUBLIC_PAGES = new Set(['/', '/pricing']);  // identical for every visitor
const noStore = new NetworkOnly({ fetchOptions: { cache: 'no-store' } });
const sameOrigin = (url) => url.origin === self.location.origin;
const bounded = (maxEntries) => new ExpirationPlugin({ maxEntries, maxAgeSeconds: 30 * 24 * 60 * 60 });

// Fail closed: opaque, private and streamed responses never enter a cache.
const publicOnly = {
  cacheWillUpdate: async ({ response }) => {
    const cacheControl = response.headers.get('cache-control') ?? '';
    const contentType = response.headers.get('content-type') ?? '';
    const refused = /no-store|private/i.test(cacheControl) || contentType.includes('text/event-stream');
    return response.status === 200 && !refused ? response : null;
  },
};

// 1. Private exclusions, before any caching route.
registerRoute(
  ({ request, url }) => sameOrigin(url) && (
    (request.mode === 'navigate' && !PUBLIC_PAGES.has(url.pathname))
    || (url.pathname.startsWith('/api/') && !url.pathname.startsWith('/api/public/'))
  ),
  noStore,
);

// 2. Identified public resources.
registerRoute(
  ({ url }) => sameOrigin(url) && url.pathname.startsWith('/static/'),
  new CacheFirst({ cacheName: 'static-assets', plugins: [publicOnly, bounded(100)] }),
);
registerRoute(
  ({ request, url }) => sameOrigin(url) && request.mode === 'navigate',
  new NetworkFirst({ cacheName: 'public-pages', networkTimeoutSeconds: 3, plugins: [publicOnly, bounded(16)] }),
);
registerRoute(
  ({ url }) => sameOrigin(url) && url.pathname.startsWith('/api/public/'),
  new StaleWhileRevalidate({ cacheName: 'public-api', plugins: [publicOnly, bounded(32)] }),
);

// 3. Everything else is not cached.
registerRoute(() => true, noStore);

setCatchHandler(async ({ request }) =>
  (request.mode === 'navigate' ? await matchPrecache('/offline') : undefined) ?? Response.error());
```

### Strategy selection guide

| Resource type | Strategy | Rationale |
|---------------|----------|-----------|
| App shell (HTML, critical CSS/JS) | Precache | Always available offline; identical for every user |
| Static assets (images, fonts) | Cache-First | Rarely change; fast from cache |
| Public HTML pages | Network-First | Fresh content; cache for offline |
| Signed-in HTML pages | Network-Only + precached fallback | Server sends `no-store`; never cache user-specific pages |
| API (public, non-auth) | Stale-While-Revalidate | Fast response; background refresh |
| API (authenticated) | Network-Only, `cache: 'no-store'` | Never cache user-specific data, in Cache Storage or the HTTP cache |
| CDN resources (versioned) | Cache-First + immutable | Hash in filename guarantees freshness |

## Push Notifications

One payload serves both paths. Declarative Web Push puts `title` and `navigate` inside `notification`, and an older browser handles the same message imperatively ([WebKit blog, 2025-03-27](https://webkit.org/blog/16535/meet-declarative-web-push/)). On the declarative path the browser opens `navigate` with no worker code, so the server must only ever send allowlisted targets.

```js
// Server: send push (VAPID). Generic text and an id, never personal content.
await webPush.sendNotification(subscription, JSON.stringify({
  web_push: 8030,
  notification: {
    title: 'New message',
    body: 'Open the app to read it.',
    navigate: 'https://app.example/messages/123',
  },
}));
```

```js
// sw-push.js: the imperative path.
const OPEN_PATHS = [/^\/messages\/[\w-]+$/];  // every path a notification may open

// A payload URL is untrusted input.
export function allowedPath(navigate) {
  try {
    const target = new URL(navigate, self.location.origin);
    const allowed = target.origin === self.location.origin
      && OPEN_PATHS.some((path) => path.test(target.pathname));
    return allowed ? target.pathname : '/';
  } catch {
    return '/';
  }
}

self.addEventListener('push', (event) => {
  const { title = 'New activity', body, navigate } = event.data?.json().notification ?? {};
  event.waitUntil(self.registration.showNotification(title, { body, data: { navigate } }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(self.clients.openWindow(allowedPath(event.notification.data?.navigate)));
});
```

**iOS/Safari limitations:** Web Push only when the PWA is on the Home Screen; no silent push; permission requires a user gesture. The Badging API is supported for Home Screen web apps ([WebKit blog, 2023-02-16](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)).

## Background Sync Pattern

This section states a contract, not an implementation: a full queue is concurrency-sensitive and depends on the product's session layer. Invariants 1, 5 and 6 are in `DATA_AND_PRIVACY.md` section 2, with the acceptance scenarios a product must test. All of it is design.

### Delivery contract

- **Enqueue:** admission runs inside the lifecycle lock (invariant 1): revalidate the originating generation, then commit the entry with its owner and operation ID before any send. A refused or failed enqueue stores nothing, keeps the form open and says so.
- **After commit:** the caller holds the ID (invariant 6). Replay and Background Sync registration run afterwards and separately: their failure is never reported as enqueue failure and never leads to resubmitting under a new ID. A failed `sync.register()` changes nothing, because it is only an enhancement.
- **Entries** leave only on acknowledgement or explicit discard, and replay sends only the current owner's (invariant 5). Failing to record an outcome leaves the entry in place and is reported as a replay failure.
- **One runner:** only one context replays at a time across pages and the worker, and no session transition or discard commits while a send is in flight. Holding the lifecycle lock around each bounded send and releasing it between sends meets this; a save then waits at most one send timeout (not demonstrated). Each send re-reads session and generation inside that hold and stops unless the session is active.
- **Each send** uses the same ID every time, since a lost response is an unknown outcome, plus `cache: 'no-store'`, `credentials: 'same-origin'`, a timeout, and `redirect: 'error'`, so a redirect to a login page cannot read as a 200.
- **Triggers:** page start, `online` and `visibilitychange` are the primary path. Background Sync is Chromium only: feature-detect it, and in the worker let the `sync` event's promise reject to ask for a retry.

### Response classification

`fetch` resolves on 4xx and 5xx, so every response is classified:

| Outcome | Status | Entry | The UI shows |
|---|---|---|---|
| `acknowledged` | 2xx | Removed | Saved |
| `auth-blocked` | 401, 403 | Kept; replay stops; a 401 of the current generation marks the session expired | "Sign in to send N changes" |
| `retrying` | 408, 425, 429, 5xx, network error, timeout | Kept; replay stops, keeping order; retried on `sync`, `online`, `visibilitychange` | "Not sent yet" and the last error |
| `rejected` | Any other status | Kept; not resent | The reason, with edit or discard |

```js
function classify(status) {
  if (status >= 200 && status < 300) return 'acknowledged';
  if (status === 401 || status === 403) return 'auth-blocked';
  if (status === 408 || status === 425 || status === 429 || status >= 500) return 'retrying';
  return 'rejected';
}
```

Run in one headless Chromium 156 on 2026-11-03, inside sample code since removed, with 2xx, 401, 403, 422 and 503; 408, 425 and 429 were not sent. A redirect under `redirect: 'error'` rejected the fetch and read as `retrying`.

### Server deduplication contract

The server owns deduplication. The effect and its record commit in one transaction, keyed by the authenticated owner, never by a value from the body. A repeated ID returns success without a second effect, and another owner's entry is refused. Run on in-memory SQLite with serialized transactions: lost acknowledgements gave one effect, the same ID as A and as B one effect each, and A's entry under B's cookie a 403. PostgreSQL and concurrent transactions across connections were not run.

```js
// applied-ops.js. Table: applied_ops (owner_id, op_id, PRIMARY KEY (owner_id, op_id)).
// db.transaction and tx.run stand for your SQL client; the placeholder syntax varies.
export async function postItem(db, sessionOwner, { opId, owner, item }) {
  if (!opId || owner !== sessionOwner) return { status: 403 };  // A's entry under B's cookie
  return db.transaction(async (tx) => {
    const { changes } = await tx.run(
      'INSERT INTO applied_ops (owner_id, op_id) VALUES (?, ?) ON CONFLICT DO NOTHING',
      [sessionOwner, opId],
    );
    if (changes === 0) return { status: 200, body: { opId, duplicate: true } };  // already applied
    await tx.run('INSERT INTO items (owner_id, body) VALUES (?, ?)', [sessionOwner, JSON.stringify(item)]);
    return { status: 201, body: { opId } };
  });
}
```

## Update Prompt Pattern

For the *prompt* policy only: the worker must not call `skipWaiting()` at install. `controllerchange` fires in every tab the worker controls "when the document's associated ServiceWorkerRegistration acquires a new active worker" ([MDN, modified 2026-10-26](https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerContainer/controllerchange_event)), not only in the tab that accepted. So a tab reloads on its own consent and saved state.

```js
// update-page.js. hasUnsavedWork, showUpdateToast and showReloadNotice belong to the app.
export function watchUpdates(registration, { hasUnsavedWork, showUpdateToast, showReloadNotice }) {
  const hadController = Boolean(navigator.serviceWorker.controller);
  let accepted = false;
  const offer = (worker) => showUpdateToast({
    onAccept() {
      accepted = true;
      worker.postMessage({ type: 'SKIP_WAITING' });
    },
  });

  if (registration.waiting && hadController) offer(registration.waiting);
  registration.addEventListener('updatefound', () => {
    const worker = registration.installing;
    worker.addEventListener('statechange', () => {
      if (worker.state === 'installed' && navigator.serviceWorker.controller) offer(worker);
    });
  });
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController) return;  // first install, nothing to replace
    if (accepted && !hasUnsavedWork()) window.location.reload();
    else showReloadNotice();     // "New version active: reload when saved." The user decides.
  });
}
```

```js
// sw-update.js
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
```

A tab that keeps running under the new worker still has old code. If old pages cannot tolerate that (for example, old chunks were removed), ask every tab first and post `SKIP_WAITING` only when all report no unsaved work (design).
