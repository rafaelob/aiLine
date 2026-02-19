'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { STEP_KEYS, TOTAL_STEPS } from './setup-types'

interface SetupStepIndicatorProps {
  currentStep: number
}

/**
 * Horizontal step indicator showing numbered circles with labels.
 * Highlights completed, current, and upcoming steps.
 */
export function SetupStepIndicator({ currentStep }: SetupStepIndicatorProps) {
  const t = useTranslations('setup')

  return (
    <nav aria-label="Setup progress" className="mb-8">
      {/* Mobile: compact step counter */}
      <p className="text-center text-sm text-[var(--color-muted)] md:hidden mb-4">
        {currentStep + 1} {t('of')} {TOTAL_STEPS}
        {' — '}
        {t(STEP_KEYS[currentStep])}
      </p>

      {/* Desktop: full step indicator */}
      <ol className="hidden md:flex items-center justify-between" role="list">
        {STEP_KEYS.map((key, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          const isUpcoming = index > currentStep

          return (
            <li
              key={key}
              className="flex flex-col items-center relative flex-1"
              aria-current={isCurrent ? 'step' : undefined}
            >
              {/* Connector line */}
              {index > 0 && (
                <div
                  className={cn(
                    'absolute top-4 right-1/2 w-full h-0.5 -translate-y-1/2',
                    isCompleted || isCurrent
                      ? 'bg-[var(--color-primary)]'
                      : 'bg-[var(--color-border)]'
                  )}
                  style={{ zIndex: 0 }}
                  aria-hidden="true"
                />
              )}

              {/* Step circle */}
              <div
                className={cn(
                  'relative z-10 flex items-center justify-center w-8 h-8 rounded-full',
                  'text-xs font-semibold transition-colors',
                  isCompleted && 'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                  isCurrent && 'bg-[var(--color-primary)] text-[var(--color-on-primary)] ring-4 ring-[var(--color-primary)]/20',
                  isUpcoming && 'bg-[var(--color-surface-elevated)] text-[var(--color-muted)] border border-[var(--color-border)]'
                )}
              >
                {isCompleted ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>

              {/* Step label */}
              <span
                className={cn(
                  'mt-2 text-xs whitespace-nowrap',
                  isCurrent ? 'text-[var(--color-text)] font-semibold' : 'text-[var(--color-muted)]'
                )}
              >
                {t(key)}
              </span>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
