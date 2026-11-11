# PWA data, privacy, logout purge and storage eviction

Read this when the app has sign-in, holds personal or sensitive data, or the work touches logout, account switching, push subscriptions, offline queues or storage persistence. Facts were checked on 2026-11-03; "design" marks a rule that comes from the platform facts below, not from a standard.

## 1. What may be cached

Cache Storage keys are URLs, not users. A response cached for user A under `/api/session` is served to user B on the same device unless the worker or the logout purge prevents it. Nothing in the web standards says what may be cached, so the rule is a design choice.

The browser HTTP cache is a separate store, and neither a user-scoped cache name nor a Cache Storage purge touches it. In `default` mode, if the HTTP cache has a fresh match, "it will be returned from the cache" ([MDN Request.cache, modified 2025-06-23](https://developer.mozilla.org/en-US/docs/Web/API/Request/cache)). So A's response with `Cache-Control: private, max-age=600` can reach B through `NetworkOnly`: `private` only keeps it out of shared caches.

| Data class | Examples | Where it may live |
|---|---|---|
| Public | hashed JS/CSS, fonts, public images, public pages | Cache Storage: precache or `CacheFirst` |
| Public data, tolerates age | public reference lists | `StaleWhileRevalidate` is fitting: Workbox describes it for resources "sort of important to keep up to date" ([Workbox strategies, undated, read 2026-11-03](https://developer.chrome.com/docs/workbox/caching-strategies-overview)) |
| Personal or sensitive | session, profile, records, scores, messages | Nowhere. The server sends `Cache-Control: no-store`, the page uses `authFetch` (section 2) and the worker `NetworkOnly`. A deliberate offline copy is a separate permission: section 1, rule 5 |
| Offline fallback page | `/offline` | Precached and identical for every user |

Rules (design):

1. Authenticated navigations are `NetworkOnly` with the precached fallback, and the server sends them with `Cache-Control: no-store`. The worker cannot add it: `fetchOptions` are dropped for navigations (`fetch(request, request.mode === "navigate" ? undefined : fetchOptions)` in `serwist` 9.5.13 and `workbox-strategies` 7.4.1, source read 2026-11-03), and navigation preload ignores them too. Prove the fallback is in the precache with an offline browser test, not by reading config.
2. Gate every runtime cache write with a fail-closed `cacheWillUpdate`. Workbox calls it "before a Response is used to update a cache"; returning `null` cancels the write ([Workbox plugins, undated, read 2026-11-03](https://developer.chrome.com/docs/workbox/using-plugins)). Store only status 200, an allowed content type, no `no-store`, no `private`, not `text/event-stream`.
3. Refuse opaque responses (status 0) in same-origin runtime caches: the worker cannot see the status or body it would store. Do not add `0` to `CacheableResponsePlugin` there. Their quota cost is UNVERIFIED.
4. Never use `CacheFirst` or `StaleWhileRevalidate` for decision-bearing reads (status polls, scores, medications, balances).
5. HTTP `max-age` never grants offline storage. A personal read is stored only when the product lists that route as offline-readable, in a cache named `app-user-<account>` that the purge deletes by prefix. The response keeps `no-store`: "The caching API doesn't honor HTTP caching headers" ([MDN Cache, modified 2026-09-11](https://developer.mozilla.org/en-US/docs/Web/API/Cache)), so that route has its own gate in place of rule 2's header test.
6. On `activate`, delete every cache not on the current allowlist ([MDN `caches.delete`, modified 2025-11-17](https://developer.mozilla.org/en-US/docs/Web/API/CacheStorage/delete) returns a Promise that resolves `true` only if the cache was found and deleted).

## 2. Session expiry, logout and account change

This section states requirements, not an implementation: auth stacks differ, and lifecycle sample code that is right for one product races in another. Build the invariants into the product's own session layer and prove the scenarios with the product's own tests. All of it is design. These are three different events; only logout may end pending work, and only after the user decides.

| Event | Pending writes | Personal reads, drafts | Next |
|---|---|---|---|
| Session expiry (401) | Kept under their owner; replay stops | Nothing deleted; hidden behind sign-in | Same account signs in: replay resumes |
| Logout | Blocked while work is pending: sync, export or explicit discard first. Nothing is deleted until then | Purged in every tab | Sign-in opens once cleanup succeeds |
| Account change | Kept, listed and replayed only for their owner | Purged in every tab: the same cleanup as logout, push included | The other account sees none of them |

### Invariants

1. **One lifecycle lock.** A single named Web Lock serializes sign-in admission, cleanup, the logout pending-work decision and enqueue admission. Checking state outside that lock and acting inside it is the defect: session, barrier and generation are read inside it, enqueue revalidates its originating generation there, and the logout decision and the session transition commit in one hold. Cleanup that finds the barrier already cleared does nothing. The handler that answers a cleanup request never waits for this lock, or the two deadlock. Pages and workers sharing a storage bucket share the lock manager, and `request()` and `query()` can reject with `InvalidStateError` or `SecurityError` ([Web Locks, Editor's Draft 2025-09-24, read 2026-11-03](https://w3c.github.io/web-locks/)): a rejection refuses the operation. Web Locks is Baseline since March 2022 and available in workers ([MDN, modified 2025-04-03](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API)).
2. **A generation per session.** Every personal read and write captures the generation when it starts. Cleanup replaces it and aborts outstanding personal requests. A response commits to UI or storage only if its generation is still current; a late 401 from an old generation never expires a newer session. A page acknowledges cleanup only after old-generation callbacks are fenced: clearing what exists now does not stop what arrives later.
3. **A persisted cleanup barrier.** Set before anything is destroyed, in a store the purge does not touch, and cleared only when every stage succeeded: other pages acknowledged (a closed page counts), stores purged, browser push unsubscribed, server push association removed, and on logout the server session ended. Sign-in is refused while it is set, and retry and start-up resume it. Account change runs the same cleanup as logout, including push; sign-in as another account while a session is recorded goes through it. The barrier keeps the push endpoint until the server confirms removal, because a retry cannot read it after `unsubscribe()`, and server removal must work after the old session expired, the normal case for account change.
4. **A failure envelope.** Each stage catches its own failure, later independent stages still run, the result is `{ ok, failures }`, and any failure keeps the barrier. Page coordination and the final barrier write are stages too, not only the store purge.
5. **The outbox is outside the purge and scoped by owner.** Entries leave only on acknowledgement or explicit discard. Lists and replay filter by owner, and the server checks the owner again.
6. **A durable operation ID.** Once enqueue commits, the caller gets the ID and keeps it through retries; a later failure is a replay failure on that ID, never a reason to resubmit under a new one. Enqueue failure, replay failure, acknowledgement and discard are distinct outcomes. Absence from the queue is never read as acknowledgement: the replay that received the acknowledgement records it. A discard after an unknown send outcome tells the user the server may already have applied it.

### Acceptance scenarios

Every row is a requirement for the product's own tests. The last column says what this skill's authors ran: one headless Chromium 156 on 2026-11-03, against sample code since removed from this skill. It proves neither these invariants as written nor any product. "Not demonstrated" means nobody here has run it.

| Scenario | Invariants | A product must show | Authors' evidence |
|---|---|---|---|
| Overlapping cleanup and sign-in across tabs | 1, 3 | Two tabs run cleanup while a third signs in as B, in each interleaving: sign-in waits or is refused until the barrier clears, no cleanup runs after admission, B's drafts survive | Not demonstrated. Sequential only: sign-in refused while the barrier was set, allowed after retry |
| Late authenticated response after cleanup | 2 | A's held response finishes after cleanup with B signed in: it is aborted or dropped, and nothing of A reaches B's UI, memory or storage | Not demonstrated |
| Enqueue during logout | 1, 5 | An enqueue paused on A's generation while logout runs either commits first, so logout returns pending, or is refused with a visible failure and nothing stored. Logout never succeeds with an undisclosed entry | Not demonstrated. Sequential only: logout with an entry already queued returned pending and kept it |
| Storage failure after enqueue | 6 | Writing a 503 outcome fails: the caller keeps the ID and sees a replay failure, the resend carries that ID, the server applies one effect | Not demonstrated |
| Concurrent discard | 1, 6 | Discard during replay or from a second tab, in each order. Discard commits before the send: it returns discarded and the send never goes out. Acknowledgement commits first: discard returns already delivered, from the recorded outcome. Discard after an unknown outcome: the entry leaves and the user is warned the server may have applied it. A repeat discard changes nothing | Not demonstrated. Sequential only: apart from delivery, explicit discard was the one path that removed an entry |
| Failed push removal | 3, 4 | Browser or server removal fails on logout and on account change: `ok: false`, barrier kept, sign-in refused, retry finishes from the kept endpoint, and only then does the barrier clear | Not demonstrated: no real subscription existed |
| One cleanup stage fails | 3, 4 | Force `locks.query()`, one store and the final barrier write to reject in turn: the other stages still run, the result is `{ ok: false, failures }`, the barrier stays | Partly: a blocked delete with a silent page, and separately a rejecting `databases()`, gave `ok: false` with the rest cleaned; `query()` and the barrier write were not forced |
| Restored tab | 2 | A tab restored with an older generation clears its session data before personal data renders; `sessionStorage` "survives over page reloads and restores" ([MDN, modified 2026-10-12](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage)) | Partly: a reload with an older stamp stood in for real session restore |
| Expiry with pending work | 5 | A 401 deletes nothing and the entry shows `auth-blocked`; logout returns pending; another account sees none of it; the owner returns and it is delivered with one server effect | Demonstrated, on the removed code |

### Code worth keeping

`authFetch` skips the HTTP cache, ran as written, and does nothing for invariant 2. The caller still passes an abort `signal` and checks the generation before committing.

```js
// no-store skips the HTTP cache on both read and write.
export const authFetch = (url, init = {}) =>
  fetch(url, { ...init, cache: 'no-store', credentials: 'same-origin' });
```

The store stage of the envelope, as run. It belongs inside the lifecycle lock with the barrier set. `OUTBOX_DB` is the never-purged store, `DB_PREFIX` and `USER_CACHE_PREFIX` are the app's prefixes, `clearOwned` removes keys with the app's prefix, and `deleteDb` resolves `{ name, ok, reason }` with `ok: true` only on a real `success` event.

```js
// One failing store never stops the others, and never reports success.
// registeredNames is the one list of databases the app and the purge both import.
export async function purgeLocalData(registeredNames = []) {
  const failures = [];
  const attempt = async (name, work) => {
    try { await work(); } catch (err) { failures.push({ name, ok: false, reason: err?.name ?? 'error' }); }
  };

  const names = new Set(registeredNames);
  if ('databases' in indexedDB) {
    await attempt('indexedDB.databases', async () => {
      for (const { name } of await indexedDB.databases()) {
        if (name.startsWith(DB_PREFIX)) names.add(name);
      }
    });
  }
  names.delete(OUTBOX_DB);
  const deleted = await Promise.all([...names].map((name) => deleteDb(name)
    .catch((err) => ({ name, ok: false, reason: err?.name ?? 'error' }))));
  failures.push(...deleted.filter((result) => !result.ok));

  if ('caches' in self) {
    await attempt('caches', async () => {
      const owned = (keys) => keys.filter((key) => key.startsWith(USER_CACHE_PREFIX));
      await Promise.allSettled(owned(await caches.keys()).map((key) => caches.delete(key)));
      for (const name of owned(await caches.keys())) failures.push({ name, ok: false, reason: 'cache' });
    });
  }
  await attempt('localStorage', () => clearOwned(localStorage));
  await attempt('sessionStorage', () => clearOwned(sessionStorage));
  return { ok: failures.length === 0, failures };
}
```

### Platform facts behind the rules

- The logout response sends `Clear-Site-Data: "cache"` for the HTTP cache of browsers that honor it. Never send `"storage"`: it runs `deleteDatabase` on every database, so it destroys retained work, and it unregisters service workers ([MDN, modified 2025-11-21](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Clear-Site-Data)). Safari support was not confirmed (UNVERIFIED), and the header gives no per-store report, so it is never the proof of a purge.
- A closed page cannot acknowledge. Each page can hold its own named lock for its lifetime, separate from the lifecycle lock, because the browser releases it when the page unloads ([Web Locks, section 2.6](https://w3c.github.io/web-locks/)). Worker termination is "vaguely defined" there, so a page ends its own dedicated workers during cleanup.
- Leave no push endpoint or keys in `localStorage`. The Next.js guide shows the same `unsubscribe()` plus a server action ([lastUpdated 2026-07-30](https://nextjs.org/docs/app/guides/progressive-web-apps)).
- A blocked delete is not a success. Every connection the app opens must close on `versionchange`; otherwise "the request's `success` event does not fire, and a `blocked` event is fired on the request instead", and "the deletion stays pending until every connection to the database is closed" ([MDN IDBFactory.deleteDatabase, modified 2026-10-13](https://developer.mozilla.org/en-US/docs/Web/API/IDBFactory/deleteDatabase)). A timeout reports "not confirmed", since the delete may still finish. `indexedDB.databases()` can also reject ([MDN, modified 2025-06-23](https://developer.mozilla.org/en-US/docs/Web/API/IDBFactory/databases)): that is a failure, while its absence leaves the registry as the complete list. When `ok` is false: keep the user signed out, show that local data could not be removed on this device (name the cause: close other tabs of this app), offer retry, and when sign-in was refused after the server authenticated, sign out on the server and keep the blocked screen.
- Also test: two users, one browser, two tabs. B sees none of A's responses (HTTP cache included), pages, queued writes, drafts or subscription. Hold a connection that ignores `versionchange`, purge and assert `ok: false` with reason `blocked`; close it, retry and assert `ok: true`.

## 3. Push privacy

- A push payload can appear on a lock screen: send an id and generic text, fetch details after the click.
- `notificationclick` opens only same-origin paths from an allowlist; refuse any other origin in the payload (`PWA_GUIDE.md`, Push Notifications).
- Subscribe with `userVisibleOnly: true` and show a notification for every event (see `SKILL.md` step 5). Store subscriptions server-side per user and delete them on 404 or 410 from the push service (design; confirm the codes in the push library you use).

## 4. Eviction and persistence

| Fact | Source |
|---|---|
| Default storage is best-effort: kept while the origin is under quota and the device has space; evicted by least-recently-used origin under pressure; eviction removes "all of its data, not parts of it" | [MDN storage quotas, modified 2026-01-05](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria) |
| Safari with cross-site tracking prevention on deletes script-created data (IndexedDB, localStorage, sessionStorage, service worker registrations and caches) after seven days of Safari use without user interaction on the site; server-set cookies are exempt | MDN page above; [WebKit blog, 2020-03-24](https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/) |
| A Home Screen web app has its own counter of days of use | WebKit blog 2020-03-24 |
| `persist()` asks for persistent storage; Firefox prompts the user, Safari and Chromium decide from interaction history | MDN page above; [MDN persist, modified 2026-10-12](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist) |
| WebKit: `persist()` is granted by heuristics such as use as a Home Screen web app; browser apps get an origin quota of up to 60% of disk, other apps 15% | [WebKit blog, 2023-08-10](https://webkit.org/blog/14403/updates-to-storage-policy/) |
| Going over quota throws `QuotaExceededError` from IndexedDB, Cache or OPFS | MDN page above |

Consequences (design):

1. Browser storage is never the only copy of user data. Anything the user created offline reaches the server, or the UI says it is local only.
2. Call `navigator.storage.persist()` after the user has invested data, and treat `false` as normal.
3. Wrap every storage write in `try`/`catch` for `QuotaExceededError`; bound caches by entries and age; check `navigator.storage.estimate()` before large downloads.
4. IndexedDB has a versioned schema with migrations and one registry of database names shared by the app and the purge.
5. After an eviction, the app starts from the server: do not assume a returning user still has a local queue.

## Not covered here

Server-side push sending, encryption of the offline queue (an app design choice, not a platform fact checked here: the owner check keeps retained work out of another account's screens and replay, but it is not encryption), and staleness display (see the staleness reference listed in `SKILL.md`).
