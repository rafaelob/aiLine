import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { DashboardContent } from '@/components/dashboard/dashboard-content'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('dashboard_title'),
    description: t('dashboard_description'),
  }
}

/**
 * Dashboard page (root for each locale).
 * Server component that renders the dashboard layout.
 */
export default function DashboardPage() {
  return (
    <div className="max-w-5xl mx-auto">
      <DashboardContent />
    </div>
  )
}
