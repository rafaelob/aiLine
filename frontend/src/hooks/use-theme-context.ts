'use client'

import { useSyncExternalStore } from 'react'

/**
 * Hook that subscribes to changes in document.body's `data-theme` attribute
 * via MutationObserver. Triggers re-render when the theme changes, which is
 * necessary for Recharts/Canvas components that cannot read CSS variables
 * dynamically (FINDING-18).
 *
 * Unlike useTheme (which writes themes), this hook is read-only and reacts
 * to external theme changes applied via DOM mutation.
 */

let currentTheme = typeof document !== 'undefined'
  ? document.body.getAttribute('data-theme') ?? 'standard'
  : 'standard'

const listeners = new Set<() => void>()

function notifyListeners() {
  for (const listener of listeners) {
    listener()
  }
}

// Single MutationObserver shared across all subscribers
let observer: MutationObserver | null = null

function ensureObserver() {
  if (observer || typeof MutationObserver === 'undefined') return

  observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (
        mutation.type === 'attributes' &&
        mutation.attributeName === 'data-theme'
      ) {
        const newTheme = document.body.getAttribute('data-theme') ?? 'standard'
        if (newTheme !== currentTheme) {
          currentTheme = newTheme
          notifyListeners()
        }
      }
    }
  })

  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['data-theme'],
  })
}

function subscribe(callback: () => void): () => void {
  listeners.add(callback)
  ensureObserver()
  return () => {
    listeners.delete(callback)
  }
}

function getSnapshot(): string {
  if (typeof document !== 'undefined') {
    currentTheme = document.body.getAttribute('data-theme') ?? 'standard'
  }
  return currentTheme
}

function getServerSnapshot(): string {
  return 'standard'
}

/**
 * Returns the current data-theme value from document.body.
 * Re-renders when the attribute changes via MutationObserver.
 * Use this in Recharts/Canvas components that need to react to theme changes.
 */
export function useThemeContext(): string {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
