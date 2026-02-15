'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
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
      <div
        className="flex flex-col items-center justify-center py-12 gap-4 rounded-xl glass border border-dashed border-[var(--color-border)]"
        role="status"
      >
        <svg width="80" height="60" viewBox="0 0 80 60" fill="none" aria-hidden="true">
          <rect x="20" y="5" width="40" height="50" rx="6" fill="var(--color-bg)" stroke="var(--color-primary)" strokeWidth="1.5" />
          <line x1="30" y1="20" x2="50" y2="20" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
          <line x1="30" y1="30" x2="50" y2="30" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
          <line x1="30" y1="40" x2="42" y2="40" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        </svg>
        <p className="text-sm font-medium text-[var(--color-text)]">{t('no_report')}</p>
      </div>
    )
  }

  const displayScore = score ?? report?.score ?? 0

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Score gauge */}
      <motion.div variants={itemVariants} className="glass rounded-2xl p-6">
        <div className="flex flex-col items-center">
          <ScoreGauge score={displayScore} />
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {displayScore} {t('out_of')}
          </p>
          {report?.decision && (
            <span
              className={cn(
                'mt-3 px-4 py-1.5 rounded-full text-sm font-semibold glass',
                report.decision === 'accept' && 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
                report.decision === 'refine' && 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
                report.decision === 'must-refine' && 'bg-[var(--color-error)]/15 text-[var(--color-error)]'
              )}
            >
              {t(`decision.${report.decision}`)}
            </span>
          )}
        </div>
      </motion.div>

      {/* Structural checks */}
      {report?.structural_checks && report.structural_checks.length > 0 && (
        <motion.div variants={itemVariants}>
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
                    'flex items-start gap-3 p-3 glass card-hover rounded-xl',
                    'border-l-4',
                    check.passed
                      ? 'border-l-[var(--color-success)]'
                      : 'border-l-[var(--color-error)]'
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
        </motion.div>
      )}

      {/* Suggestions */}
      {report?.suggestions && report.suggestions.length > 0 && (
        <motion.div variants={itemVariants}>
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
                    'glass card-hover rounded-xl',
                    'flex items-start gap-3'
                  )}
                >
                  <span
                    className="icon-orb shrink-0 flex items-center justify-center w-6 h-6"
                    style={{ background: 'var(--color-warning)' }}
                    aria-hidden="true"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M9 18h6M10 22h4M12 2a7 7 0 0 1 4 12.7V17a1 1 0 0 1-1 1h-6a1 1 0 0 1-1-1v-2.3A7 7 0 0 1 12 2z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                  {suggestion}
                </li>
              ))}
            </ul>
          </section>
        </motion.div>
      )}
    </motion.div>
  )
}
