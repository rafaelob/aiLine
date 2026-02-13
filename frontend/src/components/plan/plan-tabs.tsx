'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { TeacherPlan } from './teacher-plan'
import { StudentPlan } from './student-plan'
import { PlanReport } from './plan-report'
import { PlanExports } from './plan-exports'
import { SessionSummary } from './session-summary'
import type { StudyPlan, QualityReport } from '@/types/plan'

type TabKey = 'teacher' | 'student' | 'report' | 'exports' | 'summary'

const TAB_KEYS: TabKey[] = ['teacher', 'student', 'report', 'exports', 'summary']

interface PlanTabsProps {
  plan: StudyPlan
  qualityReport: QualityReport | null
  score: number | null
}

/**
 * Tabbed view for plan display (ADR-044).
 * Teacher | Student | Report | Exports
 * Keyboard accessible with proper ARIA tabpanel pattern.
 */
export function PlanTabs({ plan, qualityReport, score }: PlanTabsProps) {
  const t = useTranslations('plans.tabs')
  const [activeTab, setActiveTab] = useState<TabKey>('teacher')

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = TAB_KEYS.indexOf(activeTab)
      let nextIndex = currentIndex

      if (e.key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % TAB_KEYS.length
        e.preventDefault()
      } else if (e.key === 'ArrowLeft') {
        nextIndex = (currentIndex - 1 + TAB_KEYS.length) % TAB_KEYS.length
        e.preventDefault()
      } else if (e.key === 'Home') {
        nextIndex = 0
        e.preventDefault()
      } else if (e.key === 'End') {
        nextIndex = TAB_KEYS.length - 1
        e.preventDefault()
      }

      if (nextIndex !== currentIndex) {
        setActiveTab(TAB_KEYS[nextIndex])
        // Focus the new tab button
        const tabEl = document.getElementById(`tab-${TAB_KEYS[nextIndex]}`)
        tabEl?.focus()
      }
    },
    [activeTab]
  )

  return (
    <div className="w-full">
      {/* Tab list with scroll indicators */}
      <div className="relative">
        <div
          className="pointer-events-none absolute left-0 top-0 bottom-0 w-6 bg-gradient-to-r from-[var(--color-bg)] to-transparent z-10 sm:hidden"
          aria-hidden="true"
        />
        <div
          className="pointer-events-none absolute right-0 top-0 bottom-0 w-6 bg-gradient-to-l from-[var(--color-bg)] to-transparent z-10 sm:hidden"
          aria-hidden="true"
        />
        <div
          role="tablist"
          aria-label={t('teacher')}
          onKeyDown={handleKeyDown}
          className={cn(
            'flex border-b border-[var(--color-border)]',
            'overflow-x-auto scrollbar-none'
          )}
        >
        {TAB_KEYS.map((key) => (
          <button
            key={key}
            id={`tab-${key}`}
            type="button"
            role="tab"
            aria-selected={activeTab === key}
            aria-controls={`tabpanel-${key}`}
            tabIndex={activeTab === key ? 0 : -1}
            onClick={() => setActiveTab(key)}
            className={cn(
              'whitespace-nowrap px-4 py-3 text-sm font-medium',
              'border-b-2 transition-colors',
              activeTab === key
                ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-border)]'
            )}
          >
            {t(key)}
          </button>
        ))}
        </div>
      </div>

      {/* Tab panels */}
      <div className="mt-6">
        <div
          id="tabpanel-teacher"
          role="tabpanel"
          aria-labelledby="tab-teacher"
          hidden={activeTab !== 'teacher'}
        >
          {activeTab === 'teacher' && <TeacherPlan plan={plan} />}
        </div>

        <div
          id="tabpanel-student"
          role="tabpanel"
          aria-labelledby="tab-student"
          hidden={activeTab !== 'student'}
        >
          {activeTab === 'student' && <StudentPlan plan={plan} />}
        </div>

        <div
          id="tabpanel-report"
          role="tabpanel"
          aria-labelledby="tab-report"
          hidden={activeTab !== 'report'}
        >
          {activeTab === 'report' && (
            <PlanReport report={qualityReport} score={score} />
          )}
        </div>

        <div
          id="tabpanel-exports"
          role="tabpanel"
          aria-labelledby="tab-exports"
          hidden={activeTab !== 'exports'}
        >
          {activeTab === 'exports' && <PlanExports planId={plan.id} />}
        </div>

        <div
          id="tabpanel-summary"
          role="tabpanel"
          aria-labelledby="tab-summary"
          hidden={activeTab !== 'summary'}
        >
          {activeTab === 'summary' && <SessionSummary plan={plan} />}
        </div>
      </div>
    </div>
  )
}
