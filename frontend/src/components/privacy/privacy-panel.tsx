'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

interface DataSummary {
  plans: number
  sessions: number
  materials: number
  last_updated: string
}

/**
 * Privacy & data management panel.
 * Shows stored data summary, retention policies, and export/delete actions.
 */
export function PrivacyPanel() {
  const t = useTranslations('privacy')
  const [summary, setSummary] = useState<DataSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionState, setActionState] = useState<'idle' | 'exporting' | 'deleting' | 'confirm_delete'>('idle')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  useEffect(() => {
    async function fetchSummary() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/privacy/data-summary`)
        if (res.ok) {
          const data: DataSummary = await res.json()
          setSummary(data)
        }
      } catch {
        // Privacy panel degrades gracefully if API is unreachable
      } finally {
        setLoading(false)
      }
    }
    fetchSummary()
  }, [API_BASE])

  const handleExport = useCallback(async () => {
    setActionState('exporting')
    try {
      await fetch(`${API_BASE}/api/v1/privacy/export`, { method: 'POST' })
    } catch {
      // Demo mode: export simulated
    } finally {
      setActionState('idle')
    }
  }, [API_BASE])

  const handleDelete = useCallback(async () => {
    if (actionState !== 'confirm_delete') {
      setActionState('confirm_delete')
      return
    }
    setActionState('deleting')
    try {
      await fetch(`${API_BASE}/api/v1/privacy/delete`, { method: 'DELETE' })
      setSummary({ plans: 0, sessions: 0, materials: 0, last_updated: new Date().toISOString() })
    } catch {
      // Demo mode: delete simulated
    } finally {
      setActionState('idle')
    }
  }, [actionState, API_BASE])

  const retentionPolicies = [
    t('retention_plans'),
    t('retention_sessions'),
    t('retention_materials'),
    t('retention_logs'),
  ]

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--color-text)] mb-1">
          {t('title')}
        </h3>
        <p className="text-xs text-[var(--color-muted)]">{t('description')}</p>
      </div>

      {/* Data summary */}
      <section aria-labelledby="data-summary-heading">
        <h4
          id="data-summary-heading"
          className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-3"
        >
          {t('data_summary')}
        </h4>

        {loading ? (
          <div className="space-y-2" aria-busy="true">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="h-5 animate-pulse rounded bg-[var(--color-border)]" />
            ))}
          </div>
        ) : summary ? (
          <div className="grid grid-cols-3 gap-3">
            <SummaryCard label={t('plans_stored')} value={summary.plans} />
            <SummaryCard label={t('sessions_stored')} value={summary.sessions} />
            <SummaryCard label={t('materials_stored')} value={summary.materials} />
          </div>
        ) : (
          <p className="text-xs text-[var(--color-muted)]">--</p>
        )}
      </section>

      {/* Retention policies */}
      <section aria-labelledby="retention-heading">
        <h4
          id="retention-heading"
          className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-3"
        >
          {t('retention')}
        </h4>
        <ul className="space-y-1.5">
          {retentionPolicies.map((policy) => (
            <li
              key={policy}
              className="flex items-center gap-2 text-xs text-[var(--color-text)]"
            >
              <span
                className="w-1.5 h-1.5 rounded-full bg-[var(--color-muted)] shrink-0"
                aria-hidden="true"
              />
              {policy}
            </li>
          ))}
        </ul>
      </section>

      {/* Actions */}
      <section aria-labelledby="actions-heading">
        <h4
          id="actions-heading"
          className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-3"
        >
          {t('actions')}
        </h4>
        <div className="space-y-3">
          <div
            className={cn(
              'flex items-center justify-between p-3',
              'rounded-[var(--radius-md)] border border-[var(--color-border)]'
            )}
          >
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">
                {t('export_data')}
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {t('export_description')}
              </p>
            </div>
            <button
              type="button"
              onClick={handleExport}
              disabled={actionState === 'exporting'}
              className={cn(
                'px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium',
                'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                'hover:bg-[var(--color-primary-hover)] transition-colors',
                'disabled:opacity-50'
              )}
            >
              {actionState === 'exporting' ? t('exporting') : t('export_data')}
            </button>
          </div>

          <div
            className={cn(
              'flex items-center justify-between p-3',
              'rounded-[var(--radius-md)] border',
              actionState === 'confirm_delete'
                ? 'border-[var(--color-error)]/50 bg-[var(--color-error)]/5'
                : 'border-[var(--color-border)]'
            )}
          >
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">
                {t('delete_data')}
              </p>
              <p className="text-xs text-[var(--color-muted)]">
                {actionState === 'confirm_delete'
                  ? t('delete_confirm')
                  : t('delete_description')}
              </p>
            </div>
            <button
              type="button"
              onClick={handleDelete}
              disabled={actionState === 'deleting'}
              className={cn(
                'px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium',
                'transition-colors disabled:opacity-50',
                actionState === 'confirm_delete'
                  ? 'bg-[var(--color-error)] text-white hover:bg-[var(--color-error)]/80'
                  : 'bg-[var(--color-error)]/10 text-[var(--color-error)] hover:bg-[var(--color-error)]/20'
              )}
            >
              {actionState === 'deleting' ? t('deleting') : t('delete_data')}
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div
      className={cn(
        'rounded-[var(--radius-md)] border border-[var(--color-border)]',
        'bg-[var(--color-surface)] p-3 text-center'
      )}
    >
      <p className="text-lg font-bold font-mono text-[var(--color-text)]">
        {value}
      </p>
      <p className="text-[10px] text-[var(--color-muted)] mt-0.5">{label}</p>
    </div>
  )
}
