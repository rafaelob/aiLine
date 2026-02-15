'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

export interface ScorecardData {
  reading_level_before: number
  reading_level_after: number
  standards_aligned: Array<{ code: string; description: string }>
  accessibility_adaptations: string[]
  rag_groundedness: number
  quality_score: number
  quality_decision: string
  model_used: string
  router_rationale: string
  time_saved_estimate: string
  total_pipeline_time_ms: number
  export_variants_count: number
}

interface TransformationScorecardProps {
  scorecard: ScorecardData
  className?: string
}

export function TransformationScorecard({
  scorecard,
  className,
}: TransformationScorecardProps) {
  const t = useTranslations('scorecard')

  const qualityColor =
    scorecard.quality_score >= 80
      ? 'var(--color-success)'
      : scorecard.quality_score >= 60
        ? 'var(--color-warning)'
        : 'var(--color-error)'

  const ragPct = Math.round(scorecard.rag_groundedness * 100)
  const ragColor =
    ragPct >= 70
      ? 'var(--color-success)'
      : ragPct >= 40
        ? 'var(--color-warning)'
        : 'var(--color-error)'

  const pipelineSeconds = (scorecard.total_pipeline_time_ms / 1000).toFixed(1)

  const metrics = buildMetrics(t, scorecard, {
    qualityColor,
    ragPct,
    ragColor,
    pipelineSeconds,
  })

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      aria-label={t('title')}
      className={cn(
        'rounded-[var(--radius-lg)] border-2 border-[var(--color-primary)]/20',
        'bg-[var(--color-surface)] overflow-hidden',
        className
      )}
    >
      <ScorecardHeader title={t('title')} />

      <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {metrics.map((metric, i) => (
          <motion.div
            key={metric.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.08, duration: 0.3 }}
            className={cn(
              'space-y-2',
              metric.span === 2 && 'sm:col-span-2 lg:col-span-2'
            )}
          >
            <p className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wider">
              {metric.label}
            </p>
            <div>{metric.value}</div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}

/* ===== Metric builder ===== */

interface MetricColors {
  qualityColor: string
  ragPct: number
  ragColor: string
  pipelineSeconds: string
}

function buildMetrics(
  t: ReturnType<typeof useTranslations>,
  s: ScorecardData,
  c: MetricColors
) {
  return [
    {
      key: 'quality',
      label: t('quality_score'),
      value: (
        <div className="flex items-center gap-2">
          <span
            className="text-2xl font-bold"
            style={{ color: c.qualityColor }}
          >
            {s.quality_score}
          </span>
          <span className="text-xs text-[var(--color-muted)]">/100</span>
          <Badge text={s.quality_decision} color={c.qualityColor} />
        </div>
      ),
    },
    {
      key: 'time_saved',
      label: t('time_saved'),
      value: (
        <span className="text-lg font-bold text-[var(--color-success)]">
          {s.time_saved_estimate}
        </span>
      ),
    },
    {
      key: 'reading_level',
      label: t('reading_level'),
      value: (
        <div className="flex items-center gap-3">
          <div className="text-center">
            <p className="text-xs text-[var(--color-muted)]">{t('before')}</p>
            <p className="text-lg font-bold text-[var(--color-text)]">
              {s.reading_level_before}
            </p>
          </div>
          <ArrowRight />
          <div className="text-center">
            <p className="text-xs text-[var(--color-muted)]">{t('after')}</p>
            <p className="text-lg font-bold text-[var(--color-success)]">
              {s.reading_level_after}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: 'rag',
      label: t('rag_groundedness'),
      value: (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 rounded-full bg-[var(--color-surface-elevated)] overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${c.ragPct}%` }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="h-full rounded-full"
              style={{ backgroundColor: c.ragColor }}
            />
          </div>
          <span className="text-sm font-bold" style={{ color: c.ragColor }}>
            {c.ragPct}%
          </span>
        </div>
      ),
    },
    {
      key: 'standards',
      label: t('standards_aligned'),
      value: (
        <div className="flex flex-wrap gap-1.5">
          {s.standards_aligned.length > 0 ? (
            s.standards_aligned.map((std) => (
              <span
                key={std.code}
                className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                title={std.description}
              >
                {std.code}
              </span>
            ))
          ) : (
            <span className="text-xs text-[var(--color-muted)]">-</span>
          )}
        </div>
      ),
      span: 2,
    },
    {
      key: 'accessibility',
      label: t('accessibility'),
      value: (
        <div className="flex flex-wrap gap-1.5">
          {s.accessibility_adaptations.length > 0 ? (
            s.accessibility_adaptations.map((a) => (
              <span
                key={a}
                className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-success)]/10 text-[var(--color-success)]"
              >
                {a}
              </span>
            ))
          ) : (
            <span className="text-xs text-[var(--color-muted)]">-</span>
          )}
        </div>
      ),
      span: 2,
    },
    {
      key: 'model',
      label: t('model_used'),
      value: (
        <div>
          <p className="text-sm font-medium text-[var(--color-text)]">
            {s.model_used || 'Auto'}
          </p>
          {s.router_rationale && (
            <p className="text-[10px] text-[var(--color-muted)] mt-0.5">
              {s.router_rationale}
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'pipeline_time',
      label: t('pipeline_time'),
      value: (
        <span className="text-lg font-bold text-[var(--color-text)]">
          {c.pipelineSeconds}s
        </span>
      ),
    },
    {
      key: 'exports',
      label: t('export_variants'),
      value: (
        <span className="text-lg font-bold text-[var(--color-primary)]">
          {s.export_variants_count}
        </span>
      ),
    },
  ]
}

/* ===== Sub-components ===== */

function ScorecardHeader({ title }: { title: string }) {
  return (
    <div
      className={cn(
        'px-6 py-4 border-b border-[var(--color-border)]',
        'bg-gradient-to-r from-[var(--color-primary)]/5 to-transparent'
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-primary)]/10">
          <ScorecardIcon />
        </div>
        <div>
          <h2 className="text-base font-bold text-[var(--color-text)]">
            {title}
          </h2>
          <p className="text-[10px] text-[var(--color-muted)]">
            Powered by Claude Opus 4.6
          </p>
        </div>
      </div>
    </div>
  )
}

function Badge({ text, color }: { text: string; color: string }) {
  return (
    <span
      className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
        color,
      }}
    >
      {text}
    </span>
  )
}

function ArrowRight() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="var(--color-muted)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M3 8h10M9 4l4 4-4 4" />
    </svg>
  )
}

function ScorecardIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="var(--color-primary)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M4 8l2.5 2.5L12 5" />
    </svg>
  )
}
