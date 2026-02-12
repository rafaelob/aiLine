'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { ScoreGauge } from './score-gauge'
import type { QualityReport } from '@/types/plan'

interface PlanReportProps {
  report: QualityReport | null
  score: number | null
}

/**
 * Quality report view with score gauge, structural checks, and suggestions.
 * Decision mapping per ADR-050: <60 must-refine, 60-79 refine-if-budget, >=80 accept.
 */
export function PlanReport({ report, score }: PlanReportProps) {
  const t = useTranslations('quality')

  if (!report && score === null) {
    return (
      <div className="text-center py-12 text-[var(--color-muted)]" role="status">
        No quality report available yet.
      </div>
    )
  }

  const displayScore = score ?? report?.score ?? 0

  return (
    <div className="space-y-8">
      {/* Score gauge */}
      <div className="flex flex-col items-center">
        <ScoreGauge score={displayScore} />
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          {displayScore} {t('out_of')}
        </p>
        {report?.decision && (
          <span
            className={cn(
              'mt-3 px-4 py-1.5 rounded-full text-sm font-semibold',
              report.decision === 'accept' && 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
              report.decision === 'refine' && 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
              report.decision === 'must-refine' && 'bg-[var(--color-error)]/15 text-[var(--color-error)]'
            )}
          >
            {t(`decision.${report.decision}`)}
          </span>
        )}
      </div>

      {/* Structural checks */}
      {report?.structural_checks && report.structural_checks.length > 0 && (
        <section aria-labelledby="checks-heading">
          <h3
            id="checks-heading"
            className="text-base font-semibold text-[var(--color-text)] mb-4"
          >
            {t('structural_checks')}
          </h3>
          <ul className="space-y-2">
            {report.structural_checks.map((check, i) => (
              <li
                key={i}
                className={cn(
                  'flex items-start gap-3 p-3 rounded-[var(--radius-md)]',
                  check.passed
                    ? 'bg-[var(--color-success)]/5'
                    : 'bg-[var(--color-error)]/5'
                )}
              >
                <span
                  className={cn(
                    'shrink-0 mt-0.5',
                    check.passed ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'
                  )}
                  aria-label={check.passed ? t('passed') : t('failed')}
                >
                  {check.passed ? (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                      <path d="M4 9l3.5 3.5L14 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                      <path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </span>
                <div>
                  <span className="text-sm font-medium text-[var(--color-text)]">
                    {check.name}
                  </span>
                  <p className="text-xs text-[var(--color-muted)] mt-0.5">
                    {check.message}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Suggestions */}
      {report?.suggestions && report.suggestions.length > 0 && (
        <section aria-labelledby="suggestions-heading">
          <h3
            id="suggestions-heading"
            className="text-base font-semibold text-[var(--color-text)] mb-4"
          >
            {t('suggestions')}
          </h3>
          <ul className="space-y-2">
            {report.suggestions.map((suggestion, i) => (
              <li
                key={i}
                className={cn(
                  'text-sm text-[var(--color-text)] p-3',
                  'bg-[var(--color-surface-elevated)] rounded-[var(--radius-md)]',
                  'flex items-start gap-2'
                )}
              >
                <span className="text-[var(--color-warning)] shrink-0" aria-hidden="true">
                  &rarr;
                </span>
                {suggestion}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
