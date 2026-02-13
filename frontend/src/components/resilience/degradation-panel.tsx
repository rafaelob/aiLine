'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

type FailureType = 'redis' | 'llm'

interface DegradationState {
  redis: boolean
  llm: boolean
}

/**
 * Chaos-lite degradation panel for demo mode.
 * Simulates Redis down / LLM timeout via API calls,
 * showing a "Degraded Mode" banner when active.
 */
export function DegradationPanel() {
  const t = useTranslations('degradation')
  const [failures, setFailures] = useState<DegradationState>({
    redis: false,
    llm: false,
  })

  const isDegraded = failures.redis || failures.llm
  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  const toggleFailure = useCallback(
    async (type: FailureType) => {
      const newState = !failures[type]
      setFailures((prev) => ({ ...prev, [type]: newState }))

      try {
        await fetch(`${API_BASE}/api/v1/demo/chaos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ failure: type, active: newState }),
        })
      } catch {
        // Demo mode: failures are simulated locally even if API is unreachable
      }
    },
    [failures, API_BASE]
  )

  const resetAll = useCallback(async () => {
    setFailures({ redis: false, llm: false })
    try {
      await fetch(`${API_BASE}/api/v1/demo/chaos/reset`, { method: 'POST' })
    } catch {
      // Demo mode: reset locally
    }
  }, [API_BASE])

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">
          {t('title')}
        </h3>
        <p className="text-xs text-[var(--color-muted)]">{t('description')}</p>
      </div>

      {/* Status banner */}
      <div
        role="status"
        aria-live="polite"
        className={cn(
          'rounded-[var(--radius-md)] px-4 py-3 text-sm font-medium',
          'flex items-center gap-2',
          isDegraded
            ? 'bg-[var(--color-warning)]/10 text-[var(--color-warning)] border border-[var(--color-warning)]/30'
            : 'bg-[var(--color-success)]/10 text-[var(--color-success)] border border-[var(--color-success)]/30'
        )}
      >
        <span
          className={cn(
            'w-2 h-2 rounded-full shrink-0',
            isDegraded ? 'bg-[var(--color-warning)]' : 'bg-[var(--color-success)]'
          )}
          aria-hidden="true"
        />
        {isDegraded ? t('status_degraded') : t('status_healthy')}
      </div>

      {/* Failure simulation buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => toggleFailure('redis')}
          aria-pressed={failures.redis}
          className={cn(
            'px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
            'transition-colors border',
            failures.redis
              ? 'bg-[var(--color-error)]/10 border-[var(--color-error)]/30 text-[var(--color-error)]'
              : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
          )}
        >
          {t('simulate_redis')}
        </button>

        <button
          type="button"
          onClick={() => toggleFailure('llm')}
          aria-pressed={failures.llm}
          className={cn(
            'px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
            'transition-colors border',
            failures.llm
              ? 'bg-[var(--color-error)]/10 border-[var(--color-error)]/30 text-[var(--color-error)]'
              : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
          )}
        >
          {t('simulate_llm')}
        </button>

        {isDegraded && (
          <button
            type="button"
            onClick={resetAll}
            className={cn(
              'px-4 py-2.5 rounded-[var(--radius-md)] text-sm font-medium',
              'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
              'hover:bg-[var(--color-primary-hover)] transition-colors'
            )}
          >
            {t('reset')}
          </button>
        )}
      </div>

      {/* Active failure descriptions */}
      {isDegraded && (
        <ul
          className="space-y-2"
          aria-label={t('active_failures')}
        >
          {failures.redis && (
            <li className="flex items-start gap-2 text-xs text-[var(--color-warning)]">
              <WarningIcon />
              <span>{t('redis_down')}</span>
            </li>
          )}
          {failures.llm && (
            <li className="flex items-start gap-2 text-xs text-[var(--color-warning)]">
              <WarningIcon />
              <span>{t('llm_timeout')}</span>
            </li>
          )}
        </ul>
      )}
    </div>
  )
}

function WarningIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0 mt-0.5"
      aria-hidden="true"
    >
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}
