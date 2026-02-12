'use client'

import { useEffect } from 'react'
import { useAccessibilityStore } from '@/stores/accessibility-store'

/**
 * Client component that hydrates accessibility preferences from localStorage
 * on mount and applies them to the DOM.
 * Must be rendered inside the body to access document.body.
 */
export function A11yHydrator() {
  const hydrate = useAccessibilityStore((s) => s.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  return null
}
