'use client'

import { useState, useRef, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { PipelineNodeGraph } from './pipeline-node-graph'
import { TimelineEntry } from './timeline-entry'
import type { PipelineEvent } from '@/types/pipeline'

interface GlassBoxPanelProps {
  events: PipelineEvent[]
  isRunning: boolean
  score: number | null
  error: string | null
}

/**
 * Glass Box side-panel that visualizes the LangGraph agent pipeline in real-time.
 * Collapsible right-side panel with an animated node graph and SSE event timeline.
 *
 * ADR-022: Glass Box transparency — show pipeline internals to the teacher.
 */
export function GlassBoxPanel({
  events,
  isRunning,
  score,
  error,
}: GlassBoxPanelProps) {
  const t = useTranslations('pipeline')
  const [isOpen, setIsOpen] = useState(true)
  const timelineEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll timeline to bottom when new events arrive
  useEffect(() => {
    if (isOpen && timelineEndRef.current && timelineEndRef.current.scrollIntoView) {
      timelineEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [events.length, isOpen])

  const runStartTs = events.find((e) => e.type === 'run.started')?.ts ?? null
  const visibleEvents = events.filter((e) => e.type !== 'heartbeat')

  return (
    <aside
      className={cn(
        'glass rounded-[var(--radius-lg)] border border-[var(--color-border)]',
        'shadow-[var(--shadow-lg)] transition-all',
        'flex flex-col',
        isOpen ? 'w-full max-w-sm' : 'w-12'
      )}
      aria-label={t('glass_box')}
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-2',
          'border-b border-[var(--color-border)]/50'
        )}
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'flex items-center justify-center',
            'w-8 h-8 rounded-[var(--radius-sm)]',
            'hover:bg-[var(--color-surface-elevated)]',
            'transition-colors duration-150'
          )}
          aria-label={t('toggle_panel')}
          aria-expanded={isOpen}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-text)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn(
              'transition-transform duration-200',
              isOpen ? 'rotate-0' : 'rotate-180'
            )}
            aria-hidden="true"
          >
            <path d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="flex items-center gap-2 overflow-hidden"
            >
              {/* Status indicator */}
              <div
                className={cn(
                  'flex items-center gap-1.5 px-2 py-1',
                  'rounded-full text-[10px] font-semibold',
                  isRunning
                    ? 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
                    : error
                      ? 'bg-[var(--color-error)]/15 text-[var(--color-error)]'
                      : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
                )}
              >
                {isRunning && (
                  <motion.span
                    className="inline-block w-1.5 h-1.5 rounded-full bg-current"
                    animate={{ opacity: [1, 0.3, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                    aria-hidden="true"
                  />
                )}
                {t('glass_box')}
              </div>

              <h2 className="text-sm font-bold text-[var(--color-text)] whitespace-nowrap">
                {t('title')}
              </h2>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Content */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-col overflow-hidden"
          >
            {/* Node Graph */}
            <div className="px-3 py-3 border-b border-[var(--color-border)]/50">
              <PipelineNodeGraph
                events={events}
                isRunning={isRunning}
                score={score}
              />
            </div>

            {/* Timeline */}
            <div className="flex flex-col">
              <div className="px-3 py-2">
                <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                  {t('timeline')}
                </h3>
              </div>

              <div
                className="max-h-[320px] overflow-y-auto"
                role="list"
                aria-label={t('timeline')}
              >
                {visibleEvents.length === 0 ? (
                  <p className="px-3 py-4 text-xs text-[var(--color-muted)] text-center">
                    {t('no_events')}
                  </p>
                ) : (
                  visibleEvents.map((event, i) => (
                    <TimelineEntry
                      key={`${event.run_id}-${event.seq}`}
                      event={event}
                      index={i}
                      runStartTs={runStartTs}
                    />
                  ))
                )}
                <div ref={timelineEndRef} />
              </div>
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
                    'mx-3 mb-3 rounded-[var(--radius-md)] p-3',
                    'bg-[var(--color-error)]/10 border border-[var(--color-error)]/30',
                    'text-xs text-[var(--color-error)]'
                  )}
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  )
}
