'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { ExportViewer } from '@/components/exports/export-viewer'
import { VisualSchedule } from '@/components/exports/visual-schedule'
import { EXPORT_VARIANTS } from '@/lib/accessibility-data'
import type { ExportVariant } from '@/types/accessibility'
import type { ScheduleStep } from '@/types/exports'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

interface ExportsApiResponse {
  plan_title: string
  exports: Record<string, string>
  schedule_steps: ScheduleStep[]
}

type FetchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: ExportsApiResponse }

/**
 * Exports comparison page.
 * Fetches plan exports from the backend and renders a sidebar layout
 * with export variants, full-screen preview, and visual schedule.
 */
export default function ExportsPage() {
  const searchParams = useSearchParams()
  const planId = searchParams.get('planId')
  const t = useTranslations('exports')
  const tc = useTranslations('common')

  const [isFullScreen, setIsFullScreen] = useState(false)
  const [sidebarVariant, setSidebarVariant] = useState<ExportVariant>('standard')
  const [fetchState, setFetchState] = useState<FetchState>({ status: 'idle' })

  const fetchExports = useCallback(async (id: string) => {
    setFetchState({ status: 'loading' })
    try {
      const response = await fetch(`${API_BASE}/plans/${id}/exports`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data: ExportsApiResponse = await response.json()
      setFetchState({ status: 'success', data })
    } catch (err) {
      const message = err instanceof Error ? err.message : tc('error')
      setFetchState({ status: 'error', message })
    }
  }, [])

  useEffect(() => {
    if (planId) {
      fetchExports(planId)
    }
  }, [planId, fetchExports])

  const isVisualSchedule = sidebarVariant === 'visual_schedule'

  // Derive data from fetch state
  const exports = fetchState.status === 'success' ? fetchState.data.exports : {}
  const scheduleSteps = fetchState.status === 'success' ? fetchState.data.schedule_steps : []
  const planTitle = fetchState.status === 'success' ? fetchState.data.plan_title : ''

  return (
    <main className="flex min-h-screen flex-col gap-6 p-6">
      <header>
        <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text)' }}>
          {t('title')}
        </h1>
        <p className="mt-2" style={{ color: 'var(--color-muted)' }}>
          {t('description')}
        </p>
      </header>

      {/* Loading state */}
      {fetchState.status === 'loading' && (
        <div className="flex flex-1 items-center justify-center" role="status">
          <p style={{ color: 'var(--color-muted)' }}>{tc('loading')}</p>
        </div>
      )}

      {/* Error state */}
      {fetchState.status === 'error' && (
        <div className="flex flex-1 flex-col items-center justify-center gap-4" role="alert">
          <p className="text-red-600">{fetchState.message}</p>
          {planId && (
            <button
              type="button"
              onClick={() => fetchExports(planId)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              {tc('retry')}
            </button>
          )}
        </div>
      )}

      {/* Empty state (no planId) */}
      {fetchState.status === 'idle' && !planId && (
        <div className="flex flex-1 items-center justify-center">
          <p style={{ color: 'var(--color-muted)' }}>{t('no_plan')}</p>
        </div>
      )}

      {/* Success state */}
      {fetchState.status === 'success' && (
        <div className="flex flex-1 gap-6">
          {/* Sidebar: variant list */}
          <aside
            className={cn(
              'w-64 shrink-0 rounded-lg border border-gray-200 p-4 dark:border-gray-700',
              isFullScreen && 'hidden',
            )}
            aria-label={t('variants_aria_label')}
          >
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              {t('variants_heading')}
            </h2>
            <nav>
              <ul className="flex flex-col gap-1" role="list">
                {EXPORT_VARIANTS.map((variant) => {
                  const isActive = sidebarVariant === variant.id
                  const hasContent = !!exports[variant.id]
                  return (
                    <li key={variant.id}>
                      <button
                        onClick={() => setSidebarVariant(variant.id)}
                        disabled={!hasContent}
                        aria-current={isActive ? 'page' : undefined}
                        className={cn(
                          'w-full rounded-lg px-3 py-2 text-left text-sm transition-colors',
                          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600',
                          isActive
                            ? 'bg-blue-50 font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                            : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800',
                          !hasContent && 'cursor-not-allowed opacity-40',
                        )}
                      >
                        <span className="block">{variant.label}</span>
                        <span className="block text-xs text-gray-400">
                          {variant.description}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </nav>
          </aside>

          {/* Main content area */}
          <div className="flex-1">
            {isVisualSchedule ? (
              <VisualSchedule
                planTitle={planTitle}
                steps={scheduleSteps}
              />
            ) : (
              <ExportViewer
                exports={exports}
                fullScreen={isFullScreen}
                onFullScreenToggle={() => setIsFullScreen((prev) => !prev)}
              />
            )}
          </div>
        </div>
      )}
    </main>
  )
}
