'use client'

import { useEffect } from 'react'

/**
 * Registers the service worker on mount.
 * Only runs in production or when SW is available.
 */
export function ServiceWorkerRegistrar() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .catch(() => {
          // SW registration failed silently — non-critical for app function
        })
    }
  }, [])

  return null
}
