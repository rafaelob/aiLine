'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import type { PipelineEvent, PipelineStage } from '@/types/pipeline'

interface PipelineNodeGraphProps {
  events: PipelineEvent[]
  currentStage: PipelineStage | null
  isRunning: boolean
  score: number | null
}

/** Node IDs for the flow graph. */
type NodeId = 'user' | 'router' | 'llm' | 'skill' | 'quality' | 'response'

interface NodeState {
  id: NodeId
  active: boolean
  completed: boolean
  rejected: boolean
}

const NODE_ORDER: NodeId[] = ['user', 'router', 'llm', 'skill', 'quality', 'response']

/**
 * Derive which nodes are active/completed from pipeline events.
 * Maps SSE event types to the conceptual node graph.
 */
function deriveNodeStates(events: PipelineEvent[], isRunning: boolean): NodeState[] {
  const hasStage = (stage: string) => events.some((e) => e.stage === stage)
  const hasType = (type: string) => events.some((e) => e.type === type)
  const lastDecision = events.findLast((e) => e.type === 'quality.decision')
  const wasRejected = lastDecision?.payload?.decision === 'must-refine'

  return NODE_ORDER.map((id): NodeState => {
    switch (id) {
      case 'user':
        return { id, active: false, completed: events.length > 0, rejected: false }
      case 'router':
        return {
          id,
          active: isRunning && hasStage('planning') && !hasStage('validation'),
          completed: hasStage('validation') || hasStage('execution'),
          rejected: false,
        }
      case 'llm':
        return {
          id,
          active: isRunning && hasType('tool.started') && !hasType('tool.completed'),
          completed: hasType('tool.completed'),
          rejected: false,
        }
      case 'skill':
        return {
          id,
          active: isRunning && hasStage('execution') && !hasType('quality.scored'),
          completed: hasType('quality.scored'),
          rejected: false,
        }
      case 'quality':
        return {
          id,
          active: isRunning && hasType('quality.scored') && !hasType('quality.decision'),
          completed: hasType('quality.decision'),
          rejected: wasRejected,
        }
      case 'response':
        return {
          id,
          active: false,
          completed: hasType('run.completed'),
          rejected: false,
        }
      default:
        return { id, active: false, completed: false, rejected: false }
    }
  })
}

const NODE_ICONS: Record<NodeId, string> = {
  user: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
  router: 'M13 10V3L4 14h7v7l9-11h-7z',
  llm: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  skill: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
  quality: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  response: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
}

/**
 * Animated node graph showing the pipeline flow.
 * User -> Router -> LLM -> Skill Agent -> QualityGate -> Response
 */
export function PipelineNodeGraph({
  events,
  currentStage,
  isRunning,
  score,
}: PipelineNodeGraphProps) {
  const t = useTranslations('pipeline')
  const nodes = deriveNodeStates(events, isRunning)

  return (
    <div
      className="relative flex flex-col items-start gap-2 py-2 sm:flex-row sm:items-center sm:gap-1 sm:overflow-x-auto"
      role="img"
      aria-label={t('title')}
    >
      {nodes.map((node, i) => (
        <div key={node.id} className="flex items-center sm:flex-row">
          {/* Node */}
          <motion.div
            className={cn(
              'relative flex flex-col items-center gap-1',
              'min-w-[56px]'
            )}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: i * 0.08, type: 'spring', stiffness: 200 }}
          >
            {/* Circle */}
            <div
              className={cn(
                'relative flex items-center justify-center',
                'w-9 h-9 rounded-full transition-colors',
                'duration-300',
                node.completed && 'bg-[var(--color-success)]',
                node.active && 'bg-[var(--color-warning)]',
                node.rejected && 'bg-[var(--color-error)]',
                !node.completed && !node.active && !node.rejected && 'bg-[var(--color-border)]'
              )}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke={node.completed || node.active || node.rejected ? 'white' : 'var(--color-muted)'}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d={NODE_ICONS[node.id]} />
              </svg>

              {/* Active pulse ring */}
              {node.active && (
                <motion.div
                  className="absolute inset-0 rounded-full ring-2 ring-[var(--color-warning)]"
                  animate={{ scale: [1, 1.5], opacity: [0.6, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  aria-hidden="true"
                />
              )}

              {/* Rejected pulse */}
              {node.rejected && (
                <motion.div
                  className="absolute inset-0 rounded-full ring-2 ring-[var(--color-error)]"
                  animate={{ scale: [1, 1.5], opacity: [0.6, 0] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                  aria-hidden="true"
                />
              )}
            </div>

            {/* Label */}
            <span className="text-[10px] font-medium text-[var(--color-muted)] text-center leading-tight whitespace-nowrap">
              {t(`node_${node.id}`)}
            </span>

            {/* Score badge on quality node */}
            {node.id === 'quality' && score !== null && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className={cn(
                  'absolute -top-1 -right-1 text-[9px] font-bold',
                  'px-1 rounded-full text-white',
                  score >= 80 && 'bg-[var(--color-success)]',
                  score >= 60 && score < 80 && 'bg-[var(--color-warning)]',
                  score < 60 && 'bg-[var(--color-error)]'
                )}
              >
                {score}
              </motion.span>
            )}
          </motion.div>

          {/* Connector arrow -- vertical on mobile, horizontal on sm+ */}
          {i < nodes.length - 1 && (
            <>
              {/* Horizontal connector (sm+) */}
              <div className="hidden sm:flex items-center mx-0.5" aria-hidden="true">
                <div
                  className={cn(
                    'w-4 h-0.5 transition-colors duration-300',
                    nodes[i].completed
                      ? 'bg-[var(--color-success)]'
                      : 'bg-[var(--color-border)]'
                  )}
                />
                <div
                  className={cn(
                    'w-0 h-0 border-t-[3px] border-b-[3px] border-l-[5px]',
                    'border-t-transparent border-b-transparent transition-colors duration-300',
                    nodes[i].completed
                      ? 'border-l-[var(--color-success)]'
                      : 'border-l-[var(--color-border)]'
                  )}
                />
              </div>
              {/* Vertical connector (mobile) */}
              <div className="flex sm:hidden flex-col items-center my-0.5 ml-4" aria-hidden="true">
                <div
                  className={cn(
                    'w-0.5 h-3 transition-colors duration-300',
                    nodes[i].completed
                      ? 'bg-[var(--color-success)]'
                      : 'bg-[var(--color-border)]'
                  )}
                />
                <div
                  className={cn(
                    'w-0 h-0 border-l-[3px] border-r-[3px] border-t-[5px]',
                    'border-l-transparent border-r-transparent transition-colors duration-300',
                    nodes[i].completed
                      ? 'border-t-[var(--color-success)]'
                      : 'border-t-[var(--color-border)]'
                  )}
                />
              </div>
            </>
          )}
        </div>
      ))}

      {/* Loop-back arrow when quality rejects */}
      {nodes.find((n) => n.id === 'quality')?.rejected && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-0 left-1/2 -translate-x-1/2"
          aria-hidden="true"
        >
          <svg width="120" height="20" viewBox="0 0 120 20" fill="none">
            <path
              d="M100 5 C100 15, 20 15, 20 5"
              stroke="var(--color-error)"
              strokeWidth="1.5"
              strokeDasharray="4 2"
              fill="none"
              markerEnd="url(#loopArrow)"
            />
            <defs>
              <marker id="loopArrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
                <path d="M0 0 L6 3 L0 6Z" fill="var(--color-error)" />
              </marker>
            </defs>
          </svg>
        </motion.div>
      )}
    </div>
  )
}
