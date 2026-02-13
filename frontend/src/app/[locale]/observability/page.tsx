import { useTranslations } from 'next-intl'
import { ObservabilityDashboardContent } from '@/components/observability/observability-dashboard'

export default function ObservabilityPage() {
  const t = useTranslations('observability')

  return (
    <main className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">
          {t('title')}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">
          {t('description')}
        </p>
      </div>
      <ObservabilityDashboardContent />
    </main>
  )
}
