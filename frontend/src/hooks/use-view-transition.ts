'use client'

import { useCallback, useRef } from 'react'

type TransitionType = 'route' | 'theme'

interface TransitionOptions {
  /** Origin coordinates for circular reveal (theme morph). */
  x?: number
  y?: number
  /** Transition style — 'route' for slide, 'theme' for circular reveal. */
  type?: TransitionType
}

/**
 * Hook for the View Transitions API.
 *
 * Wraps document.startViewTransition() with a graceful fallback
 * for browsers that don't support it. When unsupported, the
 * callback runs immediately without animation.
 *
 * Supports two transition styles:
 * - 'route': slide cross-fade (default for navigation)
 * - 'theme': circular clip-path reveal from click origin
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition
 */
export function useViewTransition() {
  const isTransitioning = useRef(false)

  const supportsViewTransitions =
    typeof document !== 'undefined' &&
    'startViewTransition' in document

  const startTransition = useCallback(
    (
      updateCallback: () => void | Promise<void>,
      options?: TransitionOptions,
    ) => {
      if (isTransitioning.current) {
        updateCallback()
        return
      }

      if (!supportsViewTransitions) {
        updateCallback()
        return
      }

      isTransitioning.current = true

      // Set transition type so CSS can apply the right animation
      const vtType = options?.type ?? 'route'
      document.documentElement.setAttribute('data-vt-type', vtType)

      // Set origin for circular reveal
      if (vtType === 'theme' && options?.x != null && options?.y != null) {
        document.documentElement.style.setProperty(
          '--vt-x',
          `${options.x}px`,
        )
        document.documentElement.style.setProperty(
          '--vt-y',
          `${options.y}px`,
        )
      }

      const transition = (
        document as Document & {
          startViewTransition: (cb: () => void | Promise<void>) => {
            finished: Promise<void>
          }
        }
      ).startViewTransition(updateCallback)

      transition.finished.finally(() => {
        isTransitioning.current = false
        document.documentElement.removeAttribute('data-vt-type')
        document.documentElement.style.removeProperty('--vt-x')
        document.documentElement.style.removeProperty('--vt-y')
      })
    },
    [supportsViewTransitions],
  )

  return {
    startTransition,
    supportsViewTransitions,
  } as const
}
