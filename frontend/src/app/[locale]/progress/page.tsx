import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { ProgressDashboard } from '@/components/progress/progress-dashboard'
import { PageTransition } from '@/components/ui/page-transition'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('progress_title'),
    description: t('progress_description'),
  }
}

export default async function ProgressPage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'progress' })

  return (
    <PageTransition stagger>
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            {t('title')}
          </h1>
        </header>
        <ProgressDashboard />
      </div>
    </PageTransition>
  )
}
