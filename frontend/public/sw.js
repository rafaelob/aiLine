// AiLine Service Worker — Offline caching with multi-locale support
const CACHE_VERSION = 2
const CACHE_NAME = `ailine-v${CACHE_VERSION}`

// All supported locales
const LOCALES = ['en', 'pt-BR', 'es']

// Static assets pre-cached at install time (locale-aware)
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.svg',
  '/icons/icon-512x512.svg',
  // Locale root routes
  ...LOCALES.map((l) => `/${l}`),
]

// Install: pre-cache static assets including all locale roots
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

// Activate: clean old caches by version
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith('ailine-') && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  )
  self.clients.claim()
})

// Fetch strategy
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET and cross-origin requests
  if (request.method !== 'GET' || url.origin !== self.location.origin) {
    return
  }

  // SSE connections: never cache (event streams)
  const accept = request.headers.get('Accept') || ''
  if (accept.includes('text/event-stream')) {
    return
  }

  // API calls: network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
          return response
        })
        .catch(() => caches.match(request))
    )
    return
  }

  // Locale page routes: network-first with cache fallback
  const isLocaleRoute = LOCALES.some(
    (l) => url.pathname === `/${l}` || url.pathname.startsWith(`/${l}/`)
  )
  if (isLocaleRoute) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone()
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
          }
          return response
        })
        .catch(() => caches.match(request))
    )
    return
  }

  // Static assets: cache-first with network fallback
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached
      return fetch(request).then((response) => {
        // Cache successful responses for static assets
        if (
          response.ok &&
          (request.url.endsWith('.js') ||
            request.url.endsWith('.css') ||
            request.url.endsWith('.svg') ||
            request.url.endsWith('.woff2') ||
            request.url.endsWith('.png') ||
            request.url.endsWith('.webp'))
        ) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
        }
        return response
      })
    })
  )
})
