import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

export interface TraceRecord {
  run_id: string
  status: string
  total_time_ms: number
  node_count: number
  final_score: number | null
  model_used: string
  refinement_count: number
}

export function PlanHistoryCard({
  trace,
  localePrefix,
  t,
}: {
  trace: TraceRecord
  localePrefix: string
  t: ReturnType<typeof useTranslations<'dashboard'>>
}) {
  const isCompleted = trace.status === 'completed'
  const timeFormatted = `${(trace.total_time_ms / 1000).toFixed(1)}s`
  const shortId = trace.run_id.slice(0, 8)

  return (
    <a
      href={`${localePrefix}/plans`}
      aria-label={`${t('plan_run')} ${shortId} - ${isCompleted ? t('plan_status_completed') : t('plan_status_failed')}`}
      className="glass card-hover rounded-xl p-4 flex flex-col gap-2 group focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-mono text-[var(--color-muted)] truncate">
          {shortId}
        </span>
        <span
          className={cn(
            'text-[10px] font-semibold px-2 py-0.5 rounded-full',
            isCompleted
              ? 'bg-[color-mix(in_srgb,var(--color-success)_15%,transparent)] text-[var(--color-success)]'
              : 'bg-[color-mix(in_srgb,var(--color-error,#ef4444)_15%,transparent)] text-[var(--color-error,#ef4444)]'
          )}
        >
          {isCompleted ? t('plan_status_completed') : t('plan_status_failed')}
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
        <span className="px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[10px] font-medium truncate max-w-[120px]">
          {trace.model_used}
        </span>
      </div>

      <div className="flex items-center justify-between mt-auto pt-1">
        <span className="text-xs text-[var(--color-muted)]">
          {t('plan_time')}: {timeFormatted}
        </span>
        {trace.final_score !== null && (
          <span className="text-xs font-semibold text-[var(--color-text)]">
            {t('plan_score')}: {trace.final_score}
          </span>
        )}
      </div>
    </a>
  )
}
