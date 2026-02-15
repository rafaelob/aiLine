'use client'

import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { StageCard } from './stage-card'
import type { StageInfo } from '@/types/pipeline'

interface PipelineViewerProps {
  stages: StageInfo[]
  isRunning: boolean
  error: string | null
}

/**
 * Glass Box pipeline viewer (ADR-022).
 * Animated stepper showing real-time pipeline progress.
 * Stages: Planning -> Validation -> Refinement -> Execution -> Done
 */
export function PipelineViewer({ stages, isRunning, error }: PipelineViewerProps) {
  const t = useTranslations('pipeline')

  return (
    <section
      aria-label={t('title')}
      className={cn(
        'glass rounded-2xl p-6 shadow-[var(--shadow-lg)]',
        'gradient-border-glass'
      )}
    >
      {/* Header */}
      <motion.div
        className="flex items-center gap-3 mb-6"
        variants={itemVariants}
        initial="hidden"
        animate="visible"
      >
        <div
          className={cn(
            'relative flex items-center gap-2 px-3 py-1.5',
            'rounded-full text-xs font-semibold',
            isRunning
              ? 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
              : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
          )}
        >
          {isRunning && (
            <>
              <div
                className="aurora-thinking absolute inset-0 rounded-full"
                style={{ filter: 'blur(8px)', opacity: 0.3 }}
                aria-hidden="true"
              />
              <motion.span
                className="relative inline-block w-2 h-2 rounded-full bg-current"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.2, repeat: Infinity }}
                aria-hidden="true"
              />
            </>
          )}
          <span className="relative">{t('glass_box')}</span>
        </div>
        <h2
          className={cn(
            'text-base font-bold',
            isRunning
              ? 'gradient-text-animated'
              : 'text-[var(--color-text)]'
          )}
        >
          {t('title')}
        </h2>
      </motion.div>

      {/* SR-only live region for pipeline progress */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {stages.filter((s) => s.status === 'active').map((s) => (
          <span key={s.id}>{t(`stages.${s.id}`)}: {t('status.active')}</span>
        ))}
        {!isRunning && stages.length > 0 && stages.every((s) => s.status === 'completed') && (
          <span>{t('status.completed')}</span>
        )}
      </div>

      {/* Stage stepper */}
      <motion.div
        role="list"
        aria-label={t('title')}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {stages.map((stage, i) => (
          <StageCard
            key={stage.id}
            stage={stage}
            index={i}
            isLast={i === stages.length - 1}
          />
        ))}
      </motion.div>

      {/* Error display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            role="alert"
            className={cn(
              'mt-4 glass rounded-[var(--radius-md)] p-4',
              'border border-[var(--color-error)]/30',
              'text-sm text-[var(--color-error)]',
              'shadow-[0_0_12px_color-mix(in_srgb,var(--color-error)_20%,transparent)]'
            )}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}
