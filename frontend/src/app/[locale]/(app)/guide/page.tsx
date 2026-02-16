import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { InteractiveGuide } from '@/components/guide/interactive-guide'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'guide' })
  return {
    title: t('page_title'),
    description: t('page_subtitle'),
  }
}

/**
 * Interactive guide / manual page separated by roles (Teacher, Student, Parent).
 * Server component inside the (app) route group (sidebar + topbar layout).
 */
export default function GuidePage() {
  return (
    <div className="max-w-4xl mx-auto">
      <InteractiveGuide />
    </div>
  )
}
