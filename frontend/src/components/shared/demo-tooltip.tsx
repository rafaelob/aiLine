'use client'

import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { useDemoStore } from '@/stores/demo-store'

export function DemoTooltip() {
  const t = useTranslations('demo')
  const { isDemoMode, currentStep, nextStep, exitDemo } = useDemoStore()

  if (!isDemoMode || currentStep === 0) return null

  return (
    <AnimatePresence>
      <motion.div
        key={currentStep}
        initial={{ opacity: 0, y: 10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className={cn(
          'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
          'max-w-md w-full mx-4',
          'glass rounded-2xl border border-[var(--color-primary)]/20',
          'shadow-[var(--shadow-xl)] p-5',
        )}
        role="dialog"
        aria-label={t('title')}
      >
        {/* Step indicator dots */}
        <div className="flex items-center gap-1.5 mb-3">
          {[1, 2, 3].map((step) => (
            <div
              key={step}
              className={cn(
                'h-1.5 rounded-full transition-all duration-300',
                step === currentStep
                  ? 'w-6 bg-[var(--color-primary)]'
                  : 'w-1.5 bg-[var(--color-border)]',
                step < currentStep && 'bg-[var(--color-success)]',
              )}
            />
          ))}
          <span className="ml-auto text-xs text-[var(--color-muted)]">
            {currentStep}/3
          </span>
        </div>

        {/* Content */}
        <p className="text-sm font-medium text-[var(--color-text)]">
          {t(`step_${currentStep}`)}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={exitDemo}
            className="text-xs text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors"
          >
            {t('skip')}
          </button>
          <button
            onClick={() => {
              if (currentStep >= 3) exitDemo()
              else nextStep()
            }}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium',
              'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
              'hover:brightness-110 transition-all',
              'btn-shimmer',
            )}
          >
            {currentStep >= 3 ? t('complete') : t('next')}
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
