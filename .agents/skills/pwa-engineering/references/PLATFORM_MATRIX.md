# PWA platform matrix: install path and limits

Read this when deciding what to build per platform, writing install instructions, or answering "does this work on iOS, Android or desktop". Checked 2026-11-03; every row names its source. A cell marked UNVERIFIED was not confirmed on a primary page. Browser versions move: re-check caniuse and the WebKit blog before quoting a version.

## 1. Install

| Platform | Install path | Install event for your UI | Source |
|---|---|---|---|
| iOS / iPadOS Safari | Share menu > Add to Home Screen. Since iOS 26 every site added to the Home Screen opens as a web app by default; the user can switch "Open as Web App" off | None: `beforeinstallprompt` "is not supported on iOS". Show instructions | [MDN Making PWAs installable, modified 2026-10-06](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable); [WebKit blog, 2025-06-09](https://webkit.org/blog/16993/news-from-wwdc25-web-technology-coming-in-safari-26-beta/) |
| iOS 16.4+ other browsers | Chrome, Edge, Firefox and Orion can also install from the Share menu. iOS 16.3 and earlier: Safari only | None | MDN, same page |
| Android Chrome (Chromium) | Install from the browser once the install criteria are met: HTTPS, manifest with `name` or `short_name`, 192px and 512px icons, `start_url`, `display` (or `display_override`), and a click plus 30 seconds of viewing | `beforeinstallprompt`, then `prompt()` from your own button | [web.dev install-criteria, undated, read 2026-11-03](https://web.dev/articles/install-criteria); MDN, same page |
| Desktop Chrome / Edge | Chromium supports installing PWAs with a manifest on all supported desktop OSes. Same criteria as above | `beforeinstallprompt` | MDN, same page |
| Desktop Safari | File > Add to Dock on macOS Sonoma (Safari 17) and later, for any web app with or without a manifest | None | MDN, same page |
| Desktop Firefox | Browser-provided, not from the manifest: "Firefox does not support installing PWAs using a manifest file", but since Firefox 143 on Windows a site can be pinned and run as a web app from the taskbar, except on Microsoft Store installs. Other desktop OSes: UNVERIFIED | None | MDN, same page; [Firefox 143.0 release notes, 2025-09-16](https://www.mozilla.org/en-US/firefox/143.0/releasenotes/) |
| Android Firefox | Browser-provided, not WebAPK: adds a browser-badged home-screen shortcut that opens the site in the browser. Mozilla's support pages could not be read (CAPTCHA, 2026-11-03), so the menu steps are UNVERIFIED | None | MDN, same page |

Four things vary independently, so test each one per row: install promotion (`beforeinstallprompt`), manifest processing, WebAPK packaging (Android: only Chrome with Google Mobile Services and Samsung Internet, MDN, same page) and browser-provided install.

A service worker is not a requirement for installability on any row (MDN, same page). `beforeinstallprompt` is marked "Limited availability" by MDN ([modified 2026-10-26](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)): treat it as Chromium-only progressive enhancement and always ship the iOS instruction path. The Next.js guide does not recommend a custom `beforeinstallprompt` button for the same reason ([lastUpdated 2026-07-30](https://nextjs.org/docs/app/guides/progressive-web-apps)).

## 2. Capabilities and limits

| Capability | iOS / iPadOS (WebKit) | Android Chrome | Desktop |
|---|---|---|---|
| Web Push | Only for a web app on the Home Screen; the permission request must follow direct user interaction (iOS 16.4+, [WebKit 2023-02-16](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)). Delivery goes through APNs: allow `*.push.apple.com` | Supported (Chromium; Next.js guide list) | Chromium and Firefox supported (Next.js guide, 2026-07-30); Safari 16.1 on macOS Ventura (WebKit 2023-02-16; [caniuse](https://caniuse.com/push-api), read 2026-11-03) |
| Silent push | No: subscriptions stay `userVisibleOnly: true` and every push shows a notification ([WebKit 2025-03-27](https://webkit.org/blog/16535/meet-declarative-web-push/)) | Chrome and Edge reject `subscribe()` without `userVisibleOnly: true` ([MDN, modified 2025-06-23](https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe)) | Same as Android Chrome for Chromium |
| Declarative Web Push | iOS/iPadOS 18.4+ for Home Screen web apps ([WebKit 2025-03-31](https://webkit.org/blog/16574/webkit-features-in-safari-18-4/)); keep the imperative handler for older browsers | UNVERIFIED | UNVERIFIED (the 2025-03-31 post limits it to iOS and iPadOS) |
| Badging API | `setAppBadge` / `clearAppBadge` supported for Home Screen web apps (WebKit 2023-02-16) | UNVERIFIED | UNVERIFIED |
| Background Sync | No (caniuse, through Safari 27.2 on iOS) | Yes (Chrome for Android) | Chrome 49+, Edge 79+; no Firefox; no Safari ([caniuse](https://caniuse.com/background-sync), read 2026-11-03) |
| Periodic Background Sync | UNVERIFIED | UNVERIFIED | UNVERIFIED. Treat as Chromium-only |
| Screen Wake Lock | iOS/iPadOS 18.4+ including Home Screen web apps (WebKit 2025-03-31) | UNVERIFIED | UNVERIFIED |
| Launch Handler | Not usable: MDN marks it Experimental and "Limited availability" ([modified 2025-09-14](https://developer.mozilla.org/en-US/docs/Web/API/Launch_Handler_API)) | same | same |
| `display_override` | Experimental on MDN ([modified 2025-11-13](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/display_override)); per-browser support not shown on the page: UNVERIFIED | Chromium install criteria accept `display_override` in place of `display` (MDN Making PWAs installable, 2026-10-06) | `window-controls-overlay`: desktop installed PWAs only, Chromium 104+ ([web.dev, undated](https://web.dev/articles/window-controls-overlay)) |
| Service Worker static routing | Safari 27.0+ ([WebKit 2026-09-17](https://webkit.org/blog/18325/webkit-features-for-safari-27-0/)) | UNVERIFIED | UNVERIFIED |

## 3. Storage

| Rule | iOS / Safari | Chromium | Firefox |
|---|---|---|---|
| Origin quota | Browser apps up to 60% of disk (WebKit 2023-08-10); Home Screen web apps share the same limits; other apps 15% | Up to 60% of disk | Best-effort min(10% of disk, 10 GiB) |
| Inactivity wipe | Script-created data deleted after seven days of Safari use without user interaction when cross-site tracking prevention is on; server-set cookies exempt. A Home Screen web app has its own counter | None listed | None listed |
| `persist()` | Decided by heuristics (for example Home Screen use) | Decided from interaction history, no prompt | Prompts the user |

Sources: [MDN storage quotas, modified 2026-01-05](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria); [WebKit 2020-03-24](https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/); [WebKit 2023-08-10](https://webkit.org/blog/14403/updates-to-storage-policy/). When an origin is evicted, "all of its data, not parts of it, is deleted at the same time" (MDN). Design consequences and the purge requirements: see the data and privacy reference listed in `SKILL.md`.

## 4. What to build per platform

1. **Always:** HTTPS, complete manifest with PNG icons, an offline or error state that does not depend on push or sync.
2. **iOS:** Share-menu instructions, a `apple-touch-icon` PNG, push offered only after the app is on the Home Screen and after a tap, no reliance on Background Sync, and a replay on `online` and `visibilitychange`. Do not assume standalone: "Open as Web App" can be switched off, so detect with `matchMedia('(display-mode: standalone)')` ([Next.js guide](https://nextjs.org/docs/app/guides/progressive-web-apps)). `navigator.standalone` is a Safari-specific flag: UNVERIFIED on a primary page.
3. **Android Chrome and desktop Chromium:** custom install button driven by `beforeinstallprompt`; Background Sync only as an enhancement.
4. **Firefox and Safari desktop:** test offline, manifest and push. Test the browser-provided install in Firefox on Windows and Android and in Safari; do not expect a prompt event or manifest-driven install in Firefox.
5. **Verify on devices:** DevTools push simulation does not prove iOS delivery. Test on an iPhone with the app on the Home Screen.

## 5. Open questions (UNVERIFIED on 2026-11-03)

- EU: Apple announced removal of Home Screen web apps for iOS 17.4 in the EU and reversed it on 2024-03-01 according to press reports; Apple's own page was not reached and the 2026 status is unknown. Check Apple's developer site before stating the EU position.
- Whether any Safari 27.x release changed PWA install or push behaviour: the WebKit feature posts for 27.0 (2026-09-17), 27.1 (2026-10-23) and 27.2 (2026-10-26) list no such item, but Apple's release notes were not reached.
- Periodic Background Sync support matrix.
