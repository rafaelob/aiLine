'use client'

import { lazy, Suspense } from 'react'
import { useTranslations } from 'next-intl'
import { SkeletonCardGrid } from '@/components/ui/skeleton'
import { PageTransition } from '@/components/ui/page-transition'

const ObservabilityDashboardContent = lazy(() => import('@/components/observability/observability-dashboard'))
const DegradationPanel = lazy(() => import('@/components/resilience/degradation-panel').then(m => ({ default: m.DegradationPanel })))

export default function ObservabilityPage() {
  const t = useTranslations('observability')

  return (
    <PageTransition stagger>
      <main className="flex flex-col gap-6 p-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            {t('title')}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">
            {t('description')}
          </p>
        </div>
        <Suspense fallback={<SkeletonCardGrid count={6} />}>
          <ObservabilityDashboardContent />
        </Suspense>
        <hr className="border-[var(--color-border)]" />
        <Suspense fallback={<SkeletonCardGrid count={3} />}>
          <DegradationPanel />
        </Suspense>
      </main>
    </PageTransition>
  )
}
