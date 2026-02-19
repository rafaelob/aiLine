'use client'

import { useEffect, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useConfetti } from '@/hooks/use-confetti'
import { PlanTabs } from './plan-tabs'
import { TransformationScorecard } from './transformation-scorecard'
import { TeacherReviewPanel } from './teacher-review-panel'
import { AdaptationDiff } from './adaptation-diff'
import { EvidencePanel } from './evidence-panel'
import type { ScorecardData } from './transformation-scorecard'
import type { StudyPlan, QualityReport } from '@/types/plan'

interface PlanResultDisplayProps {
  plan: StudyPlan
  qualityReport: QualityReport | null
  score: number | null
  scorecard: ScorecardData | null
  runId: string | null
  onReset: () => void
}

/**
 * Displays the plan generation result with success celebration,
 * transformation scorecard, teacher review panel, and plan tabs.
 * Fires confetti on mount to celebrate successful plan generation.
 */
export function PlanResultDisplay({
  plan,
  qualityReport,
  score,
  scorecard,
  runId,
  onReset,
}: PlanResultDisplayProps) {
  const t = useTranslations('plans')
  const { fire: fireConfetti } = useConfetti()
  const confettiFired = useRef(false)

  useEffect(() => {
    if (!confettiFired.current) {
      confettiFired.current = true
      fireConfetti({ x: 0.5, y: 0.3 })
    }
  }, [fireConfetti])

  return (
    <div className="space-y-6">
      {/* Success celebration */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        role="status"
        aria-live="polite"
        className={cn(
          'flex items-center gap-3 p-4 rounded-[var(--radius-lg)]',
          'bg-[var(--color-success)]/10 border border-[var(--color-success)]/20'
        )}
      >
        <div
          className="flex items-center justify-center w-10 h-10 rounded-full bg-[var(--color-success)]"
          aria-hidden="true"
        >
          <SuccessCheckIcon />
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--color-success)]">
            {t('generation_complete')}
          </p>
          {score !== null && (
            <p className="text-xs text-[var(--color-muted)] mt-0.5">
              {t('quality_score')}: {score}/100
            </p>
          )}
        </div>
      </motion.div>

      {scorecard && (
        <TransformationScorecard scorecard={scorecard} />
      )}

      <EvidencePanel
        plan={plan}
        qualityReport={qualityReport}
        scorecard={scorecard}
      />

      {runId && <TeacherReviewPanel planId={runId} />}

      <AdaptationDiff plan={plan} />

      <PlanTabs plan={plan} qualityReport={qualityReport} score={score} scorecard={scorecard} />

      <div className="flex justify-center">
        <button
          type="button"
          onClick={onReset}
          className={cn(
            'px-6 py-2 rounded-[var(--radius-md)]',
            'border border-[var(--color-border)] text-[var(--color-text)]',
            'text-sm font-medium hover:bg-[var(--color-surface-elevated)]'
          )}
        >
          {t('create')}
        </button>
      </div>
    </div>
  )
}

function SuccessCheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M5 10l3.5 3.5L15 7"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
