'use client'

import { useOptimistic, useCallback, useTransition } from 'react'

/**
 * Generic optimistic setting hook for instant UI feedback.
 *
 * Wraps React 19's useOptimistic to show the new value immediately
 * while the actual persist action (localStorage, API call) runs
 * inside a transition.
 *
 * Usage:
 *   const [value, setValue] = useOptimisticSetting(storeValue, persistFn)
 */
export function useOptimisticSetting<T>(
  currentValue: T,
  persistAction: (newValue: T) => void,
): [T, (newValue: T) => void] {
  const [optimisticValue, setOptimistic] = useOptimistic(currentValue)
  const [, startTransition] = useTransition()

  const setValue = useCallback(
    (newValue: T) => {
      // Show optimistic value immediately
      setOptimistic(newValue)

      // Persist in a transition so it doesn't block the UI
      startTransition(() => {
        persistAction(newValue)
      })
    },
    [setOptimistic, persistAction],
  )

  return [optimisticValue, setValue]
}
