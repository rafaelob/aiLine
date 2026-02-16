'use client'

import { useState } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import type { StageInfo } from '@/types/pipeline'

interface StreamingThoughtProps {
  stages: StageInfo[]
  isRunning: boolean
}

/**
 * Collapsible AI "thinking" panel that shows processing steps during plan generation.
 * Each stage appears with a staggered animation and a pulsing dot indicator.
 * The loading indicator adapts to the active accessibility persona.
 * Respects reduced-motion preferences.
 */
export function StreamingThought({ stages, isRunning }: StreamingThoughtProps) {
  const t = useTranslations('pipeline')
  const tThought = useTranslations('streaming_thought')
  const [expanded, setExpanded] = useState(true)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const theme = useAccessibilityStore((s) => s.theme)

  if (stages.length === 0 && !isRunning) return null

  const completedCount = stages.filter((s) => s.status === 'completed').length
  const totalCount = stages.length
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

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
            <PersonaIndicator theme={theme} noMotion={noMotion} />
          )}
          {isRunning ? tThought('thinking') : tThought('complete')}
          {isRunning && theme === 'tdah' && totalCount > 0 && (
            <span className="ml-1 text-xs text-[var(--color-muted)]">
              {completedCount}/{totalCount} ({progressPct}%)
            </span>
          )}
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

      {/* ADHD progress bar */}
      {isRunning && theme === 'tdah' && totalCount > 0 && (
        <div className="px-4 pb-1" aria-hidden="true">
          <div className="h-1.5 rounded-full bg-[var(--color-surface-elevated)] overflow-hidden">
            <div
              className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

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
                  <PersonaThinkingDots theme={theme} />
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

/**
 * Persona-adaptive loading indicator shown in the header.
 * - TEA: calm slow-pulsing dot (no distracting ping)
 * - ADHD: not shown (progress bar in header instead)
 * - Dyslexia: simple static dot (no spinning)
 * - High Contrast: neon glow dot
 * - Default: standard pulsing dot with ping
 */
function PersonaIndicator({ theme, noMotion }: { theme: string; noMotion: boolean }) {
  if (theme === 'tea') {
    return (
      <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
        <span
          className={cn(
            'relative inline-flex h-2.5 w-2.5 rounded-full bg-[var(--color-primary)]',
            !noMotion && 'animate-persona-breathe'
          )}
        />
      </span>
    )
  }

  if (theme === 'dyslexia') {
    return (
      <span className="relative flex h-3 w-3" aria-hidden="true">
        <span className="inline-flex h-3 w-3 rounded-sm bg-[var(--color-primary)]" />
      </span>
    )
  }

  if (theme === 'high-contrast') {
    return (
      <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
        <span
          className="inline-flex h-2.5 w-2.5 rounded-full bg-[var(--color-primary)]"
          style={{ boxShadow: '0 0 8px 2px var(--color-primary)' }}
        />
      </span>
    )
  }

  // Default / ADHD / other
  return (
    <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
      <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-75 animate-ping motion-reduce:hidden" />
      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[var(--color-primary)]" />
    </span>
  )
}

/**
 * Persona-adaptive thinking dots shown in the log area.
 * - TEA: single slow-breathing circle
 * - ADHD: fast bouncing dots with different colors
 * - Dyslexia: simple block placeholders (no spinning)
 * - High Contrast: neon glowing dots
 * - Default: standard bouncing dots
 */
function PersonaThinkingDots({ theme }: { theme: string }) {
  if (theme === 'tea') {
    return (
      <span className="flex gap-2" aria-hidden="true">
        <span className="h-2 w-2 rounded-full bg-[var(--color-primary)] opacity-60 animate-persona-breathe" />
      </span>
    )
  }

  if (theme === 'tdah') {
    return (
      <span className="flex gap-1" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full animate-bounce"
            style={{
              animationDelay: `${i * 100}ms`,
              animationDuration: '0.6s',
              backgroundColor: i === 0
                ? 'var(--color-primary)'
                : i === 1
                  ? 'var(--color-secondary)'
                  : 'var(--color-success)',
            }}
          />
        ))}
      </span>
    )
  }

  if (theme === 'dyslexia') {
    return (
      <span className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-sm bg-[var(--color-muted)] animate-pulse"
            style={{ animationDelay: `${i * 300}ms` }}
          />
        ))}
      </span>
    )
  }

  if (theme === 'high-contrast') {
    return (
      <span className="flex gap-1" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full animate-bounce"
            style={{
              animationDelay: `${i * 150}ms`,
              animationDuration: '1s',
              backgroundColor: 'var(--color-primary)',
              boxShadow: '0 0 6px 1px var(--color-primary)',
            }}
          />
        ))}
      </span>
    )
  }

  // Default
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
