import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { PlanGenerationFlow } from '@/components/plan/plan-generation-flow'
import { PendingReviewsBadge } from '@/components/plan/pending-reviews-badge'
import { PageTransition } from '@/components/ui/page-transition'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('plans_title'),
    description: t('plans_description'),
  }
}

/**
 * Plans page -- create and view study plans.
 * Server component shell; interactive logic in client component.
 */
export default async function PlansPage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'plans' })

  return (
    <PageTransition stagger>
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--color-text)]">
              {t('title')}
            </h1>
          </div>
          <PendingReviewsBadge />
        </header>

        <PlanGenerationFlow />
      </div>
    </PageTransition>
  )
}
