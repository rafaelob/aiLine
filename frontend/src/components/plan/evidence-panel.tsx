'use client'

import { useState, useCallback, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import { usePipelineStore } from '@/stores/pipeline-store'
import type { StudyPlan, QualityReport } from '@/types/plan'
import type { ScorecardData } from './transformation-scorecard'
import type { PipelineEvent } from '@/types/pipeline'

interface EvidencePanelProps {
  plan: StudyPlan
  qualityReport: QualityReport | null
  scorecard: ScorecardData | null
  className?: string
}

interface EvidenceSection {
  id: string
  icon: React.ReactNode
  title: string
  badge: string
  content: React.ReactNode
}

/**
 * Collapsible accordion panel showing AI decision transparency.
 * Sections: Model, Quality Score, Standards Aligned, RAG Provenance,
 * Accommodations, Skills Used, Processing Time.
 */
export function EvidencePanel({ plan, qualityReport, scorecard, className }: EvidencePanelProps) {
  const t = useTranslations('evidence')
  const events = usePipelineStore((s) => s.events)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(['model', 'quality']))

  const toggleSection = useCallback((id: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const aiReceipt = useMemo(() => extractAiReceipt(events), [events])
  const pipelineTime = scorecard?.total_pipeline_time_ms ?? computePipelineTime(events)

  const sections: EvidenceSection[] = useMemo(() => {
    const result: EvidenceSection[] = []

    // Model
    const modelName = scorecard?.model_used ?? aiReceipt?.model ?? 'Auto-routed'
    result.push({
      id: 'model',
      icon: <BrainIcon />,
      title: t('model_title'),
      badge: modelName,
      content: (
        <div className="space-y-2 text-sm">
          <MetricRow label={t('model_name')} value={modelName} />
          {scorecard?.router_rationale && (
            <MetricRow label={t('router_rationale')} value={scorecard.router_rationale} />
          )}
        </div>
      ),
    })

    // Quality Score
    const score = qualityReport?.score ?? scorecard?.quality_score
    if (score != null) {
      const decision = qualityReport?.decision ?? scorecard?.quality_decision
      result.push({
        id: 'quality',
        icon: <ShieldCheckIcon />,
        title: t('quality_title'),
        badge: `${score}/100`,
        content: (
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <QualityGauge score={score} />
              {decision && (
                <span className={cn(
                  'px-2 py-0.5 rounded-full text-xs font-semibold',
                  decision === 'accept' && 'bg-[var(--color-success)]/15 text-[var(--color-success)]',
                  decision === 'refine' && 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]',
                  decision === 'must-refine' && 'bg-[var(--color-error)]/15 text-[var(--color-error)]',
                )}>
                  {decision}
                </span>
              )}
            </div>
            {qualityReport?.structural_checks && qualityReport.structural_checks.length > 0 && (
              <div className="space-y-1 mt-2">
                {qualityReport.structural_checks.map((check, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className={check.passed ? 'text-[var(--color-success)]' : 'text-[var(--color-error)]'}>
                      {check.passed ? '\u2713' : '\u2717'}
                    </span>
                    <span className="text-[var(--color-text)]">{check.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ),
      })
    }

    // Standards Aligned
    if (plan.curriculum_alignment && plan.curriculum_alignment.length > 0) {
      result.push({
        id: 'standards',
        icon: <BookIcon />,
        title: t('standards_title'),
        badge: `${plan.curriculum_alignment.length}`,
        content: (
          <div className="space-y-1.5 text-sm">
            {plan.curriculum_alignment.map((std, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-[var(--color-primary)]/10 text-[var(--color-primary)] shrink-0">
                  {std.standard_id}
                </span>
                <span className="text-xs text-[var(--color-muted)]">{std.standard_name}</span>
              </div>
            ))}
          </div>
        ),
      })
    }

    // RAG Provenance
    const ragScore = scorecard?.rag_groundedness
    if (ragScore != null) {
      result.push({
        id: 'rag',
        icon: <SearchIcon />,
        title: t('rag_title'),
        badge: `${Math.round(ragScore * 100)}%`,
        content: (
          <div className="text-sm">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 rounded-full bg-[var(--color-surface-elevated)] overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-[var(--color-primary)]"
                  initial={noMotion ? { width: `${ragScore * 100}%` } : { width: '0%' }}
                  animate={{ width: `${ragScore * 100}%` }}
                  transition={noMotion ? { duration: 0 } : { duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
              <span className="text-xs font-semibold text-[var(--color-text)]">
                {Math.round(ragScore * 100)}%
              </span>
            </div>
            <p className="text-xs text-[var(--color-muted)] mt-2">
              {t('rag_description')}
            </p>
          </div>
        ),
      })
    }

    // Accommodations
    if (plan.accessibility_notes && plan.accessibility_notes.length > 0) {
      result.push({
        id: 'accommodations',
        icon: <AccessibilityIcon />,
        title: t('accommodations_title'),
        badge: `${plan.accessibility_notes.length}`,
        content: (
          <ul className="space-y-1.5 text-sm">
            {plan.accessibility_notes.map((note, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[var(--color-text)]">
                <span className="text-[var(--color-primary)] mt-0.5 shrink-0">{'\u2192'}</span>
                {note}
              </li>
            ))}
          </ul>
        ),
      })
    }

    // Scorecard adaptations (additional)
    if (scorecard?.accessibility_adaptations && scorecard.accessibility_adaptations.length > 0) {
      const existing = result.find((s) => s.id === 'accommodations')
      if (!existing) {
        result.push({
          id: 'accommodations',
          icon: <AccessibilityIcon />,
          title: t('accommodations_title'),
          badge: `${scorecard.accessibility_adaptations.length}`,
          content: (
            <ul className="space-y-1.5 text-sm">
              {scorecard.accessibility_adaptations.map((adaptation, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-[var(--color-text)]">
                  <span className="text-[var(--color-primary)] mt-0.5 shrink-0">{'\u2192'}</span>
                  {adaptation}
                </li>
              ))}
            </ul>
          ),
        })
      }
    }

    // Processing Time
    if (pipelineTime > 0) {
      const seconds = (pipelineTime / 1000).toFixed(1)
      const refinementCount = events.filter((e) => e.type === 'refinement.completed').length
      result.push({
        id: 'processing',
        icon: <ClockIcon />,
        title: t('processing_title'),
        badge: `${seconds}s`,
        content: (
          <div className="space-y-2 text-sm">
            <MetricRow label={t('total_time')} value={`${seconds}s`} />
            {refinementCount > 0 && (
              <MetricRow label={t('refinement_loops')} value={`${refinementCount}`} />
            )}
            {scorecard?.export_variants_count != null && (
              <MetricRow label={t('export_variants')} value={`${scorecard.export_variants_count}`} />
            )}
          </div>
        ),
      })
    }

    return result
  }, [t, plan, qualityReport, scorecard, aiReceipt, events, pipelineTime, noMotion])

  if (sections.length === 0) {
    return null
  }

  return (
    <section
      className={cn('space-y-1', className)}
      aria-label={t('section_label')}
    >
      <h3 className="text-sm font-semibold text-[var(--color-text)] mb-3 flex items-center gap-2">
        <EyeIcon />
        {t('title')}
      </h3>
      <div className="glass rounded-xl overflow-hidden divide-y divide-[var(--color-border)]">
        {sections.map((section) => {
          const isOpen = openSections.has(section.id)
          return (
            <div key={section.id}>
              <button
                type="button"
                onClick={() => toggleSection(section.id)}
                aria-expanded={isOpen}
                aria-controls={`evidence-${section.id}`}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 text-left',
                  'hover:bg-[var(--color-surface)]/50 transition-colors',
                )}
              >
                <span className="text-[var(--color-primary)] shrink-0" aria-hidden="true">
                  {section.icon}
                </span>
                <span className="flex-1 text-sm font-medium text-[var(--color-text)]">
                  {section.title}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full glass text-[var(--color-primary)]">
                  {section.badge}
                </span>
                <motion.span
                  animate={{ rotate: isOpen ? 180 : 0 }}
                  transition={noMotion ? { duration: 0 } : { duration: 0.2 }}
                  className="text-[var(--color-muted)]"
                  aria-hidden="true"
                >
                  <ChevronDownIcon />
                </motion.span>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    id={`evidence-${section.id}`}
                    role="region"
                    aria-labelledby={`evidence-btn-${section.id}`}
                    initial={noMotion ? undefined : { height: 0, opacity: 0 }}
                    animate={noMotion ? undefined : { height: 'auto', opacity: 1 }}
                    exit={noMotion ? undefined : { height: 0, opacity: 0 }}
                    transition={noMotion ? undefined : { duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 pt-1 pl-11">{section.content}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </section>
  )
}

/* ===== Sub-components ===== */

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-xs text-[var(--color-muted)]">{label}</span>
      <span className="text-xs font-semibold text-[var(--color-text)] text-right">{value}</span>
    </div>
  )
}

function QualityGauge({ score }: { score: number }) {
  const color =
    score >= 80
      ? 'var(--color-success)'
      : score >= 60
        ? 'var(--color-warning)'
        : 'var(--color-error)'

  return (
    <div className="flex items-center gap-2">
      <div className="relative w-12 h-12">
        <svg viewBox="0 0 36 36" className="w-12 h-12 -rotate-90" aria-hidden="true">
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="var(--color-surface-elevated)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 97.4} 97.4`}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[var(--color-text)]">
          {score}
        </span>
      </div>
    </div>
  )
}

/* ===== Data helpers ===== */

interface AiReceiptData {
  model?: string
  quality?: number
  citations?: string[]
}

function extractAiReceipt(events: PipelineEvent[]): AiReceiptData | null {
  const receipt =
    events.find((e) => e.type === 'ai_receipt') ??
    events.find((e) => e.type === 'tool.completed' && e.payload?.tool_name === 'ai_receipt')
  if (!receipt?.payload) return null
  return {
    model: receipt.payload.model as string | undefined,
    quality: receipt.payload.quality as number | undefined,
    citations: receipt.payload.citations as string[] | undefined,
  }
}

function computePipelineTime(events: PipelineEvent[]): number {
  if (events.length < 2) return 0
  const first = events[0]
  const last = events[events.length - 1]
  if (!first?.ts || !last?.ts) return 0
  try {
    return new Date(last.ts).getTime() - new Date(first.ts).getTime()
  } catch {
    return 0
  }
}

/* ===== Icons ===== */

function BrainIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44A2.5 2.5 0 0 1 2.5 17A2.5 2.5 0 0 1 4 12.5A2.5 2.5 0 0 1 2.5 10A2.5 2.5 0 0 1 5.5 7h.5" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44A2.5 2.5 0 0 0 21.5 17a2.5 2.5 0 0 0-1.5-4.5A2.5 2.5 0 0 0 21.5 10a2.5 2.5 0 0 0-3-2.5h-.5" />
    </svg>
  )
}

function ShieldCheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

function BookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  )
}

function AccessibilityIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="4" r="1" />
      <path d="m5 8 3.5 1L12 13l3.5-4L19 8" />
      <path d="m9 21 3-8 3 8" />
    </svg>
  )
}

function ClockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function ChevronDownIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="m6 9 6 6 6-6" />
    </svg>
  )
}
