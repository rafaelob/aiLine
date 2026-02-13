'use client'

import { useCallback, useRef } from 'react'

/**
 * Hook for the View Transitions API (experimental).
 *
 * Wraps document.startViewTransition() with a graceful fallback
 * for browsers that don't support it. When unsupported, the
 * callback runs immediately without animation.
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition
 */
export function useViewTransition() {
  const isTransitioning = useRef(false)

  const supportsViewTransitions =
    typeof document !== 'undefined' &&
    'startViewTransition' in document

  const startTransition = useCallback(
    (updateCallback: () => void | Promise<void>) => {
      if (isTransitioning.current) {
        // Avoid overlapping transitions
        updateCallback()
        return
      }

      if (!supportsViewTransitions) {
        updateCallback()
        return
      }

      isTransitioning.current = true

      const transition = (
        document as Document & {
          startViewTransition: (cb: () => void | Promise<void>) => {
            finished: Promise<void>
          }
        }
      ).startViewTransition(updateCallback)

      transition.finished.finally(() => {
        isTransitioning.current = false
      })
    },
    [supportsViewTransitions],
  )

  return {
    startTransition,
    supportsViewTransitions,
  } as const
}
