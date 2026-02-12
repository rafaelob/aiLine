'use client'

import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { MarkdownWithMermaid } from '@/components/shared/markdown-with-mermaid'
import type { StudyPlan } from '@/types/plan'

interface TeacherPlanProps {
  plan: StudyPlan
}

/**
 * Teacher-facing plan view with full detail.
 * Shows objectives, activities with adaptations, assessments, and curriculum alignment.
 */
export function TeacherPlan({ plan }: TeacherPlanProps) {
  const t = useTranslations()

  return (
    <article aria-label={plan.title} className="space-y-6">
      {/* Header */}
      <header>
        <h2 className="text-xl font-bold text-[var(--color-text)]">{plan.title}</h2>
        <div className="flex gap-4 mt-2 text-sm text-[var(--color-muted)]">
          <span>{plan.subject}</span>
          <span aria-hidden="true">|</span>
          <span>{plan.grade}</span>
        </div>
      </header>

      {/* Objectives */}
      <section aria-labelledby="objectives-heading">
        <h3
          id="objectives-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-3"
        >
          {t('plans.form.prompt')} &mdash; Objectives
        </h3>
        <ul className="space-y-2">
          {plan.objectives.map((obj, i) => (
            <li
              key={i}
              className={cn(
                'flex items-start gap-2 text-sm text-[var(--color-text)]',
                'pl-4 border-l-2 border-[var(--color-primary)] py-1'
              )}
            >
              {obj}
            </li>
          ))}
        </ul>
      </section>

      {/* Activities */}
      <section aria-labelledby="activities-heading">
        <h3
          id="activities-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-3"
        >
          Activities
        </h3>
        <div className="space-y-4">
          {plan.activities.map((activity, i) => (
            <div
              key={i}
              className={cn(
                'rounded-[var(--radius-md)] border p-4',
                'bg-[var(--color-surface)] border-[var(--color-border)]'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-[var(--color-text)]">
                  {activity.title}
                </h4>
                <span className="text-xs text-[var(--color-muted)] px-2 py-1 bg-[var(--color-surface-elevated)] rounded-full">
                  {activity.duration_minutes} min
                </span>
              </div>
              <div className="text-sm text-[var(--color-text)] mb-3">
                <MarkdownWithMermaid
                  content={activity.description}
                  textClassName="text-sm text-[var(--color-text)]"
                />
              </div>

              {/* Materials */}
              {activity.materials.length > 0 && (
                <div className="mb-3">
                  <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
                    Materials
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {activity.materials.map((mat, j) => (
                      <span
                        key={j}
                        className="text-xs px-2 py-1 bg-[var(--color-surface-elevated)] rounded-[var(--radius-sm)] text-[var(--color-text)]"
                      >
                        {mat}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Adaptations */}
              {activity.adaptations.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-[var(--color-secondary)] uppercase tracking-wide">
                    Adaptations
                  </span>
                  <ul className="mt-1 space-y-1">
                    {activity.adaptations.map((adapt, j) => (
                      <li
                        key={j}
                        className="text-xs text-[var(--color-text)] flex gap-2"
                      >
                        <span className="font-medium text-[var(--color-secondary)] shrink-0">
                          [{adapt.profile}]
                        </span>
                        {adapt.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Assessments */}
      {plan.assessments.length > 0 && (
        <section aria-labelledby="assessments-heading">
          <h3
            id="assessments-heading"
            className="text-base font-semibold text-[var(--color-text)] mb-3"
          >
            Assessments
          </h3>
          <div className="space-y-3">
            {plan.assessments.map((assessment, i) => (
              <div
                key={i}
                className={cn(
                  'rounded-[var(--radius-md)] border p-4',
                  'bg-[var(--color-surface)] border-[var(--color-border)]'
                )}
              >
                <h4 className="font-medium text-[var(--color-text)] mb-1">
                  {assessment.title}
                </h4>
                <span className="text-xs text-[var(--color-muted)]">
                  Type: {assessment.type}
                </span>
                <ul className="mt-2 space-y-1">
                  {assessment.criteria.map((c, j) => (
                    <li key={j} className="text-sm text-[var(--color-text)] flex items-start gap-2">
                      <span className="text-[var(--color-success)] shrink-0" aria-hidden="true">
                        &bull;
                      </span>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Accessibility Notes */}
      {plan.accessibility_notes.length > 0 && (
        <section aria-labelledby="a11y-notes-heading">
          <h3
            id="a11y-notes-heading"
            className="text-base font-semibold text-[var(--color-secondary)] mb-3"
          >
            Accessibility Notes
          </h3>
          <ul className="space-y-2">
            {plan.accessibility_notes.map((note, i) => (
              <li
                key={i}
                className={cn(
                  'text-sm text-[var(--color-text)] p-3',
                  'bg-[var(--color-secondary)]/5 rounded-[var(--radius-md)]',
                  'border-l-3 border-[var(--color-secondary)]'
                )}
              >
                {note}
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}
