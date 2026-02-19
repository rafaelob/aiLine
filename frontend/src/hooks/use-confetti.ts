import { useCallback } from 'react'
import { useAccessibilityStore } from '@/stores/accessibility-store'

/**
 * Hook that fires a celebratory confetti burst.
 * Respects reduced-motion preferences -- no-ops when motion is reduced.
 * Uses dynamic import to keep canvas-confetti out of the main bundle.
 */
export function useConfetti() {
  const reducedMotion = useAccessibilityStore((s) => s.reducedMotion)

  const fire = useCallback(
    async (opts?: { x?: number; y?: number }) => {
      if (reducedMotion) return

      const confetti = (await import('canvas-confetti')).default

      const x = opts?.x ?? 0.5
      const y = opts?.y ?? 0.6

      await confetti({
        particleCount: 80,
        spread: 70,
        origin: { x, y },
        colors: ['#2563EB', '#059669', '#7C3AED', '#FFD700', '#FF6B6B'],
        disableForReducedMotion: true,
        zIndex: 9999,
        scalar: 0.9,
        gravity: 1.2,
        ticks: 150,
      })

      // Mark confetti canvas as decorative for assistive technology
      document.querySelectorAll('canvas').forEach((c) => {
        if (c.style.zIndex === '9999') {
          c.setAttribute('aria-hidden', 'true')
        }
      })
    },
    [reducedMotion]
  )

  return { fire }
}
