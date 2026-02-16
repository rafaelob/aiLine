'use client'

import { cn } from '@/lib/cn'
import { AnimatedCounter } from '@/components/shared/animated-counter'

interface LandingStatsProps {
  personas: string
  languages: string
  models: string
  standards: string
  sectionLabel: string
}

const LANDING_SPRING = {
  stiffness: 80,
  damping: 18,
  mass: 0.6,
} as const

/**
 * Animated stat counters with "+" suffixes, dividers, and spring count-up on scroll.
 */
export function LandingStats({ personas, languages, models, standards, sectionLabel }: LandingStatsProps) {
  const stats = [
    { value: 9, suffix: '+', label: personas },
    { value: 3, suffix: '+', label: languages },
    { value: 5, suffix: '+', label: models },
    { value: 3, suffix: '+', label: standards },
  ]

  return (
    <section
      className="py-8 md:py-12 px-6 bg-[var(--color-surface)]"
      aria-label={sectionLabel}
    >
      <div
        className={cn(
          'max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-8',
          'sm:[&>*+*]:border-l sm:[&>*+*]:border-[var(--color-border)]',
          'sm:[&>*+*]:pl-8'
        )}
      >
        {stats.map((stat) => (
          <div key={stat.label} className="flex flex-col items-center gap-2">
            <div className="flex items-baseline">
              <span className="text-4xl sm:text-5xl font-bold text-[var(--color-text)]">
                <AnimatedCounter
                  value={stat.value}
                  suffix={stat.suffix}
                  label={stat.label}
                  spring={LANDING_SPRING}
                  viewMargin="-20px"
                />
              </span>
            </div>
            <span className="text-sm text-[var(--color-muted)] font-medium">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
