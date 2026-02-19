'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { PipelineEvent, StageInfo } from '@/types/pipeline'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface PipelineVisualizationProps {
  stages: StageInfo[]
  events: PipelineEvent[]
  isRunning: boolean
  score: number | null
  className?: string
}

type VisNodeId = 'rag' | 'profile' | 'planner' | 'quality' | 'executor' | 'export'
type VisNodeStatus = 'idle' | 'active' | 'completed' | 'failed'

interface VisNode {
  id: VisNodeId
  status: VisNodeStatus
  detail: string | null
}

/* ------------------------------------------------------------------ */
/*  Node State Derivation                                              */
/* ------------------------------------------------------------------ */

function deriveVisNodes(
  stages: StageInfo[],
  events: PipelineEvent[],
  isRunning: boolean,
): VisNode[] {
  const stageMap = new Map(stages.map((s) => [s.id, s]))
  const planning = stageMap.get('planning')
  const validation = stageMap.get('validation')
  const refinement = stageMap.get('refinement')
  const execution = stageMap.get('execution')
  const done = stageMap.get('done')

  const hasEvent = (type: string) => events.some((e) => e.type === type)
  const lastTool = events.findLast((e) => e.type === 'tool.started')
  const toolName = lastTool?.payload?.tool_name
    ? String(lastTool.payload.tool_name)
    : null

  // RAG and Profile are parallel sub-steps of planning
  const planningActive = planning?.status === 'active'
  const planningDone = planning?.status === 'completed' || planning?.status === 'failed'

  // Quality score from events
  const qualityEvent = events.findLast((e) => e.type === 'quality.scored')
  const qualityScore =
    typeof qualityEvent?.payload?.score === 'number'
      ? qualityEvent.payload.score
      : null
  const qualityDecision = events.findLast((e) => e.type === 'quality.decision')
  const isRefining = hasEvent('refinement.started') && !hasEvent('refinement.completed')

  return [
    {
      id: 'rag',
      status: toVisStatus(planningActive, planningDone, planning?.status === 'failed'),
      detail: null,
    },
    {
      id: 'profile',
      status: toVisStatus(planningActive, planningDone, planning?.status === 'failed'),
      detail: null,
    },
    {
      id: 'planner',
      status: toVisStatus(
        planningActive || (isRunning && planningDone && !validation),
        planningDone && (validation?.status !== undefined),
        planning?.status === 'failed',
      ),
      detail: null,
    },
    {
      id: 'quality',
      status: toVisStatus(
        validation?.status === 'active' || isRefining,
        validation?.status === 'completed' && !isRefining,
        validation?.status === 'failed',
      ),
      detail: qualityScore !== null ? `${qualityScore}/100` : null,
    },
    {
      id: 'executor',
      status: toVisStatus(
        execution?.status === 'active',
        execution?.status === 'completed',
        execution?.status === 'failed',
      ),
      detail: toolName,
    },
    {
      id: 'export',
      status: toVisStatus(
        false,
        done?.status === 'completed',
        done?.status === 'failed',
      ),
      detail: null,
    },
  ]
}

function toVisStatus(
  active: boolean,
  completed: boolean,
  failed: boolean,
): VisNodeStatus {
  if (failed) return 'failed'
  if (completed) return 'completed'
  if (active) return 'active'
  return 'idle'
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export function PipelineVisualization({
  stages,
  events,
  isRunning,
  score,
  className,
}: PipelineVisualizationProps) {
  const t = useTranslations('pipelineViz')
  const prefersReduced = useReducedMotion()
  const noMotion = prefersReduced ?? false

  const nodes = useMemo(
    () => deriveVisNodes(stages, events, isRunning),
    [stages, events, isRunning],
  )

  const isRefining = useMemo(
    () =>
      events.some((e) => e.type === 'refinement.started') &&
      !events.some((e) => e.type === 'refinement.completed'),
    [events],
  )

  // Active stage name for screen reader announcements
  const activeNode = nodes.find((n) => n.status === 'active')

  return (
    <section
      aria-label={t('title')}
      className={cn(
        'rounded-[var(--radius-lg)] glass p-4 sm:p-6',
        'shadow-[var(--shadow-md)]',
        className,
      )}
    >
      {/* SR-only live region */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {activeNode && t(`nodes.${activeNode.id}`) + ': ' + t('status.active')}
      </div>

      {/* Title row */}
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-sm font-bold text-[var(--color-text)]">
          {t('title')}
        </h3>
        {isRunning && (
          <span className="relative flex h-2 w-2" aria-hidden="true">
            <span className="absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-50 animate-ping motion-reduce:hidden" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-primary)]" />
          </span>
        )}
      </div>

      {/* Node graph */}
      <div
        className="grid gap-2 sm:gap-3"
        style={{
          gridTemplateColumns: 'repeat(5, 1fr)',
          gridTemplateRows: 'auto auto',
          gridTemplateAreas: `
            "rag     conn1  planner  conn3  executor"
            "profile conn2  quality  conn4  export"
          `,
        }}
        role="img"
        aria-label={t('graph_label')}
      >
        {/* Row 1: RAG -> [conn] -> Planner -> [conn] -> Executor */}
        <div style={{ gridArea: 'rag' }}>
          <VisNodeCard node={nodes[0]} t={t} noMotion={noMotion} index={0} />
        </div>
        <div style={{ gridArea: 'conn1' }} className="flex items-center justify-center" aria-hidden="true">
          <Connector completed={nodes[0].status === 'completed'} />
        </div>
        <div style={{ gridArea: 'planner' }} className="row-span-2 flex items-center">
          <VisNodeCard
            node={nodes[2]}
            t={t}
            noMotion={noMotion}
            index={2}
            badge={t('opus_badge')}
          />
        </div>
        <div style={{ gridArea: 'conn3' }} className="flex items-center justify-center" aria-hidden="true">
          <Connector completed={nodes[4].status === 'completed' || nodes[4].status === 'active'} />
        </div>
        <div style={{ gridArea: 'executor' }}>
          <VisNodeCard node={nodes[4]} t={t} noMotion={noMotion} index={4} />
        </div>

        {/* Row 2: Profile -> [conn] -> Quality -> [conn] -> Export */}
        <div style={{ gridArea: 'profile' }}>
          <VisNodeCard node={nodes[1]} t={t} noMotion={noMotion} index={1} />
        </div>
        <div style={{ gridArea: 'conn2' }} className="flex items-center justify-center" aria-hidden="true">
          <Connector completed={nodes[1].status === 'completed'} />
        </div>
        {/* Quality is positioned under planner, connected via merge */}
        <div style={{ gridArea: 'quality' }} className="flex items-center">
          <VisNodeCard
            node={nodes[3]}
            t={t}
            noMotion={noMotion}
            index={3}
            showLoop={isRefining}
          />
        </div>
        <div style={{ gridArea: 'conn4' }} className="flex items-center justify-center" aria-hidden="true">
          <Connector completed={nodes[5].status === 'completed'} />
        </div>
        <div style={{ gridArea: 'export' }}>
          <VisNodeCard node={nodes[5]} t={t} noMotion={noMotion} index={5} />
        </div>
      </div>

      {/* Refinement loop indicator */}
      <AnimatePresence>
        {isRefining && (
          <motion.div
            initial={noMotion ? false : { opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={noMotion ? undefined : { opacity: 0, height: 0 }}
            className={cn(
              'mt-3 flex items-center gap-2 px-3 py-1.5',
              'rounded-[var(--radius-sm)]',
              'bg-[var(--color-warning)]/10 text-[var(--color-warning)]',
              'text-xs font-medium',
            )}
            role="status"
          >
            <LoopIcon />
            {t('refining')}
            {score !== null && (
              <span className="font-bold">{score}/100</span>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

const NODE_ICONS: Record<VisNodeId, string> = {
  rag: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
  profile: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
  planner: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  quality: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  executor: 'M13 10V3L4 14h7v7l9-11h-7z',
  export: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
}

interface VisNodeCardProps {
  node: VisNode
  t: (key: string) => string
  noMotion: boolean
  index: number
  badge?: string
  showLoop?: boolean
}

function VisNodeCard({ node, t, noMotion, index, badge, showLoop }: VisNodeCardProps) {
  const statusColors: Record<VisNodeStatus, string> = {
    idle: 'bg-[var(--color-border)] text-[var(--color-muted)]',
    active: 'bg-[var(--color-warning)] text-white',
    completed: 'bg-[var(--color-success)] text-white',
    failed: 'bg-[var(--color-error)] text-white',
  }

  return (
    <motion.div
      className={cn(
        'relative flex flex-col items-center gap-1 p-2',
        'rounded-[var(--radius-md)]',
        'text-center min-w-0',
      )}
      initial={noMotion ? false : { scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={noMotion ? undefined : { delay: index * 0.06, type: 'spring', stiffness: 200 }}
      tabIndex={0}
      role="group"
      aria-label={`${t(`nodes.${node.id}`)}: ${t(`status.${node.status}`)}`}
    >
      {/* Icon circle */}
      <div
        className={cn(
          'relative flex items-center justify-center',
          'w-10 h-10 rounded-full transition-colors duration-300',
          statusColors[node.status],
        )}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d={NODE_ICONS[node.id]} />
        </svg>

        {/* Active pulse ring */}
        {node.status === 'active' && (
          <motion.div
            className="absolute inset-0 rounded-full ring-2 ring-[var(--color-warning)] motion-reduce:hidden"
            animate={{ scale: [1, 1.6], opacity: [0.5, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            aria-hidden="true"
          />
        )}

        {/* Loop indicator on quality node */}
        {showLoop && (
          <motion.div
            className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[var(--color-warning)] flex items-center justify-center"
            animate={noMotion ? undefined : { rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            aria-hidden="true"
          >
            <LoopIcon size={10} />
          </motion.div>
        )}

        {/* Score badge */}
        {node.id === 'quality' && node.detail && (
          <motion.span
            initial={noMotion ? false : { scale: 0 }}
            animate={{ scale: 1 }}
            className={cn(
              'absolute -bottom-1 left-1/2 -translate-x-1/2',
              'text-[9px] font-bold px-1.5 py-0.5 rounded-full',
              'bg-[var(--color-surface)] text-[var(--color-text)]',
              'border border-[var(--color-border)]',
              'shadow-[var(--shadow-sm)]',
            )}
          >
            {node.detail}
          </motion.span>
        )}
      </div>

      {/* Label */}
      <span className="text-[10px] font-semibold text-[var(--color-text)] leading-tight">
        {t(`nodes.${node.id}`)}
      </span>

      {/* Badge (e.g. "Opus 4.6 Reasoning Core") */}
      {badge && (
        <span
          className={cn(
            'text-[8px] font-medium leading-tight',
            'px-1.5 py-0.5 rounded-full',
            'bg-[var(--color-primary)]/10 text-[var(--color-primary)]',
            'border border-[var(--color-primary)]/20',
          )}
        >
          {badge}
        </span>
      )}

      {/* Detail (tool name on executor) */}
      {node.id === 'executor' && node.detail && (
        <span className="text-[9px] text-[var(--color-muted)] truncate max-w-[80px]">
          {node.detail}
        </span>
      )}
    </motion.div>
  )
}

function Connector({ completed }: { completed: boolean }) {
  return (
    <div className="flex items-center w-full">
      <div
        className={cn(
          'flex-1 h-0.5 transition-colors duration-300 rounded-full',
          completed ? 'bg-[var(--color-success)]' : 'bg-[var(--color-border)]',
        )}
      />
      <div
        className={cn(
          'w-0 h-0 border-t-[3px] border-b-[3px] border-l-[5px]',
          'border-t-transparent border-b-transparent transition-colors duration-300',
          completed ? 'border-l-[var(--color-success)]' : 'border-l-[var(--color-border)]',
        )}
      />
    </div>
  )
}

function LoopIcon({ size = 12 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12a9 9 0 11-3-6.7" />
      <path d="M21 3v6h-6" />
    </svg>
  )
}
