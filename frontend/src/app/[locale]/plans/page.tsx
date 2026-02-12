import { useTranslations } from 'next-intl'
import { PlanGenerationFlow } from '@/components/plan/plan-generation-flow'

/**
 * Plans page -- create and view study plans.
 * Server component shell; interactive logic in client component.
 */
export default function PlansPage() {
  const t = useTranslations('plans')

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">
          {t('title')}
        </h1>
      </header>

      <PlanGenerationFlow />
    </div>
  )
}
