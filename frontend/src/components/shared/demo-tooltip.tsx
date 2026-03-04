'use client'

import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { useDemoStore } from '@/stores/demo-store'

export function DemoTooltip() {
  const t = useTranslations()
  const {
    isDemoMode,
    activeTrack,
    currentStep,
    nextStep,
    prevStep,
    exitDemo,
    getSteps,
    getCurrentStep,
  } = useDemoStore()

  const steps = getSteps()
  const step = getCurrentStep()

  if (!isDemoMode || !step || !activeTrack) return null

  const totalSteps = steps.length
  const isFirst = currentStep === 0
  const isLast = currentStep >= totalSteps - 1
  const trackColor =
    activeTrack === 'teacher'
      ? 'from-blue-500 to-indigo-600'
      : 'from-emerald-500 to-teal-600'
  const trackIcon = activeTrack === 'teacher' ? 'T' : 'A'
  const trackLabel =
    activeTrack === 'teacher' ? t('demo.track_teacher') : t('demo.track_a11y')

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step.id}
        initial={{ opacity: 0, y: 16, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className={cn(
          'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
          'max-w-lg w-full mx-4',
          'glass rounded-2xl border border-[var(--color-primary)]/20',
          'shadow-[var(--shadow-xl)] p-5',
        )}
        role="dialog"
        aria-label={t(step.title)}
        aria-describedby="demo-step-desc"
      >
        {/* Track badge + step indicator */}
        <div className="flex items-center gap-2 mb-3">
          <span
            className={cn(
              'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full',
              'text-[11px] font-bold uppercase tracking-wider text-white',
              'bg-gradient-to-r',
              trackColor,
            )}
          >
            {trackIcon} {trackLabel}
          </span>

          {/* Step dots */}
          <div className="flex items-center gap-1 ml-auto">
            {steps.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => useDemoStore.getState().goToStep(idx)}
                className={cn(
                  'h-1.5 rounded-full transition-all duration-300',
                  idx === currentStep
                    ? 'w-5 bg-[var(--color-primary)]'
                    : idx < currentStep
                      ? 'w-1.5 bg-[var(--color-success)]'
                      : 'w-1.5 bg-[var(--color-border)]',
                )}
                aria-label={`Step ${idx + 1} of ${totalSteps}`}
                aria-current={idx === currentStep ? 'step' : undefined}
              />
            ))}
            <span className="ml-2 text-xs text-[var(--color-muted)] tabular-nums">
              {currentStep + 1}/{totalSteps}
            </span>
          </div>
        </div>

        {/* Content */}
        <h4 className="text-sm font-bold text-[var(--color-text)] mb-1">
          {t(step.title)}
        </h4>
        <p
          id="demo-step-desc"
          className="text-xs text-[var(--color-muted)] leading-relaxed"
        >
          {t(step.description)}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-between mt-4">
          <button
            type="button"
            onClick={exitDemo}
            className={cn(
              'text-xs text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors',
              'rounded-[var(--radius-sm)] px-2 py-1',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
            )}
          >
            {t('demo.skip')}
          </button>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                type="button"
                onClick={prevStep}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-medium',
                  'border border-[var(--color-border)] text-[var(--color-text)]',
                  'hover:bg-[var(--color-surface-elevated)] transition-colors',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
                )}
              >
                {t('demo.prev')}
              </button>
            )}
            <button
              type="button"
              onClick={nextStep}
              className={cn(
                'px-4 py-1.5 rounded-lg text-xs font-medium',
                'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                'hover:brightness-110 transition-all btn-press',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
              )}
            >
              {isLast ? t('demo.complete') : t('demo.next')}
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
