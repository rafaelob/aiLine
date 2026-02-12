import { useTranslations } from 'next-intl'
import { TutorChat } from '@/components/tutor/tutor-chat'

/**
 * Tutors page -- AI tutor chat interface with voice input.
 * Server component shell; interactive logic in client components.
 */
export default function TutorsPage() {
  const t = useTranslations('tutor')

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <header>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">
          {t('title')}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">
          {t('subtitle')}
        </p>
      </header>

      <TutorChat />
    </div>
  )
}
