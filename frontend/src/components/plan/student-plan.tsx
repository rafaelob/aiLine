'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
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
  const t = useTranslations('student_plan')

  return (
    <motion.article
      aria-label={t('aria_label', { title: plan.title })}
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.section variants={itemVariants}>
        <header className="text-center">
          <h2 className="text-2xl font-bold gradient-text-animated">{plan.title}</h2>
          <p className="text-base text-[var(--color-muted)] mt-1">
            {plan.subject} &mdash; {plan.grade}
          </p>
        </header>
      </motion.section>

      {/* What you will learn */}
      <motion.section variants={itemVariants} aria-labelledby="student-objectives">
        <h3
          id="student-objectives"
          className={cn(
            'text-lg font-semibold text-[var(--color-primary)] mb-4',
            'flex items-center gap-2'
          )}
        >
          <div
            className="flex items-center justify-center w-8 h-8 icon-orb shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
            aria-hidden="true"
          >
            <span className="text-white"><TargetIcon /></span>
          </div>
          {t('what_you_will_learn')}
        </h3>
        <ul className="space-y-3">
          {plan.objectives.map((obj, i) => (
            <li
              key={i}
              className={cn(
                'flex items-start gap-3 text-base text-[var(--color-text)]',
                'p-3 rounded-xl',
                'glass card-hover',
                'border-l-3 border-[var(--color-primary)]'
              )}
            >
              <span
                className={cn(
                  'flex items-center justify-center w-7 h-7 rounded-full shrink-0 icon-orb',
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
      <motion.section variants={itemVariants} aria-labelledby="student-activities">
        <h3
          id="student-activities"
          className={cn(
            'text-lg font-semibold text-[var(--color-primary)] mb-4',
            'flex items-center gap-2'
          )}
        >
          <div
            className="flex items-center justify-center w-8 h-8 icon-orb shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
            aria-hidden="true"
          >
            <span className="text-white"><ActivityIcon /></span>
          </div>
          {t('activities')}
        </h3>
        <div className="space-y-4">
          {plan.activities.map((activity, i) => (
            <div
              key={i}
              className="gradient-border-glass rounded-2xl glass card-hover p-5"
            >
              <div className="flex items-center gap-3 mb-2">
                <span
                  className={cn(
                    'flex items-center justify-center w-8 h-8',
                    'rounded-lg text-sm font-bold icon-orb text-white'
                  )}
                  style={{ background: 'linear-gradient(135deg, var(--color-secondary), var(--color-primary))' }}
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
                <span className="glass rounded-full px-3 py-1 flex items-center gap-1.5">
                  <ClockIcon />
                  <span>{t('duration', { minutes: activity.duration_minutes })}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </motion.section>
    </motion.article>
  )
}

function TargetIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}

function ActivityIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
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
