'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { ObservabilityDashboard } from '@/types/trace'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

/**
 * Judge Dashboard page content.
 * Shows LLM provider, score breakdown, latency, error rate,
 * circuit breaker state, SSE event counts, and token usage.
 */
export default function ObservabilityDashboardContent() {
  const t = useTranslations('observability')
  const [data, setData] = useState<ObservabilityDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/observability/dashboard`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: ObservabilityDashboard = await res.json()
      setData(json)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
        {Array.from({ length: 6 }, (_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 h-32"
            aria-hidden="true"
          />
        ))}
      </div>
    )
  }

  if (error || !data) {
    return (
      <div
        role="alert"
        className={cn(
          'rounded-[var(--radius-lg)] border border-[var(--color-error)]/30',
          'bg-[var(--color-error)]/10 p-6 text-center'
        )}
      >
        <p className="text-sm text-[var(--color-error)]">
          {t('fetch_error')}: {error ?? 'No data'}
        </p>
        <button
          onClick={fetchData}
          className={cn(
            'mt-3 px-4 py-2 rounded-[var(--radius-md)]',
            'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'text-sm font-medium hover:bg-[var(--color-primary-hover)]',
            'transition-colors'
          )}
        >
          {t('retry')}
        </button>
      </div>
    )
  }

  const cbStateColor =
    data.circuit_breaker_state === 'closed'
      ? 'text-[var(--color-success)] bg-[var(--color-success)]/10'
      : data.circuit_breaker_state === 'open'
        ? 'text-[var(--color-error)] bg-[var(--color-error)]/10'
        : 'text-[var(--color-warning)] bg-[var(--color-warning)]/10'

  const sseEntries = Object.entries(data.sse_event_counts)
  const maxSseCount = Math.max(1, ...sseEntries.map(([, c]) => c))

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {/* Provider card */}
      <StatCard title={t('provider')} className="sm:col-span-2 lg:col-span-1">
        <p className="text-lg font-bold text-[var(--color-text)]">{data.provider}</p>
        <p className="text-sm text-[var(--color-muted)]">{data.model}</p>
        <p className="text-xs text-[var(--color-muted)] mt-2">
          {t('quality_avg')}: <span className="font-mono">{data.scores.quality_avg.toFixed(1)}</span>
        </p>
      </StatCard>

      {/* Latency card */}
      <StatCard title={t('latency')}>
        <div className="flex gap-6">
          <div>
            <p className="text-xs text-[var(--color-muted)]">p50</p>
            <p className="text-lg font-bold font-mono text-[var(--color-text)]">
              {data.scores.latency_p50_ms}ms
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-muted)]">p95</p>
            <p className="text-lg font-bold font-mono text-[var(--color-text)]">
              {data.scores.latency_p95_ms}ms
            </p>
          </div>
        </div>
        {/* Mini latency sparkline */}
        {data.latency_history.length > 0 && (
          <div className="mt-3 flex items-end gap-px h-8" aria-hidden="true">
            {data.latency_history.slice(-20).map((point, i) => {
              const maxP95 = Math.max(1, ...data.latency_history.map((p) => p.p95))
              const height = Math.max(2, (point.p95 / maxP95) * 32)
              return (
                <div
                  key={i}
                  className="flex-1 rounded-t bg-[var(--color-primary)]/40"
                  style={{ height: `${height}px` }}
                />
              )
            })}
          </div>
        )}
      </StatCard>

      {/* Error rate + Circuit breaker */}
      <StatCard title={t('error_rate')}>
        <p className="text-lg font-bold font-mono text-[var(--color-text)]">
          {(data.error_rate * 100).toFixed(1)}%
        </p>
        <div className="mt-2 flex items-center gap-2">
          <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-semibold', cbStateColor)}>
            {t(`cb_${data.circuit_breaker_state}`)}
          </span>
        </div>
      </StatCard>

      {/* SSE event counts */}
      <StatCard title={t('sse_events')} className="sm:col-span-2 lg:col-span-2">
        <div className="space-y-1.5">
          {sseEntries.map(([type, count]) => (
            <div key={type} className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--color-muted)] w-28 shrink-0 truncate font-mono">
                {type}
              </span>
              <div className="flex-1 h-2 rounded-full bg-[var(--color-border)]">
                <div
                  className="h-full rounded-full bg-[var(--color-primary)] transition-all"
                  style={{ width: `${(count / maxSseCount) * 100}%` }}
                />
              </div>
              <span className="text-[10px] font-mono text-[var(--color-muted)] w-8 text-right">
                {count}
              </span>
            </div>
          ))}
        </div>
      </StatCard>

      {/* Token usage */}
      <StatCard title={t('token_usage')}>
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-[var(--color-muted)]">{t('input_tokens')}</span>
            <span className="font-mono text-[var(--color-text)]">
              {new Intl.NumberFormat('en-US').format(data.token_usage.input_tokens)}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[var(--color-muted)]">{t('output_tokens')}</span>
            <span className="font-mono text-[var(--color-text)]">
              {new Intl.NumberFormat('en-US').format(data.token_usage.output_tokens)}
            </span>
          </div>
          <div className="flex justify-between text-xs pt-1 border-t border-[var(--color-border)]">
            <span className="text-[var(--color-muted)]">{t('estimated_cost')}</span>
            <span className="font-mono font-semibold text-[var(--color-text)]">
              ${data.token_usage.estimated_cost_usd.toFixed(4)}
            </span>
          </div>
        </div>
      </StatCard>
    </div>
  )
}

function StatCard({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-5',
        className
      )}
    >
      <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-3">
        {title}
      </h3>
      {children}
    </div>
  )
}
