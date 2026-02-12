'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { StageInfo, StageStatus } from '@/types/pipeline'

interface StageCardProps {
  stage: StageInfo
  index: number
  isLast: boolean
}

const STATUS_COLORS: Record<StageStatus, string> = {
  pending: 'bg-[var(--color-border)]',
  active: 'bg-[var(--color-warning)]',
  completed: 'bg-[var(--color-success)]',
  failed: 'bg-[var(--color-error)]',
}

const STATUS_RING: Record<StageStatus, string> = {
  pending: 'ring-[var(--color-border)]',
  active: 'ring-[var(--color-warning)]',
  completed: 'ring-[var(--color-success)]',
  failed: 'ring-[var(--color-error)]',
}

/**
 * Individual stage card for the pipeline stepper.
 * Shows status indicator with animated pulse for active stage.
 */
export function StageCard({ stage, index, isLast }: StageCardProps) {
  const t = useTranslations('pipeline')

  return (
    <div className="flex items-start gap-4" role="listitem">
      {/* Step indicator column */}
      <div className="flex flex-col items-center">
        {/* Circle indicator */}
        <motion.div
          className={cn(
            'relative flex items-center justify-center',
            'w-10 h-10 rounded-full ring-2',
            STATUS_COLORS[stage.status],
            STATUS_RING[stage.status]
          )}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: index * 0.1, type: 'spring', stiffness: 200 }}
          aria-hidden="true"
        >
          {stage.status === 'completed' && <CheckIcon />}
          {stage.status === 'failed' && <XIcon />}
          {stage.status === 'active' && (
            <>
              <LoadingSpinner />
              <motion.div
                className="absolute inset-0 rounded-full ring-2 ring-[var(--color-warning)]"
                animate={{ scale: [1, 1.4], opacity: [0.5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </>
          )}
          {stage.status === 'pending' && (
            <span className="text-xs font-bold text-[var(--color-muted)]">
              {index + 1}
            </span>
          )}
        </motion.div>

        {/* Connector line */}
        {!isLast && (
          <div
            className={cn(
              'w-0.5 flex-1 min-h-[24px]',
              stage.status === 'completed'
                ? 'bg-[var(--color-success)]'
                : 'bg-[var(--color-border)]'
            )}
            aria-hidden="true"
          />
        )}
      </div>

      {/* Content */}
      <motion.div
        className={cn(
          'flex-1 pb-6 pt-1',
          isLast && 'pb-0'
        )}
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1 + 0.05 }}
      >
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-[var(--color-text)]">
            {t(`stages.${stage.id}`)}
          </h3>
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full',
              stage.status === 'active' && 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]',
              stage.status === 'completed' && 'bg-[var(--color-success)]/20 text-[var(--color-success)]',
              stage.status === 'failed' && 'bg-[var(--color-error)]/20 text-[var(--color-error)]',
              stage.status === 'pending' && 'bg-[var(--color-border)] text-[var(--color-muted)]'
            )}
            aria-label={t(`status.${stage.status}`)}
          >
            {t(`status.${stage.status}`)}
          </span>
        </div>

        {/* Progress bar for active stages */}
        {stage.status === 'active' && stage.progress > 0 && (
          <div
            className="mt-2 h-1.5 w-full rounded-full bg-[var(--color-border)]"
            role="progressbar"
            aria-valuenow={stage.progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${t(`stages.${stage.id}`)} ${stage.progress}%`}
          >
            <motion.div
              className="h-full rounded-full bg-[var(--color-warning)]"
              initial={{ width: 0 }}
              animate={{ width: `${stage.progress}%` }}
              transition={{ type: 'spring', stiffness: 100 }}
            />
          </div>
        )}
      </motion.div>
    </div>
  )
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M3.5 8.5L6.5 11.5L12.5 5.5"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function XIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M4 4l8 8M12 4l-8 8" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function LoadingSpinner() {
  return (
    <motion.svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      aria-hidden="true"
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        stroke="white"
        strokeWidth="2"
        strokeDasharray="28 10"
        strokeLinecap="round"
      />
    </motion.svg>
  )
}
