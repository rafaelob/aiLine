'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import type { AgentTrace, TraceNode } from '@/types/trace'

interface AgentTraceViewerProps {
  trace: AgentTrace | null
  className?: string
}

/**
 * Collapsible timeline showing LangGraph node execution trace.
 * Each node shows: time_ms, tool calls, quality score.
 * Placed inside the Glass Box Pipeline Viewer panel.
 */
export function AgentTraceViewer({ trace, className }: AgentTraceViewerProps) {
  const t = useTranslations('trace')
  const [expandedNode, setExpandedNode] = useState<string | null>(null)

  if (!trace) {
    return (
      <div className={cn('px-3 py-4 text-xs text-[var(--color-muted)] text-center', className)}>
        {t('no_trace')}
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col gap-1', className)} role="list" aria-label={t('trace_label')}>
      {trace.nodes.map((node, i) => (
        <TraceNodeEntry
          key={node.node_name}
          node={node}
          index={i}
          isLast={i === trace.nodes.length - 1}
          isExpanded={expandedNode === node.node_name}
          onToggle={() =>
            setExpandedNode((prev) =>
              prev === node.node_name ? null : node.node_name
            )
          }
        />
      ))}

      {/* Total time footer */}
      <div className="flex items-center justify-between px-3 py-2 text-[10px] text-[var(--color-muted)]">
        <span>{t('total_time')}</span>
        <span className="font-mono">{trace.total_time_ms}ms</span>
      </div>
    </div>
  )
}

interface TraceNodeEntryProps {
  node: TraceNode
  index: number
  isLast: boolean
  isExpanded: boolean
  onToggle: () => void
}

function TraceNodeEntry({ node, index, isLast, isExpanded, onToggle }: TraceNodeEntryProps) {
  const t = useTranslations('trace')

  const statusColor =
    node.status === 'completed'
      ? 'bg-[var(--color-success)]'
      : node.status === 'running'
        ? 'bg-[var(--color-warning)] animate-pulse'
        : 'bg-[var(--color-error)]'

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      role="listitem"
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        className={cn(
          'flex items-center gap-3 w-full px-3 py-2 text-left',
          'rounded-[var(--radius-sm)]',
          'hover:bg-[var(--color-surface-elevated)]',
          'transition-colors'
        )}
      >
        {/* Timeline connector */}
        <div className="relative flex flex-col items-center">
          <div className={cn('w-2.5 h-2.5 rounded-full shrink-0', statusColor)} />
          {!isLast && (
            <div className="w-px h-4 bg-[var(--color-border)] mt-0.5" aria-hidden="true" />
          )}
        </div>

        {/* Node info */}
        <div className="flex-1 min-w-0">
          <span className="text-xs font-semibold text-[var(--color-text)]">
            {node.node_name}
          </span>
        </div>

        {/* Time badge */}
        <span className="text-[10px] font-mono text-[var(--color-muted)] shrink-0">
          {node.time_ms}ms
        </span>

        {/* Quality score badge */}
        {node.quality_score !== null && (
          <span
            className={cn(
              'text-[10px] font-mono px-1.5 py-0.5 rounded-full shrink-0',
              node.quality_score >= 80
                ? 'bg-[var(--color-success)]/10 text-[var(--color-success)]'
                : node.quality_score >= 60
                  ? 'bg-[var(--color-warning)]/10 text-[var(--color-warning)]'
                  : 'bg-[var(--color-error)]/10 text-[var(--color-error)]'
            )}
          >
            {node.quality_score}
          </span>
        )}

        {/* Expand chevron */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--color-muted)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={cn('transition-transform duration-150', isExpanded && 'rotate-90')}
          aria-hidden="true"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="ml-8 pl-3 pb-2 space-y-1 border-l border-[var(--color-border)]">
              {node.tool_calls.length > 0 && (
                <div>
                  <span className="text-[10px] font-semibold text-[var(--color-muted)] uppercase">
                    {t('tool_calls')}
                  </span>
                  <ul className="mt-0.5 space-y-0.5">
                    {node.tool_calls.map((tool) => (
                      <li key={tool} className="text-[11px] font-mono text-[var(--color-text)]">
                        {tool}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {node.quality_score !== null && (
                <p className="text-[10px] text-[var(--color-muted)]">
                  {t('quality_score')}: <span className="font-mono">{node.quality_score}/100</span>
                </p>
              )}
              <p className="text-[10px] text-[var(--color-muted)]">
                {t('duration')}: <span className="font-mono">{node.time_ms}ms</span>
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
