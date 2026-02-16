'use client'

import { useRef, useEffect, useState } from 'react'
import { useMotionValue, animate, useInView, useReducedMotion } from 'motion/react'

export interface SpringConfig {
  stiffness: number
  damping: number
  mass: number
}

const DEFAULT_SPRING: SpringConfig = {
  stiffness: 100,
  damping: 15,
  mass: 0.5,
}

/**
 * Spring-physics count-up that triggers when scrolled into view.
 * Respects reduced motion: shows final value immediately without animation.
 * Announces final count to screen readers via aria-live region.
 */
export function AnimatedCounter({
  value,
  suffix = '',
  label,
  spring = DEFAULT_SPRING,
  viewMargin = '-10px',
}: {
  value: number
  suffix?: string
  label?: string
  spring?: SpringConfig
  viewMargin?: `${number}${'px' | '%'}`
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const motionValue = useMotionValue(0)
  const isInView = useInView(ref, { once: true, margin: viewMargin })
  const prefersReducedMotion = useReducedMotion()
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!isInView) return

    if (prefersReducedMotion) {
      if (ref.current) ref.current.textContent = `${value}${suffix}`
      queueMicrotask(() => setDone(true))
      return
    }

    const controls = animate(motionValue, value, {
      type: 'spring',
      ...spring,
      onComplete: () => queueMicrotask(() => setDone(true)),
    })
    return () => controls.stop()
  }, [value, isInView, motionValue, spring, prefersReducedMotion, suffix])

  useEffect(() => {
    if (prefersReducedMotion) return

    const unsubscribe = motionValue.on('change', (latest) => {
      if (ref.current) {
        ref.current.textContent = `${Math.round(latest)}${suffix}`
      }
    })
    return unsubscribe
  }, [motionValue, suffix, prefersReducedMotion])

  return (
    <>
      <span ref={ref}>{`${value}${suffix}`}</span>
      {done && label && (
        <span className="sr-only" aria-live="polite">
          {value}{suffix} {label}
        </span>
      )}
    </>
  )
}
