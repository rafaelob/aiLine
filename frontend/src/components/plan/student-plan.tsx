'use client'

import { cn } from '@/lib/cn'
import { MarkdownWithMermaid } from '@/components/shared/markdown-with-mermaid'
import type { StudyPlan } from '@/types/plan'

interface StudentPlanProps {
  plan: StudyPlan
}

/**
 * Student-facing simplified plan.
 * Shows objectives and activities without teacher-specific detail.
 * Uses simpler language and larger text for readability.
 */
export function StudentPlan({ plan }: StudentPlanProps) {
  return (
    <article aria-label={`Student plan: ${plan.title}`} className="space-y-6">
      {/* Header */}
      <header className="text-center">
        <h2 className="text-2xl font-bold text-[var(--color-text)]">{plan.title}</h2>
        <p className="text-base text-[var(--color-muted)] mt-1">
          {plan.subject} &mdash; {plan.grade}
        </p>
      </header>

      {/* What you will learn */}
      <section aria-labelledby="student-objectives">
        <h3
          id="student-objectives"
          className={cn(
            'text-lg font-semibold text-[var(--color-primary)] mb-4',
            'flex items-center gap-2'
          )}
        >
          <TargetIcon />
          What You Will Learn
        </h3>
        <ul className="space-y-3">
          {plan.objectives.map((obj, i) => (
            <li
              key={i}
              className={cn(
                'flex items-start gap-3 text-base text-[var(--color-text)]',
                'p-3 rounded-[var(--radius-md)]',
                'bg-[var(--color-surface-elevated)]'
              )}
            >
              <span
                className={cn(
                  'flex items-center justify-center w-7 h-7 rounded-full shrink-0',
                  'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
                  'text-xs font-bold'
                )}
                aria-hidden="true"
              >
                {i + 1}
              </span>
              {obj}
            </li>
          ))}
        </ul>
      </section>

      {/* Activities */}
      <section aria-labelledby="student-activities">
        <h3
          id="student-activities"
          className={cn(
            'text-lg font-semibold text-[var(--color-primary)] mb-4',
            'flex items-center gap-2'
          )}
        >
          <ActivityIcon />
          Activities
        </h3>
        <div className="space-y-4">
          {plan.activities.map((activity, i) => (
            <div
              key={i}
              className={cn(
                'rounded-[var(--radius-lg)] border-2 p-5',
                'border-[var(--color-border)] bg-[var(--color-surface)]'
              )}
            >
              <div className="flex items-center gap-3 mb-2">
                <span
                  className={cn(
                    'flex items-center justify-center w-8 h-8',
                    'rounded-[var(--radius-md)] text-sm font-bold',
                    'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)]'
                  )}
                  aria-hidden="true"
                >
                  {i + 1}
                </span>
                <h4 className="text-base font-semibold text-[var(--color-text)]">
                  {activity.title}
                </h4>
              </div>
              <div className="text-base text-[var(--color-text)] leading-relaxed">
                <MarkdownWithMermaid
                  content={activity.description}
                  textClassName="text-base text-[var(--color-text)]"
                />
              </div>
              <div className="mt-3 flex items-center gap-2 text-sm text-[var(--color-muted)]">
                <ClockIcon />
                <span>{activity.duration_minutes} minutes</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </article>
  )
}

function TargetIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}

function ActivityIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
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
