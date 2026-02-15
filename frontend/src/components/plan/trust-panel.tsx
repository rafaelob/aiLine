'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import type { QualityReport } from '@/types/plan'
import type { ScorecardData } from './transformation-scorecard'

interface TrustPanelProps {
  qualityReport: QualityReport | null
  score: number | null
  scorecard: ScorecardData | null
  plan: { id?: string; title?: string }
}

export function TrustPanel({ qualityReport, score, scorecard }: TrustPanelProps) {
  const t = useTranslations('trust')

  if (!qualityReport && !scorecard && score === null) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <ShieldIcon className="mx-auto mb-3 text-[var(--color-muted)]" />
        <p className="text-sm text-[var(--color-muted)]">{t('no_data')}</p>
      </div>
    )
  }

  const displayScore = score ?? qualityReport?.score ?? scorecard?.quality_score ?? null
  const decision = qualityReport?.decision

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-4"
    >
      {/* Quality Score Hero */}
      <motion.div variants={itemVariants} className="glass card-hover rounded-xl p-5">
        <div className="flex items-center gap-3 mb-3">
          <div
            className="icon-orb w-10 h-10 flex items-center justify-center rounded-full"
            style={{ background: 'linear-gradient(135deg, var(--color-success), var(--color-primary))' }}
          >
            <ShieldIcon className="text-white w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('quality_section')}</h3>
        </div>
        <div className="flex items-center gap-4">
          {displayScore !== null && (
            <div className="text-3xl font-bold text-[var(--color-text)]">
              {displayScore}<span className="text-lg text-[var(--color-muted)]">/100</span>
            </div>
          )}
          {decision && (
            <span className={cn(
              'px-3 py-1 rounded-full text-xs font-semibold glass',
              decision === 'accept' && 'text-[var(--color-success)]',
              decision === 'refine' && 'text-[var(--color-warning)]',
              decision === 'must-refine' && 'text-[var(--color-error)]',
            )}>
              {decision === 'accept' ? 'Accepted' : decision === 'must-refine' ? 'Must Refine' : 'Refine if Budget'}
            </span>
          )}
        </div>
        {qualityReport?.structural_checks && qualityReport.structural_checks.length > 0 && (
          <div className="mt-3 space-y-1">
            {qualityReport.structural_checks.map((check, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className={check.passed ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'}>
                  {check.passed ? '\u2713' : '\u2717'}
                </span>
                <span className="text-[var(--color-text)]">{check.name}</span>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Scorecard Metrics */}
      {scorecard && (
        <motion.div variants={itemVariants} className="glass card-hover rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="icon-orb w-10 h-10 flex items-center justify-center rounded-full"
              style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
            >
              <MetricsIcon className="text-white w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('standards_section')}</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {scorecard.standards_aligned.length > 0 && (
              <MetricCard label={t('standards_count')} value={`${scorecard.standards_aligned.length}`} />
            )}
            {scorecard.accessibility_adaptations.length > 0 && (
              <MetricCard label={t('adaptations_count')} value={`${scorecard.accessibility_adaptations.length}`} />
            )}
            {scorecard.reading_level_before != null && scorecard.reading_level_after != null && (
              <MetricCard label={t('reading_level')} value={`${scorecard.reading_level_before} \u2192 ${scorecard.reading_level_after}`} />
            )}
            {scorecard.rag_groundedness != null && (
              <MetricCard label={t('rag_groundedness')} value={`${Math.round(scorecard.rag_groundedness * 100)}%`} />
            )}
            {scorecard.export_variants_count != null && (
              <MetricCard label={t('export_variants')} value={`${scorecard.export_variants_count}`} />
            )}
            {scorecard.total_pipeline_time_ms != null && (
              <MetricCard label={t('pipeline_time')} value={`${(scorecard.total_pipeline_time_ms / 1000).toFixed(1)}s`} />
            )}
          </div>
        </motion.div>
      )}

      {/* AI Reasoning */}
      {scorecard?.model_used && (
        <motion.div variants={itemVariants} className="glass card-hover rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="icon-orb w-10 h-10 flex items-center justify-center rounded-full"
              style={{ background: 'linear-gradient(135deg, var(--color-warning), var(--color-primary))' }}
            >
              <BrainIcon className="text-white w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-[var(--color-text)]">{t('reasoning_section')}</h3>
          </div>
          <p className="text-sm text-[var(--color-text)]">
            {t('model_chosen', { model: scorecard.model_used })}
          </p>
        </motion.div>
      )}

      {/* Suggestions */}
      {qualityReport?.suggestions && qualityReport.suggestions.length > 0 && (
        <motion.div variants={itemVariants} className="glass card-hover rounded-xl p-5">
          <h3 className="text-sm font-semibold text-[var(--color-text)] mb-2">{t('suggestions')}</h3>
          <ul className="space-y-1">
            {qualityReport.suggestions.map((s, i) => (
              <li key={i} className="text-xs text-[var(--color-muted)] flex items-start gap-2">
                <span className="text-[var(--color-primary)] mt-0.5">{'\u2192'}</span> {s}
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </motion.div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass rounded-lg p-3">
      <p className="text-xs text-[var(--color-muted)]">{label}</p>
      <p className="text-sm font-semibold text-[var(--color-text)] mt-0.5">{value}</p>
    </div>
  )
}

function ShieldIcon({ className }: { className?: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  )
}

function MetricsIcon({ className }: { className?: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d="M12 20V10M18 20V4M6 20v-4" />
    </svg>
  )
}

function BrainIcon({ className }: { className?: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44A2.5 2.5 0 0 1 2.5 17A2.5 2.5 0 0 1 4 12.5A2.5 2.5 0 0 1 2.5 10A2.5 2.5 0 0 1 5.5 7h.5" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44A2.5 2.5 0 0 0 21.5 17a2.5 2.5 0 0 0-1.5-4.5A2.5 2.5 0 0 0 21.5 10a2.5 2.5 0 0 0-3-2.5h-.5" />
    </svg>
  )
}
