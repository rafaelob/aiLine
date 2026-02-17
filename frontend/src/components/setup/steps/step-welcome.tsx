'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

interface StepWelcomeProps {
  language: string
  onLanguageChange: (lang: string) => void
}

const LANGUAGES = [
  { code: 'en', label: 'English', flag: 'EN' },
  { code: 'pt-BR', label: 'Portugues (Brasil)', flag: 'BR' },
  { code: 'es', label: 'Espanol', flag: 'ES' },
] as const

/**
 * Welcome step: intro text and language selection.
 */
export function StepWelcome({ language, onLanguageChange }: StepWelcomeProps) {
  const t = useTranslations('setup')

  return (
    <div className="space-y-8">
      {/* Logo + title */}
      <div className="text-center">
        <div
          className="mx-auto mb-6 w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-[var(--color-on-primary)]"
          style={{ background: 'var(--gradient-hero)' }}
          aria-hidden="true"
        >
          A
        </div>
        <h2 className="text-2xl font-bold text-[var(--color-text)]">
          {t('welcome_title')}
        </h2>
        <p className="mt-3 text-[var(--color-muted)] max-w-md mx-auto leading-relaxed">
          {t('welcome_desc')}
        </p>
      </div>

      {/* Language picker */}
      <fieldset>
        <legend className="text-sm font-medium text-[var(--color-text)] mb-3">
          {t('select_language')}
        </legend>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" role="radiogroup">
          {LANGUAGES.map((lang) => {
            const isSelected = language === lang.code
            return (
              <button
                key={lang.code}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => onLanguageChange(lang.code)}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)]',
                  'border transition-all text-left',
                  'focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50',
                  isSelected
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5 shadow-sm'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-muted)]'
                )}
              >
                <span
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0',
                    isSelected
                      ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                      : 'bg-[var(--color-surface-elevated)] text-[var(--color-muted)]'
                  )}
                  aria-hidden="true"
                >
                  {lang.flag}
                </span>
                <span className={cn(
                  'text-sm font-medium',
                  isSelected ? 'text-[var(--color-primary)]' : 'text-[var(--color-text)]'
                )}>
                  {lang.label}
                </span>
                {isSelected && (
                  <svg className="ml-auto shrink-0 text-[var(--color-primary)]" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
      </fieldset>
    </div>
  )
}
