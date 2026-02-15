import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { PageTransition } from '@/components/ui/page-transition'
import { TutorPageContent } from './tutor-page-content'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('tutors_title'),
    description: t('tutors_description'),
  }
}

/**
 * Tutors page -- AI tutor chat interface with voice input and conversation review.
 * Server component shell; interactive logic in client components.
 */
export default async function TutorsPage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'tutor' })

  return (
    <PageTransition stagger>
      <div className="max-w-4xl mx-auto space-y-4">
        <header>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            {t('title')}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">
            {t('subtitle')}
          </p>
        </header>

        <TutorPageContent />
      </div>
    </PageTransition>
  )
}
