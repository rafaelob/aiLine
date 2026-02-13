'use client'

import { useEffect, useSyncExternalStore, useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useSpring, useTransform } from 'motion/react'
import { useThemeContext } from '@/hooks/use-theme-context'

interface ScoreGaugeProps {
  score: number
  size?: number
}

/**
 * Subscribe to a trivial "mounted" external store.
 * Avoids the React Compiler warning about setState in useEffect.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function subscribeMounted(onStoreChange: () => void) {
  // Client is always mounted after hydration; no subscription needed.
  return () => {}
}

function getSnapshotMounted() {
  return true
}

function getServerSnapshotMounted() {
  return false
}

/**
 * Radial score gauge 0-100 with animated counter and color interpolation.
 * Red (0) -> Yellow (50) -> Green (100).
 * Uses motion/react for spring physics animation.
 */
export function ScoreGauge({ score, size = 160 }: ScoreGaugeProps) {
  const t = useTranslations('quality')
  // Subscribe to theme changes so Canvas/SVG redraws with correct colors (FINDING-18)
  useThemeContext()

  const mounted = useSyncExternalStore(
    subscribeMounted,
    getSnapshotMounted,
    getServerSnapshotMounted
  )
  const clampedScore = Math.max(0, Math.min(100, score))

  // Spring animation for the score value
  const springValue = useSpring(0, { stiffness: 60, damping: 15 })
  const displayScore = useTransform(springValue, (v) => Math.round(v))

  useEffect(() => {
    springValue.set(clampedScore)
  }, [clampedScore, springValue])

  // SVG arc calculations
  const strokeWidth = 12
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const progress = clampedScore / 100
  const dashOffset = circumference * (1 - progress)

  // Color interpolation: red(0) -> yellow(50) -> green(100)
  const color = scoreToColor(clampedScore)

  return (
    <div
      className="relative inline-flex items-center justify-center"
      role="meter"
      aria-valuenow={clampedScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={t('gauge_label', { score: clampedScore })}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />

        {/* Progress arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ type: 'spring', stiffness: 40, damping: 12, delay: 0.2 }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>

      {/* Centered score number */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-3xl font-bold"
          style={{ color }}
        >
          {mounted ? <MotionNumber value={displayScore} /> : '0'}
        </motion.span>
        <span className="text-xs text-[var(--color-muted)] mt-1">/ 100</span>
      </div>
    </div>
  )
}

/**
 * Animated number display driven by a motion value.
 */
function MotionNumber({ value }: { value: ReturnType<typeof useTransform<number, number>> }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const unsubscribe = value.on('change', (v) => setDisplay(v))
    return unsubscribe
  }, [value])

  return <>{display}</>
}

/**
 * Interpolate score to color: red(0) -> yellow(50) -> green(100).
 */
function scoreToColor(score: number): string {
  if (score <= 50) {
    // Red to yellow
    const t = score / 50
    const r = Math.round(220 + (217 - 220) * t)
    const g = Math.round(38 + (119 - 38) * t)
    const b = Math.round(38 + (6 - 38) * t)
    return `rgb(${r}, ${g}, ${b})`
  }
  // Yellow to green
  const t = (score - 50) / 50
  const r = Math.round(217 + (5 - 217) * t)
  const g = Math.round(119 + (150 - 119) * t)
  const b = Math.round(6 + (105 - 6) * t)
  return `rgb(${r}, ${g}, ${b})`
}
