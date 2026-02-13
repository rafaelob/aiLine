'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { ScheduleStep, StepType } from '@/types/exports'

interface VisualScheduleProps {
  /** The lesson plan title shown above the schedule. */
  planTitle: string
  /** Ordered list of lesson steps to render as cards. */
  steps: ScheduleStep[]
  /** Total duration label (computed from steps if omitted). */
  totalDurationMinutes?: number
}

/**
 * Visual schedule renderer for TEA/TDAH-friendly cards.
 * Grid of cards showing lesson steps in order, color-coded by step type.
 * Uses large, clear typography and staggered motion entry animations.
 *
 * Color coding: intro=blue, develop=green, close=orange,
 * activity=purple, assessment=teal.
 */
export function VisualSchedule({
  planTitle,
  steps,
  totalDurationMinutes,
}: VisualScheduleProps) {
  const t = useTranslations('visual_schedule')

  const totalMinutes =
    totalDurationMinutes ??
    steps.reduce((sum, s) => sum + s.durationMinutes, 0)

  return (
    <section aria-labelledby="schedule-title" className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h2
            id="schedule-title"
            className="text-2xl font-bold text-[var(--color-text)]"
          >
            {planTitle}
          </h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {t('subtitle', { steps: steps.length, minutes: totalMinutes })}
          </p>
        </div>
      </div>

      {/* Step cards grid */}
      <ol
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        aria-label={t('steps_label')}
      >
        {steps.map((step, index) => (
          <motion.li
            key={step.stepNumber}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              delay: index * 0.08,
              duration: 0.4,
              ease: [0.25, 0.46, 0.45, 0.94],
            }}
          >
            <StepCard step={step} />
          </motion.li>
        ))}
      </ol>
    </section>
  )
}

/* --- Sub-component --- */

interface StepCardProps {
  step: ScheduleStep
}

function StepCard({ step }: StepCardProps) {
  const t = useTranslations('visual_schedule')
  const colors = STEP_COLORS[step.type]
  const typeKey = `type_${step.type}` as const

  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-xl border-2 p-5',
        'transition-shadow hover:shadow-md',
        'focus-within:ring-2 focus-within:ring-[var(--color-primary)] focus-within:ring-offset-2',
        colors.border,
        colors.bg,
      )}
      tabIndex={0}
      aria-label={t('step_label', { number: step.stepNumber, title: step.title, minutes: step.durationMinutes })}
    >
      {/* Step header */}
      <div className="flex items-center justify-between">
        <span
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-full text-lg font-bold',
            colors.badge,
          )}
          aria-hidden="true"
        >
          {step.stepNumber}
        </span>
        <span
          className={cn(
            'rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
            colors.typeBadge,
          )}
        >
          {t(typeKey)}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-[var(--color-text)]">
        {step.title}
      </h3>

      {/* Description */}
      <p className="text-sm leading-relaxed text-[var(--color-text)]">
        {step.description}
      </p>

      {/* Duration */}
      <div
        className="flex items-center gap-2 text-sm font-medium text-[var(--color-muted)]"
        aria-label={t('duration_label', { minutes: step.durationMinutes })}
      >
        <ClockIcon />
        <span>{step.durationMinutes} min</span>
      </div>

      {/* Materials */}
      {step.materials && step.materials.length > 0 && (
        <div className="mt-1">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
            {t('materials_heading')}
          </p>
          <ul className="flex flex-wrap gap-1.5" aria-label={t('materials_label')}>
            {step.materials.map((material, i) => (
              <li
                key={i}
                className="rounded-md bg-[var(--color-bg)]/60 px-2 py-0.5 text-xs text-[var(--color-text)]"
              >
                {material}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Adaptations */}
      {step.adaptations && step.adaptations.length > 0 && (
        <div className="mt-1">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
            {t('adaptations_heading')}
          </p>
          <ul className="flex flex-col gap-1" aria-label={t('adaptations_label')}>
            {step.adaptations.map((adaptation, i) => (
              <li
                key={i}
                className="flex items-start gap-1.5 text-xs text-[var(--color-muted)]"
              >
                <span aria-hidden="true" className="mt-0.5 text-[var(--color-success)]">
                  *
                </span>
                {adaptation}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  )
}

/* --- Icon --- */

function ClockIcon() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 6v6l4 2m6-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z"
      />
    </svg>
  )
}

/* --- Constants --- */

interface StepColorSet {
  border: string
  bg: string
  badge: string
  typeBadge: string
}

const STEP_COLORS: Record<StepType, StepColorSet> = {
  intro: {
    border: 'border-[var(--color-primary)]/30',
    bg: 'bg-[var(--color-primary)]/10',
    badge: 'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
    typeBadge: 'bg-[var(--color-primary)]/15 text-[var(--color-primary)]',
  },
  develop: {
    border: 'border-[var(--color-success)]/30',
    bg: 'bg-[var(--color-success)]/10',
    badge: 'bg-[var(--color-success)] text-[var(--color-on-primary)]',
    typeBadge: 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
  },
  close: {
    border: 'border-[var(--color-warning)]/30',
    bg: 'bg-[var(--color-warning)]/10',
    badge: 'bg-[var(--color-warning)] text-[var(--color-on-primary)]',
    typeBadge: 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
  },
  activity: {
    border: 'border-[var(--color-secondary)]/30',
    bg: 'bg-[var(--color-secondary)]/10',
    badge: 'bg-[var(--color-secondary)] text-[var(--color-on-primary)]',
    typeBadge: 'bg-[var(--color-secondary)]/15 text-[var(--color-secondary)]',
  },
  assessment: {
    border: 'border-[var(--color-success)]/30',
    bg: 'bg-[var(--color-success)]/10',
    badge: 'bg-[var(--color-success)] text-[var(--color-on-primary)]',
    typeBadge: 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
  },
}
