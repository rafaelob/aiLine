import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'
import { PageTransition } from '@/components/ui/page-transition'
import { SettingsContent } from './settings-content'

interface PageProps {
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('settings_title'),
    description: t('settings_description'),
  }
}

export default async function SettingsPage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'settings' })
  return (
    <PageTransition stagger>
      <div className="max-w-3xl mx-auto space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">{t('title')}</h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('description')}</p>
        </header>
        <SettingsContent />
      </div>
    </PageTransition>
  )
}
