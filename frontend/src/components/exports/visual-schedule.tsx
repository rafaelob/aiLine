'use client'

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
            className="text-2xl font-bold text-gray-900 dark:text-white"
          >
            {planTitle}
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Agenda Visual - {steps.length} etapas - {totalMinutes} min total
          </p>
        </div>
      </div>

      {/* Step cards grid */}
      <ol
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        aria-label="Etapas da aula em ordem"
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
  const colors = STEP_COLORS[step.type]

  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-xl border-2 p-5',
        'transition-shadow hover:shadow-md',
        'focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2',
        colors.border,
        colors.bg,
      )}
      tabIndex={0}
      aria-label={`Etapa ${step.stepNumber}: ${step.title}, ${step.durationMinutes} minutos`}
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
          {STEP_TYPE_LABELS[step.type]}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
        {step.title}
      </h3>

      {/* Description */}
      <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
        {step.description}
      </p>

      {/* Duration */}
      <div
        className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400"
        aria-label={`Duração: ${step.durationMinutes} minutos`}
      >
        <ClockIcon />
        <span>{step.durationMinutes} min</span>
      </div>

      {/* Materials */}
      {step.materials && step.materials.length > 0 && (
        <div className="mt-1">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Materiais
          </p>
          <ul className="flex flex-wrap gap-1.5" aria-label="Materiais necessários">
            {step.materials.map((material, i) => (
              <li
                key={i}
                className="rounded-md bg-white/60 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800/60 dark:text-gray-300"
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
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Adaptações
          </p>
          <ul className="flex flex-col gap-1" aria-label="Adaptações de acessibilidade">
            {step.adaptations.map((adaptation, i) => (
              <li
                key={i}
                className="flex items-start gap-1.5 text-xs text-gray-600 dark:text-gray-400"
              >
                <span aria-hidden="true" className="mt-0.5 text-green-500">
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

const STEP_TYPE_LABELS: Record<StepType, string> = {
  intro: 'Introdução',
  develop: 'Desenvolvimento',
  close: 'Fechamento',
  activity: 'Atividade',
  assessment: 'Avaliação',
}

interface StepColorSet {
  border: string
  bg: string
  badge: string
  typeBadge: string
}

const STEP_COLORS: Record<StepType, StepColorSet> = {
  intro: {
    border: 'border-blue-300 dark:border-blue-700',
    bg: 'bg-blue-50 dark:bg-blue-950',
    badge: 'bg-blue-600 text-white',
    typeBadge: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  },
  develop: {
    border: 'border-green-300 dark:border-green-700',
    bg: 'bg-green-50 dark:bg-green-950',
    badge: 'bg-green-600 text-white',
    typeBadge: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  },
  close: {
    border: 'border-orange-300 dark:border-orange-700',
    bg: 'bg-orange-50 dark:bg-orange-950',
    badge: 'bg-orange-600 text-white',
    typeBadge: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  },
  activity: {
    border: 'border-purple-300 dark:border-purple-700',
    bg: 'bg-purple-50 dark:bg-purple-950',
    badge: 'bg-purple-600 text-white',
    typeBadge: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  },
  assessment: {
    border: 'border-teal-300 dark:border-teal-700',
    bg: 'bg-teal-50 dark:bg-teal-950',
    badge: 'bg-teal-600 text-white',
    typeBadge: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  },
}
