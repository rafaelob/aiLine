'use client'

import { useState } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import type { StageInfo } from '@/types/pipeline'

interface StreamingThoughtProps {
  stages: StageInfo[]
  isRunning: boolean
}

/**
 * Collapsible AI "thinking" panel that shows processing steps during plan generation.
 * Each stage appears with a staggered animation and a pulsing dot indicator.
 * Respects reduced-motion preferences.
 */
export function StreamingThought({ stages, isRunning }: StreamingThoughtProps) {
  const t = useTranslations('pipeline')
  const tThought = useTranslations('streaming_thought')
  const [expanded, setExpanded] = useState(true)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  if (stages.length === 0 && !isRunning) return null

  return (
    <div
      className={cn(
        'rounded-[var(--radius-lg)] overflow-hidden',
        'border border-[var(--color-border)]',
        'bg-[var(--color-surface)]'
      )}
    >
      {/* Header toggle */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        aria-controls="streaming-thought-content"
        className={cn(
          'flex items-center justify-between w-full px-4 py-3',
          'text-sm font-medium text-[var(--color-text)]',
          'hover:bg-[var(--color-surface-elevated)] transition-colors'
        )}
      >
        <span className="flex items-center gap-2">
          {isRunning && (
            <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-75 animate-ping motion-reduce:hidden" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[var(--color-primary)]" />
            </span>
          )}
          {isRunning ? tThought('thinking') : tThought('complete')}
        </span>
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          className={cn('transition-transform', expanded && 'rotate-180')}
          aria-hidden="true"
        >
          <path d="M4 6l4 4 4-4" />
        </svg>
      </button>

      {/* Collapsible content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id="streaming-thought-content"
            initial={noMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={noMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div
              className="px-4 pb-4 space-y-1"
              role="log"
              aria-label={tThought('log_label')}
              aria-live="polite"
            >
              {stages.map((stage, i) => (
                <ThoughtStep
                  key={stage.id}
                  label={t(`stages.${stage.id}` as Parameters<typeof t>[0])}
                  status={stage.status}
                  index={i}
                  noMotion={noMotion}
                />
              ))}

              {isRunning && (
                <motion.div
                  initial={noMotion ? false : { opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 py-1.5 pl-6"
                >
                  <ThinkingDots />
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ===== Sub-components ===== */

function ThoughtStep({
  label,
  status,
  index,
  noMotion,
}: {
  label: string
  status: string
  index: number
  noMotion: boolean
}) {
  const isActive = status === 'active'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  return (
    <motion.div
      initial={noMotion ? false : { opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={noMotion ? undefined : { delay: index * 0.05, duration: 0.25 }}
      className="flex items-center gap-2.5 py-1.5"
    >
      <div className="flex items-center justify-center w-5 h-5 shrink-0" aria-hidden="true">
        {isCompleted && (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="var(--color-success)" opacity="0.15" />
            <path
              d="M5 8l2 2 4-4"
              stroke="var(--color-success)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
        {isActive && (
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-50 animate-ping motion-reduce:hidden" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-[var(--color-primary)]" />
          </span>
        )}
        {isFailed && (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="var(--color-error)" opacity="0.15" />
            <path d="M6 6l4 4M10 6l-4 4" stroke="var(--color-error)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        )}
        {!isCompleted && !isActive && !isFailed && (
          <span className="inline-flex h-2 w-2 rounded-full bg-[var(--color-border)]" />
        )}
      </div>

      <span
        className={cn(
          'text-sm',
          isActive && 'text-[var(--color-text)] font-medium',
          isCompleted && 'text-[var(--color-muted)]',
          isFailed && 'text-[var(--color-error)]',
          !isActive && !isCompleted && !isFailed && 'text-[var(--color-muted)]'
        )}
      >
        {label}
      </span>
    </motion.div>
  )
}

function ThinkingDots() {
  return (
    <span className="flex gap-1" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[var(--color-muted)] animate-bounce"
          style={{ animationDelay: `${i * 150}ms`, animationDuration: '1s' }}
        />
      ))}
    </span>
  )
}
