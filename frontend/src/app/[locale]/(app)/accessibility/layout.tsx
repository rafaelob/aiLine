import type { Metadata } from 'next'
import { getTranslations } from 'next-intl/server'

interface LayoutProps {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

export async function generateMetadata({ params }: LayoutProps): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })
  return {
    title: t('accessibility_title'),
    description: t('accessibility_description'),
  }
}

export default function AccessibilityLayout({ children }: LayoutProps) {
  return children
}
