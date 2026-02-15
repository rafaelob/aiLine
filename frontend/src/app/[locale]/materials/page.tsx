import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { MaterialsContent } from './materials-content'
import { PageTransition } from '@/components/ui/page-transition'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('materials_title'),
    description: t('materials_description'),
  }
}

/**
 * Materials page -- upload and manage teaching materials.
 * Server component shell; interactive logic in client component.
 */
export default async function MaterialsPage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'materials' })

  return (
    <PageTransition stagger>
      <div className="max-w-5xl mx-auto space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            {t('title')}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">
            {t('upload_desc')}
          </p>
        </header>

        <MaterialsContent />
      </div>
    </PageTransition>
  )
}
