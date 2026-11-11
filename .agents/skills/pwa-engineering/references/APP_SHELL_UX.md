# PWA app shell UX: the build side of the installed app

Read this when building the installed-app experience: install prompt timing, offline and update states, safe areas, `display_override`. It is the build side; visual direction, navigation and slot layout stay in the `frontend-design` skill, and target sizes, live regions and colour-alone rules in `accessibility`. Checked 2026-11-03; "design" marks a rule that is a choice, not a standard.

## 1. Install prompt

- Capture `beforeinstallprompt`, call `preventDefault()`, keep the event, and call `prompt()` only from a click on your own control. MDN's example keeps the button hidden until the event arrives and clears the stored event after `prompt()` ([MDN, modified 2026-10-26](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)). Treat the event as Chromium-only: MDN marks it "Limited availability".
- Timing, from web.dev ([promote-install](https://web.dev/articles/promote-install), undated, read 2026-11-03): show the promotion only after the event has fired; wait until the user has shown interest ("after a few interactions" for a snackbar), not on first load; let the user dismiss it and remember that; limit frequency; a snackbar stays up 4 to 7 seconds.
- Design: a threshold such as the second session and a stored cooldown (for example 30 days) in `localStorage`, wrapped in `try`/`catch` because storage can be blocked. Keep the number in one constant and state the same number in the comment.
- Hide the control on `appinstalled` and when `matchMedia('(display-mode: standalone)').matches` is true.
- iOS has no install event. Show a dismissible instruction (Share, then Add to Home Screen) when the user agent is iOS and the app is not standalone, as the Next.js guide does ([lastUpdated 2026-07-30](https://nextjs.org/docs/app/guides/progressive-web-apps)). Since iOS 26 the user can turn "Open as Web App" off for a Home Screen site, so the app may be on the Home Screen yet not standalone ([WebKit, 2025-06-09](https://webkit.org/blog/16993/news-from-wwdc25-web-technology-coming-in-safari-26-beta/)).
- Ask for notification permission as a separate step after install, from a tap, with the value explained. On iOS it only works from the Home Screen app.

## 2. Offline and stale states

- `navigator.onLine` is a hint about transport, not about the data. Do not disable features from it.
- Show three states per data region, not one banner for the shell: live, cached with its age, stale or failed refresh with the last good time. A global "offline" chip cannot describe one screen that holds both a live form and a cached summary. The age must come from the record or the response payload; the staleness reference named in `SKILL.md` covers how.
- Queued writes are marked unconfirmed until the server acknowledges them, and a failed replay is shown, never swallowed.
- The offline fallback page is precached, identical for every user, and offers a retry. Prove it with the browser set offline on a production build.
- With Serwist on Next, `reloadOnOnline` reloads the page on each `online` event: `SERWIST_NEXT.md` section 5.

## 3. Update flow

Pick the policy from `SKILL.md` step 4 and make the page match the worker.

| Policy | Worker | Page |
|---|---|---|
| Prompt | No `skipWaiting` at install; on `SKIP_WAITING` message call `skipWaiting()` | Toast "Update available" with a **Reload** action that posts the message. On `controllerchange`, only the tab that accepted and has no unsaved work reloads; every other tab shows a notice. Do not auto-dismiss it before the user can act |
| Silent | `skipWaiting()` + `clients.claim()` | No prompt. A short notice is fine, but a toast without an action is only information. Use only when no unsaved state can exist |

A prompt component fed by a worker that always calls `skipWaiting()` never fires, and a toast that appears and offers no reload is dead UI: delete one side. web.dev warns that after `skipWaiting()` the new worker "is likely controlling pages that were loaded with an older version" ([service-worker-lifecycle](https://web.dev/articles/service-worker-lifecycle), undated). In a form or editor, defer the reload until the work is saved.

## 4. Safe areas, viewport and scrolling

- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`. Without `viewport-fit=cover`, Safari insets content to the safe area; with it, the page lays out to the full screen and must use `env(safe-area-inset-*)` ([WebKit, 2017-09-22](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)).
- Pad every fixed or sticky bar with the matching inset and give `env()` a fallback after the first comma: `padding-bottom: env(safe-area-inset-bottom, 0px)`. Give the page content an equal bottom padding so the last row is not hidden behind a fixed bar. `env()` is Baseline widely available since January 2020 ([MDN, modified 2026-10-08](https://developer.mozilla.org/en-US/docs/Web/CSS/env)).
- Full-height shells: `100vh` equals `lvh`. MDN says the dynamic units (`dvh`) "are not stable, even when the viewport itself is unchanged" and can resize content while the user scrolls, whereas `svh` and `lvh` are fixed ([MDN length, modified 2026-07-08](https://developer.mozilla.org/en-US/docs/Web/CSS/length)). Use `min-height: 100svh` for the shell and `dvh` only where tracking the visible area matters. Per-unit Baseline dates were not shown on that page: UNVERIFIED.
- `overscroll-behavior: contain` on modals and inner scrollers. MDN marks the property "Limited availability" ([modified 2026-10-13](https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior)); Safari behaviour is UNVERIFIED, so check on a device.
- A fixed bar can cover inputs when the on-screen keyboard opens: test on a real phone, since keyboard resizing differs by browser (UNVERIFIED here).

## 5. `display_override` and window controls

- `display_override` is a list of display modes; the browser applies the first it supports, then falls back to `display` ([web.dev add-manifest](https://web.dev/articles/add-manifest), undated; [MDN, modified 2025-11-13](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/display_override), marked Experimental). Keep `display` as the fallback, and list only modes the CSS supports.
- `window-controls-overlay` applies only to an installed PWA window on a desktop OS (Chromium 104). The page must position its header with `env(titlebar-area-x|y|width|height)` (give each a fallback) and mark drag regions with `app-region: drag` (still `-webkit-app-region`), otherwise "the window is no longer draggable (apart from a very small area)" ([web.dev window-controls-overlay](https://web.dev/articles/window-controls-overlay), undated). If you do not build that layout, remove it from the list.
- Manifest screenshots: width and height 320 to 3840 px, longer side at most 2.3 times the shorter, optional `form_factor` of `wide` or `narrow`; desktop Chrome shows 1 to 8, Android up to 5 (web.dev add-manifest). Use real raster screenshots of the app, not a logo and not SVG.
- Give the manifest an `id` so `start_url` can change later (web.dev add-manifest).

## Not covered here

Visual direction, navigation and slot layout, the age marker's look, theme colour tokens (`frontend-design`); target sizes, live regions and colour-alone rules (`accessibility`); push sending; the logout purge.
