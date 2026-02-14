'use client'

import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
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
        'rounded-[var(--radius-lg)] border p-6',
        'bg-[var(--color-surface)] border-[var(--color-border)]'
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1.5',
            'rounded-full text-xs font-semibold',
            isRunning
              ? 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
              : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
          )}
        >
          {isRunning && (
            <motion.span
              className="inline-block w-2 h-2 rounded-full bg-current"
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
              aria-hidden="true"
            />
          )}
          {t('glass_box')}
        </div>
        <h2 className="text-base font-bold text-[var(--color-text)]">
          {t('title')}
        </h2>
      </div>

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
      <div role="list" aria-label={t('title')}>
        {stages.map((stage, i) => (
          <StageCard
            key={stage.id}
            stage={stage}
            index={i}
            isLast={i === stages.length - 1}
          />
        ))}
      </div>

      {/* Error display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            role="alert"
            className={cn(
              'mt-4 rounded-[var(--radius-md)] p-4',
              'bg-[var(--color-error)]/10 border border-[var(--color-error)]/30',
              'text-sm text-[var(--color-error)]'
            )}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}
