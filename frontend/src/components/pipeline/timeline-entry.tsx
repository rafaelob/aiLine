'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { PipelineEvent, PipelineEventType } from '@/types/pipeline'

interface TimelineEntryProps {
  event: PipelineEvent
  index: number
  /** Timestamp of the run.started event for relative time calculation. */
  runStartTs: string | null
}

const TYPE_ICONS: Record<string, string> = {
  'run.started': 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z',
  'run.completed': 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  'run.failed': 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  'stage.started': 'M13 10V3L4 14h7v7l9-11h-7z',
  'stage.progress': 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  'stage.completed': 'M5 13l4 4L19 7',
  'stage.failed': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  'quality.scored': 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
  'quality.decision': 'M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z',
  'refinement.started': 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  'refinement.completed': 'M5 13l4 4L19 7',
  'tool.started': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
  'tool.completed': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
  'heartbeat': 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
}

function typeColor(type: PipelineEventType): string {
  if (type.startsWith('run.failed') || type.startsWith('stage.failed')) {
    return 'text-[var(--color-error)] bg-[var(--color-error)]/10'
  }
  if (type.includes('completed') || type === 'quality.decision') {
    return 'text-[var(--color-success)] bg-[var(--color-success)]/10'
  }
  if (type.includes('started') || type.includes('progress')) {
    return 'text-[var(--color-warning)] bg-[var(--color-warning)]/10'
  }
  if (type.startsWith('quality')) {
    return 'text-[var(--color-secondary)] bg-[var(--color-secondary)]/10'
  }
  return 'text-[var(--color-muted)] bg-[var(--color-border)]'
}

/** Compute relative time string from runStartTs. */
function relativeTime(eventTs: string, runStartTs: string | null): string {
  if (!runStartTs) return ''
  const diff = new Date(eventTs).getTime() - new Date(runStartTs).getTime()
  if (diff < 0) return '+0.0s'
  return `+${(diff / 1000).toFixed(1)}s`
}

/** Extract a short rationale string from event payload. */
function extractRationale(event: PipelineEvent): string | null {
  const p = event.payload
  if (!p) return null

  // Model selection info
  if (p.model) {
    const confidence = typeof p.confidence === 'number' ? `, ${(p.confidence * 100).toFixed(0)}%` : ''
    return `${p.model}${confidence}`
  }

  // Quality score
  if (typeof p.score === 'number') {
    return `${p.score}/100`
  }

  // Quality decision
  if (p.decision) {
    return String(p.decision)
  }

  // Tool name
  if (p.tool_name) {
    return String(p.tool_name)
  }

  // Stage name
  if (p.stage_name) {
    return String(p.stage_name)
  }

  // Error
  if (p.error) {
    return String(p.error)
  }

  return null
}

/**
 * Single entry in the Glass Box event timeline.
 * Shows timestamp, stage icon, label, rationale, and latency.
 */
export function TimelineEntry({ event, index, runStartTs }: TimelineEntryProps) {
  const t = useTranslations('pipeline')
  const relative = relativeTime(event.ts, runStartTs)
  const rationale = extractRationale(event)
  const iconPath = TYPE_ICONS[event.type] ?? TYPE_ICONS['heartbeat']
  const colorClass = typeColor(event.type)

  // Skip heartbeat events in the visible timeline
  if (event.type === 'heartbeat') return null

  return (
    <motion.div
      className={cn(
        'flex items-start gap-3 px-3 py-2',
        'border-b border-[var(--color-border)]/50',
        'last:border-b-0'
      )}
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03, duration: 0.2 }}
      role="listitem"
    >
      {/* Timestamp */}
      <span className="text-[10px] font-mono text-[var(--color-muted)] w-12 shrink-0 pt-0.5 text-right">
        {relative}
      </span>

      {/* Icon */}
      <div
        className={cn(
          'flex items-center justify-center w-6 h-6 rounded-full shrink-0',
          colorClass
        )}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d={iconPath} />
        </svg>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <span className="text-xs font-semibold text-[var(--color-text)]">
          {t(`event_types.${event.type}` as Parameters<typeof t>[0])}
        </span>
        {rationale && (
          <p className="text-[11px] text-[var(--color-muted)] truncate mt-0.5">
            {rationale}
          </p>
        )}
      </div>

      {/* Latency badge */}
      {relative && (
        <span
          className={cn(
            'text-[9px] font-mono px-1.5 py-0.5 rounded-full shrink-0',
            'bg-[var(--color-surface-elevated)] text-[var(--color-muted)]'
          )}
          aria-label={`${t('latency')}: ${relative}`}
        >
          {relative}
        </span>
      )}
    </motion.div>
  )
}
