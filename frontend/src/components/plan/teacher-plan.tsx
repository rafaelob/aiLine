'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
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
  const t = useTranslations('teacher_plan')

  return (
    <motion.article
      aria-label={plan.title}
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.section variants={itemVariants}>
        <header className="gradient-border-glass rounded-2xl glass p-5">
          <h2 className="text-xl font-bold gradient-text-animated">{plan.title}</h2>
          <div className="flex gap-4 mt-2 text-sm text-[var(--color-muted)]">
            <span>{plan.subject}</span>
            <span aria-hidden="true">|</span>
            <span>{plan.grade}</span>
          </div>
        </header>
      </motion.section>

      {/* Objectives */}
      <motion.section variants={itemVariants} aria-labelledby="objectives-heading">
        <h3
          id="objectives-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-3"
        >
          {t('objectives')}
        </h3>
        <ul className="space-y-2">
          {plan.objectives.map((obj, i) => (
            <li
              key={i}
              className={cn(
                'flex items-start gap-3 text-sm text-[var(--color-text)]',
                'p-3 rounded-xl glass card-hover',
                'border-l-3 border-[var(--color-primary)]'
              )}
            >
              <span
                className={cn(
                  'flex items-center justify-center w-6 h-6 rounded-full shrink-0 icon-orb',
                  'text-xs font-bold text-white'
                )}
                style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
                aria-hidden="true"
              >
                {i + 1}
              </span>
              {obj}
            </li>
          ))}
        </ul>
      </motion.section>

      {/* Activities */}
      <motion.section variants={itemVariants} aria-labelledby="activities-heading">
        <h3
          id="activities-heading"
          className="text-base font-semibold text-[var(--color-text)] mb-3"
        >
          {t('activities')}
        </h3>
        <div className="space-y-4">
          {plan.activities.map((activity, i) => (
            <div
              key={i}
              className="gradient-border-glass rounded-2xl glass card-hover p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-[var(--color-text)]">
                  {activity.title}
                </h4>
                <span className="text-xs text-[var(--color-muted)] px-2 py-1 glass rounded-full">
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
                    {t('materials')}
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {activity.materials.map((mat, j) => (
                      <span
                        key={j}
                        className="text-xs px-2 py-1 glass rounded-full text-[var(--color-text)]"
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
                    {t('adaptations')}
                  </span>
                  <ul className="mt-1 space-y-1">
                    {activity.adaptations.map((adapt, j) => (
                      <li
                        key={j}
                        className="text-xs text-[var(--color-text)] flex items-center gap-2"
                      >
                        <span
                          className={cn(
                            'inline-flex items-center justify-center px-1.5 py-0.5 rounded icon-orb',
                            'text-[10px] font-bold text-white shrink-0'
                          )}
                          style={{ background: 'linear-gradient(135deg, var(--color-secondary), var(--color-primary))' }}
                        >
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
      </motion.section>

      {/* Assessments */}
      {plan.assessments.length > 0 && (
        <motion.section variants={itemVariants} aria-labelledby="assessments-heading">
          <h3
            id="assessments-heading"
            className="text-base font-semibold text-[var(--color-text)] mb-3"
          >
            {t('assessments')}
          </h3>
          <div className="space-y-3">
            {plan.assessments.map((assessment, i) => (
              <div
                key={i}
                className="glass card-hover rounded-xl p-4"
              >
                <h4 className="font-medium text-[var(--color-text)] mb-1">
                  {assessment.title}
                </h4>
                <span className="text-xs text-[var(--color-muted)]">
                  {t('type')}: {assessment.type}
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
        </motion.section>
      )}

      {/* Accessibility Notes */}
      {plan.accessibility_notes.length > 0 && (
        <motion.section variants={itemVariants} aria-labelledby="a11y-notes-heading">
          <h3
            id="a11y-notes-heading"
            className={cn(
              'text-base font-semibold text-[var(--color-secondary)] mb-3',
              'flex items-center gap-2'
            )}
          >
            <div
              className="flex items-center justify-center w-7 h-7 icon-orb shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--color-secondary), var(--color-primary))' }}
              aria-hidden="true"
            >
              <span className="text-white"><A11yIcon /></span>
            </div>
            {t('accessibility_notes')}
          </h3>
          <ul className="space-y-2">
            {plan.accessibility_notes.map((note, i) => (
              <li
                key={i}
                className={cn(
                  'text-sm text-[var(--color-text)] p-3',
                  'glass card-hover rounded-xl',
                  'border-l-3 border-[var(--color-secondary)]'
                )}
              >
                {note}
              </li>
            ))}
          </ul>
        </motion.section>
      )}
    </motion.article>
  )
}

function A11yIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="4" r="2" />
      <path d="M12 8v6" />
      <path d="M6 10l6 2 6-2" />
      <path d="M8 22l4-6 4 6" />
    </svg>
  )
}
