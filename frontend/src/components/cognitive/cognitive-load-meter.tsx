'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

export interface CognitiveLoadFactors {
  uiDensity: number    // 0-100: how dense the visible UI is
  readingLevel: number // 0-100: reading complexity score
  interactionCount: number // active interactive elements count
}

interface CognitiveLoadMeterProps {
  factors: CognitiveLoadFactors
}

function computeLoadScore(factors: CognitiveLoadFactors): number {
  // Weighted heuristic: density 40%, reading 35%, interactions 25%
  const normalizedInteractions = Math.min(100, factors.interactionCount * 10)
  return Math.round(
    factors.uiDensity * 0.4 +
    factors.readingLevel * 0.35 +
    normalizedInteractions * 0.25
  )
}

function getLoadLevel(score: number): 'low' | 'medium' | 'high' {
  if (score < 40) return 'low'
  if (score < 70) return 'medium'
  return 'high'
}

const LEVEL_COLORS = {
  low: {
    bar: 'bg-[var(--color-success)]',
    text: 'text-[var(--color-success)]',
    bg: 'bg-[var(--color-success)]/10',
  },
  medium: {
    bar: 'bg-[var(--color-warning)]',
    text: 'text-[var(--color-warning)]',
    bg: 'bg-[var(--color-warning)]/10',
  },
  high: {
    bar: 'bg-[var(--color-error)]',
    text: 'text-[var(--color-error)]',
    bg: 'bg-[var(--color-error)]/10',
  },
} as const

/**
 * Cognitive load meter.
 * Displays a heuristic score based on UI density, reading complexity,
 * and active interaction count relative to the learner profile.
 */
export function CognitiveLoadMeter({ factors }: CognitiveLoadMeterProps) {
  const t = useTranslations('cognitive_load')

  const score = useMemo(() => computeLoadScore(factors), [factors])
  const level = useMemo(() => getLoadLevel(score), [score])
  const colors = LEVEL_COLORS[level]

  const factorItems = [
    { key: 'ui_density', value: factors.uiDensity },
    { key: 'reading_level', value: factors.readingLevel },
    { key: 'interaction_count', value: factors.interactionCount },
  ]

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">
          {t('title')}
        </h3>
      </div>

      {/* Score display */}
      <div
        className={cn(
          'rounded-[var(--radius-md)] p-4',
          'border border-[var(--color-border)]'
        )}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[var(--color-muted)]">{t('level')}</span>
          <span className={cn('text-xs font-semibold', colors.text)}>
            {t(level)}
          </span>
        </div>

        {/* Progress bar */}
        <div
          className="h-2 rounded-full bg-[var(--color-border)] overflow-hidden"
          role="progressbar"
          aria-valuenow={score}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={t('score_label')}
        >
          <div
            className={cn('h-full rounded-full transition-all', colors.bar)}
            style={{ width: `${Math.min(100, score)}%` }}
          />
        </div>

        <p className="text-right text-[10px] font-mono text-[var(--color-muted)] mt-1">
          {score}/100
        </p>
      </div>

      {/* Factor breakdown */}
      <section aria-labelledby="factors-heading">
        <h4
          id="factors-heading"
          className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-2"
        >
          {t('factors')}
        </h4>
        <div className="space-y-2">
          {factorItems.map(({ key, value }) => (
            <div key={key} className="flex items-center justify-between text-xs">
              <span className="text-[var(--color-muted)]">{t(key)}</span>
              <span className="font-mono text-[var(--color-text)]">{value}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Suggestion */}
      <div className={cn('rounded-[var(--radius-md)] p-3', colors.bg)}>
        <p className="text-xs font-medium text-[var(--color-text)] mb-1">
          {t('suggestion')}
        </p>
        <p className={cn('text-xs', colors.text)}>
          {t(`suggestion_${level}`)}
        </p>
      </div>
    </div>
  )
}
