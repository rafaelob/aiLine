'use client'

import { useState, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { PipelineEvent, StageInfo } from '@/types/pipeline'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ThoughtPanelProps {
  stages: StageInfo[]
  events: PipelineEvent[]
  isRunning: boolean
  className?: string
}

interface ThoughtStep {
  id: string
  label: string
  detail: string | null
  status: 'pending' | 'active' | 'completed' | 'failed'
  icon: 'stage' | 'tool' | 'quality' | 'skill'
  timestamp: string
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

/**
 * Collapsible sidebar/overlay showing agent reasoning steps during plan
 * generation. Displays stage progression, tool calls, quality scores,
 * and activated skills from SSE events.
 *
 * Desktop: sidebar next to pipeline viewer.
 * Mobile: overlay panel toggled by button.
 *
 * ARIA: role="complementary", aria-label, aria-expanded, keyboard toggle.
 */
export function ThoughtPanel({
  stages,
  events,
  isRunning,
  className,
}: ThoughtPanelProps) {
  const t = useTranslations('thoughtPanel')
  const tPipeline = useTranslations('pipeline')
  const [expanded, setExpanded] = useState(true)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  // Build thought steps from events
  const steps = useMemo(() => buildSteps(events, stages, tPipeline), [events, stages, tPipeline])

  // Extract activated skills from events
  const activatedSkills = useMemo(() => {
    const skills: string[] = []
    for (const ev of events) {
      if (ev.type === 'tool.started' && ev.payload?.tool_name) {
        const name = String(ev.payload.tool_name)
        if (!skills.includes(name)) skills.push(name)
      }
    }
    return skills
  }, [events])

  // Extract quality score
  const qualityScore = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      if (events[i].type === 'quality.scored' && typeof events[i].payload?.score === 'number') {
        return events[i].payload.score as number
      }
    }
    return null
  }, [events])

  // Extract RAG citations
  const ragCitations = useMemo(() => {
    const citations: string[] = []
    for (const ev of events) {
      if (ev.payload?.citations && Array.isArray(ev.payload.citations)) {
        for (const c of ev.payload.citations as string[]) {
          if (!citations.includes(c)) citations.push(c)
        }
      }
      if (ev.payload?.sources && Array.isArray(ev.payload.sources)) {
        for (const s of ev.payload.sources as string[]) {
          if (!citations.includes(s)) citations.push(s)
        }
      }
    }
    return citations
  }, [events])

  if (steps.length === 0 && !isRunning) return null

  return (
    <aside
      role="complementary"
      aria-label={t('panel_label')}
      className={cn(
        'rounded-[var(--radius-lg)] overflow-hidden',
        'border border-[var(--color-border)]',
        'bg-[var(--color-surface)]',
        className,
      )}
    >
      {/* Header toggle */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        aria-controls="thought-panel-content"
        className={cn(
          'flex items-center justify-between w-full px-4 py-3',
          'text-sm font-medium text-[var(--color-text)]',
          'hover:bg-[var(--color-surface-elevated)] transition-colors',
        )}
      >
        <span className="flex items-center gap-2">
          <ThoughtIcon />
          {t('title')}
          {isRunning && (
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-50 animate-ping motion-reduce:hidden" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-primary)]" />
            </span>
          )}
          <span className="text-xs text-[var(--color-muted)]">
            ({steps.length})
          </span>
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
            id="thought-panel-content"
            initial={noMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={noMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4 max-h-[60vh] overflow-y-auto">
              {/* Steps log */}
              <div
                role="log"
                aria-label={t('steps_label')}
                aria-live="polite"
                className="space-y-1"
              >
                {steps.map((step, i) => (
                  <StepRow
                    key={step.id}
                    step={step}
                    index={i}
                    noMotion={noMotion}
                  />
                ))}
              </div>

              {/* Activated skills */}
              {activatedSkills.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-2">
                    {t('skills_label')}
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {activatedSkills.map((skill) => (
                      <span
                        key={skill}
                        className={cn(
                          'inline-flex items-center px-2 py-0.5',
                          'rounded-full text-[10px] font-medium',
                          'bg-[var(--color-primary)]/10 text-[var(--color-primary)]',
                          'border border-[var(--color-primary)]/20',
                        )}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Quality score */}
              {qualityScore !== null && (
                <div className="flex items-center gap-2">
                  <QualityIcon />
                  <span className="text-xs font-medium text-[var(--color-text)]">
                    {t('quality_label')}:
                  </span>
                  <span
                    className={cn(
                      'text-xs font-bold',
                      qualityScore >= 80
                        ? 'text-[var(--color-success)]'
                        : qualityScore >= 60
                          ? 'text-[var(--color-warning)]'
                          : 'text-[var(--color-error)]',
                    )}
                  >
                    {qualityScore}/100
                  </span>
                </div>
              )}

              {/* RAG citations */}
              {ragCitations.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-1.5">
                    {t('citations_label')}
                  </h4>
                  <ul className="space-y-0.5">
                    {ragCitations.map((citation, i) => (
                      <li
                        key={i}
                        className="text-[10px] text-[var(--color-muted)] truncate pl-3 relative before:content-[''] before:absolute before:left-0 before:top-1/2 before:w-1.5 before:h-1.5 before:rounded-full before:bg-[var(--color-border)] before:-translate-y-1/2"
                      >
                        {citation}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  )
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function StepRow({
  step,
  index,
  noMotion,
}: {
  step: ThoughtStep
  index: number
  noMotion: boolean
}) {
  return (
    <motion.div
      initial={noMotion ? false : { opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={noMotion ? undefined : { delay: index * 0.03, duration: 0.2 }}
      className="flex items-start gap-2 py-1"
    >
      <div className="flex items-center justify-center w-4 h-4 mt-0.5 shrink-0" aria-hidden="true">
        <StepStatusIcon status={step.status} />
      </div>
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            'text-xs',
            step.status === 'active' && 'text-[var(--color-text)] font-medium',
            step.status === 'completed' && 'text-[var(--color-muted)]',
            step.status === 'failed' && 'text-[var(--color-error)]',
            step.status === 'pending' && 'text-[var(--color-muted)]',
          )}
        >
          {step.label}
        </span>
        {step.detail && (
          <p className="text-[10px] text-[var(--color-muted)] truncate mt-0.5">
            {step.detail}
          </p>
        )}
      </div>
    </motion.div>
  )
}

function StepStatusIcon({ status }: { status: string }) {
  if (status === 'completed') {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="5" fill="var(--color-success)" opacity="0.2" />
        <path d="M4 6L5.5 7.5L8.5 4.5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
  if (status === 'active') {
    return (
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-50 animate-ping motion-reduce:hidden" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[var(--color-primary)]" />
      </span>
    )
  }
  if (status === 'failed') {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="5" fill="var(--color-error)" opacity="0.2" />
        <path d="M4.5 4.5l3 3M7.5 4.5l-3 3" stroke="var(--color-error)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    )
  }
  return <span className="inline-flex h-1.5 w-1.5 rounded-full bg-[var(--color-border)]" />
}

/* ------------------------------------------------------------------ */
/*  Icons                                                              */
/* ------------------------------------------------------------------ */

function ThoughtIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
    </svg>
  )
}

function QualityIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
      <path d="M22 4L12 14.01l-3-3" />
    </svg>
  )
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function buildSteps(
  events: PipelineEvent[],
  stages: StageInfo[],
  tPipeline: (key: string) => string,
): ThoughtStep[] {
  const steps: ThoughtStep[] = []
  const seen = new Set<string>()

  for (const ev of events) {
    const id = `${ev.type}-${ev.seq}`
    if (seen.has(id)) continue
    seen.add(id)

    switch (ev.type) {
      case 'stage.started':
        if (ev.stage) {
          steps.push({
            id,
            label: tPipeline(`stages.${ev.stage}` as Parameters<typeof tPipeline>[0]),
            detail: null,
            status: 'active',
            icon: 'stage',
            timestamp: ev.ts,
          })
        }
        break

      case 'stage.completed':
        if (ev.stage) {
          // Update previous active step for this stage
          const existingIdx = steps.findIndex(
            (s) => s.label === tPipeline(`stages.${ev.stage}` as Parameters<typeof tPipeline>[0]) && s.status === 'active',
          )
          if (existingIdx >= 0) {
            steps[existingIdx] = { ...steps[existingIdx], status: 'completed' }
          }
        }
        break

      case 'stage.failed':
        if (ev.stage) {
          const existingIdx = steps.findIndex(
            (s) => s.label === tPipeline(`stages.${ev.stage}` as Parameters<typeof tPipeline>[0]) && s.status === 'active',
          )
          if (existingIdx >= 0) {
            steps[existingIdx] = { ...steps[existingIdx], status: 'failed' }
          }
        }
        break

      case 'tool.started':
        steps.push({
          id,
          label: String(ev.payload?.tool_name ?? 'Tool'),
          detail: ev.payload?.description ? String(ev.payload.description) : null,
          status: 'active',
          icon: 'tool',
          timestamp: ev.ts,
        })
        break

      case 'tool.completed': {
        const toolName = String(ev.payload?.tool_name ?? 'Tool')
        const toolIdx = steps.findIndex(
          (s) => s.label === toolName && s.status === 'active' && s.icon === 'tool',
        )
        if (toolIdx >= 0) {
          steps[toolIdx] = { ...steps[toolIdx], status: 'completed' }
        }
        break
      }

      case 'quality.scored':
        steps.push({
          id,
          label: tPipeline('event_types.quality.scored'),
          detail: typeof ev.payload?.score === 'number' ? `Score: ${ev.payload.score}` : null,
          status: 'completed',
          icon: 'quality',
          timestamp: ev.ts,
        })
        break

      case 'run.completed':
        steps.push({
          id,
          label: tPipeline('event_types.run.completed'),
          detail: null,
          status: 'completed',
          icon: 'stage',
          timestamp: ev.ts,
        })
        break

      case 'run.failed':
        steps.push({
          id,
          label: tPipeline('event_types.run.failed'),
          detail: ev.payload?.error ? String(ev.payload.error) : null,
          status: 'failed',
          icon: 'stage',
          timestamp: ev.ts,
        })
        break
    }
  }

  return steps
}
