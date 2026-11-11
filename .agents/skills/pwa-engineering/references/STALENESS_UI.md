# Staleness and offline-degraded state at the UI layer

Load this when cached or offline-served data reaches a screen the user acts on. Step 6
of `SKILL.md` covers the *storage and sync* half (IndexedDB, optimistic UI, the write
queue) and step 3 covers the *strategy* half. This file covers the half
that neither reaches: what the screen tells the user about how old the number in front
of them is.

All external facts below were verified **2026-07-29** against the sources named inline;
Section 3 was re-verified and corrected **2026-07-30**.

## 1. The service worker knows; the component does not

A `StaleWhileRevalidate` route is, by construction, a decision to show the user
something old. Workbox states the tradeoff plainly: responding from cache "comes with
a tradeoff that users may end up seeing stale data"
(https://developer.chrome.com/docs/workbox/modules/workbox-broadcast-update).

That knowledge lives in the service worker — and even there it is only *provenance*
(cache or network), not age; age is bookkeeping somebody has to do (section 3). The
React/Vue/Svelte component that renders the value receives a resolved `Response` and has
no idea whether it came off the network two seconds ago or out of a cache six days ago.
Unless something carries provenance and age across that boundary, the UI *cannot* be
honest, no matter how well the caching layer is tuned.

**Do not treat this as solved by an online/offline chip.** `navigator.onLine` answers a
different question, and answers it badly. MDN: "Browsers and operating systems leverage
different heuristics... In general, connection to LAN is considered online, even though
the LAN may not have Internet access... Therefore, this property is inherently
unreliable, and you should not disable features based on the online status, only provide
hints when the user may seem offline."
(https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine). `online`/`offline`
events fire on `window`, not on `navigator`.

So: connectivity is a hint about the transport. Staleness is a fact about the record.
They are not the same signal and one does not substitute for the other.

## 2. Three states, not two

Most PWAs ship a binary: normal, or an "You are offline" banner. The user-meaningful
model has three states, and the third is the one that gets skipped:

| State | Meaning | UI obligation |
|---|---|---|
| **Live** | Fetched from the server for this view | Nothing. Silence is the correct signal. |
| **Cached** | Served from cache; age is known and within this surface's tolerance | Show the age, quietly. |
| **Stale / degraded** | Age exceeds tolerance, or a refresh was attempted and failed | Say so at the data, and say when it was last good. |

"Cached" and "stale" are the same mechanism and a different message. Collapsing them
into one is why teams reject the whole idea: a permanent "cached data" chip on every
screen is noise, so it gets removed, and then the genuinely stale case has no channel
left to speak through.

## 3. Two questions, and only one of them has an official bridge

"Did the cached copy change?" and "how old is the value I am showing?" are separate
questions with separate answers. Wiring an age indicator to the signal that answers the
first one is the most common way this gets built wrong.

### `workbox-broadcast-update` says *what* changed, never *how old* it was

Added as a plugin to `StaleWhileRevalidate`, it posts to window clients when a cached
response changed. The documented message is the whole message:

```js
{
  type: 'CACHE_UPDATED',
  meta: 'workbox-broadcast-update',
  payload: {
    cacheName: 'the-cache-name',
    updatedURL: 'https://example.com/'
  }
}
```

A cache name and a URL. **No timestamp, no age, no origin marker, nothing about the copy
that was just replaced.** It fires *because* a fresher copy has landed, so what it
legitimately licenses at the UI layer is a "new data available — reload" affordance, or a
re-read of `updatedURL` by whichever view owns it. It cannot produce "updated 4 min ago",
and it cannot tell you that what the user is currently looking at is six days old,
because it neither knows nor says. Any age rendered next to it came from somewhere else,
and that somewhere else is the thing you actually have to build.

Mechanics that decide whether it fires at all: it compares **headers, not bodies**
(default `headersToCheck` is `Content-Length`, `ETag`, `Last-Modified`, overridable);
register the page listener **before `DOMContentLoaded`**, because browsers queue early
service-worker messages only "up until (but not after)" that event; it does **not** work
with `workbox-precaching`, whose content-hashed URLs are never overwritten in place; and
opaque (cross-origin `no-cors`) responses never trigger it, because their headers are not
readable (https://developer.chrome.com/docs/workbox/modules/workbox-broadcast-update).

### Age has to come from a source you own

Two options, in decreasing order of how well they survive production:

1. **Timestamp the record, not the response.** When reads and writes both go through
   IndexedDB, store `fetchedAt` (and `syncedAt`) on the row itself. The screen then reads
   an age from its own data layer with no service-worker coupling at all. Prefer this on
   any read-write surface and on anything with a real staleness tolerance. If you also
   want a server-authored anchor, put the timestamp **in the response payload**, where it
   is readable, versioned with the data, and cached alongside it — unlike a header, it
   cannot be stripped by an intermediary or lost to opacity.
2. **Read the `Date` header off the cached `Response`.** Cheapest to add, weakest in
   practice. `Date` is "the date and time at which the message originated"
   (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Date) — i.e. when
   the *response* was produced upstream, not when your app last reconciled with the
   server, and not accounting for time the copy spent in an intermediate cache. It also
   needs the header to be present, and it is unreadable on opaque responses.

Workbox's own expiration plugin splits along exactly this line, which is the tell: it
keeps entry ages in its own IndexedDB — hence its `updateTimestamp()` API — and skips
that lookup only when a `Date` header is present
(https://developer.chrome.com/docs/workbox/modules/workbox-expiration). Age is
bookkeeping someone has to keep; it is not a property the cached `Response` hands you,
and it is not in a `CACHE_UPDATED` message.

Whichever you pick, provenance *and* age must arrive as data the view layer can render
and branch on — not as a console log, and not as a variable that only the service worker
sees.

## 4. Bind the indicator to the data, not to the app shell

A global banner in the shell is the wrong place, and it is where almost everyone puts it,
because the shell is where the connectivity state already lives.

- The shell banner answers "is the app online". The user's question is "is *this value*
  current".
- One screen can hold both live and stale regions at once (a live form beside a cached
  summary). A single shell-level flag cannot express that, so it either lies about the
  fresh part or lies about the stale part.
- Placement follows consequence: put the marker on the surface the user is about to act
  from — the figure, the row, the card, the total — not in a corner of the chrome that
  eyes stop seeing after two sessions.

How the marker looks (weight, escalation styling) is `frontend-design`'s; the rule kept
here is that it is bound to the data region and escalates from the surface's tolerance.

## 5. Tolerance is per-surface and is a domain decision

There is no global staleness threshold, and inventing one in a config file is how the
indicator ends up wrong everywhere at once. Tolerance belongs to the surface:

- A trend chart or an activity feed tolerates hours. Showing an age at all may be enough.
- A value that gates an irreversible or safety-relevant action tolerates very little, and
  when it cannot be refreshed the honest UI blocks or explicitly downgrades the action
  rather than rendering a confident-looking number.
- A list used for navigation tolerates a lot; the detail record it leads to may tolerate
  nothing.

Decide tolerance per surface, write it next to the surface, and derive the indicator's
escalation from it. Highest-consequence screens are where this matters most — and, per
the field note below, where it is most often missing.

## 6. A queued write is not a confirmed write

Offline reads and offline writes fail differently, and the write case is the one that
does real damage. Background Sync and an IndexedDB outbox (`SKILL.md` step 6) make the mutation
*durable*; they do not make it *done*. If optimistic UI renders a queued mutation
identically to a server-confirmed one, the interface has asserted something false.

- Mark unconfirmed rows/fields distinctly until the server acknowledges them.
- Keep the marker until acknowledgement, not until the local write returns.
- Give the queue a visible surface: how many pending, since when, and what happens if
  the replay conflicts. Conflict resolution strategy is a domain choice (last-write-wins, merge); *telling the user a
  conflict happened and what was kept* is this layer.
- Never silently swallow a failed replay. A mutation the user believes landed and that
  never landed is worse than an error at submit time.

## 7. Make the indicator accessible

A staleness signal is a dynamic status change that assistive technology misses by default:
colour-alone, live-region and text-alternative rules belong to the `accessibility` skill.
Apply them to the marker and to its transitions.

## 8. Checklist

- [ ] Every screen that renders cached data can distinguish live / cached / stale, not
      just online / offline.
- [ ] Cache **age** reaches the view layer from a source that actually carries an age — a
      record timestamp, or a timestamp in the response payload/`Date` header — not
      inferred, not assumed, and **not** from a `CACHE_UPDATED` broadcast, whose payload is
      only `cacheName` + `updatedURL`.
- [ ] If `workbox-broadcast-update` is used, it drives a "new data available" affordance or
      a re-read, not an age display; its listener is registered before `DOMContentLoaded`
      and the route is not a precached one.
- [ ] The indicator sits on the data region, not only in the app shell.
- [ ] A staleness tolerance is written down per surface, and the highest-consequence
      surfaces were checked first rather than last.
- [ ] Unconfirmed (queued) writes are visually distinct from acknowledged writes, and
      stay distinct until the server acknowledges.
- [ ] Failed sync replays surface to the user; none are swallowed.
- [ ] The indicator and its transitions pass the `accessibility` checks (section 7).
- [ ] `navigator.onLine` is used as a hint only, never as the sole source of the
      staleness story and never to hard-disable features (per MDN, above).

## 9. Field note

[observed] A production clinical application already had a staleness indicator
component built, styled, and working — and it was wired into none of the screens where
a stale value carried the highest consequence. The caching layer was sound; the
component existed; the binding to the risky surfaces was simply never done, and no
checklist in the delivery path asked for it.

The generalisable failure is not "we lacked a component". It is that offline capability
was treated as finished when the service worker was correct, so the last hop — from
cache mechanics to what the screen actually claims — was nobody's step. Audit the
highest-consequence screens first: an unused indicator is indistinguishable, from the
user's side, from an indicator that was never built.

## 10. Correction log

**2026-07-30 — section 3 rewritten.** The first version of this file titled section 3 "Getting the age
to the component" and listed `workbox-broadcast-update` as mechanism 1 of 3, and the section 8
checklist named it as a source of cache age. That was wrong, and wrong in the direction
that produces a lying indicator: the documented `CACHE_UPDATED` payload is
`{ cacheName, updatedURL }` and nothing else — it reports **which URL in which cache
changed**, carrying no timestamp, no age, and no marker of the copy it replaced
(re-verified https://developer.chrome.com/docs/workbox/modules/workbox-broadcast-update,
2026-07-30). An age display built on it would have had to invent the number. Section 3 now
splits the two questions: broadcast-update answers "did it change" and drives a reload
affordance; age comes from a record timestamp, a timestamp in the response payload, or
the `Date` header — sources the app owns and that actually carry a time.
