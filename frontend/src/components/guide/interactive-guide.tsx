'use client'

import { useState, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'
import { GuideRoleSection, type GuideItem } from './guide-role-section'
import {
  GettingStartedIcon,
  PipelineIcon,
  StudentProfilesIcon,
  ReviewIcon,
  MonitoringIcon,
  TutoringIcon,
  ExportIcon,
  YourTutorIcon,
  AccessibilityFeaturesIcon,
  YourProgressIcon,
  GettingHelpIcon,
  ReportsIcon,
  ChildPlanIcon,
  SupportHomeIcon,
  PrivacyIcon,
} from './guide-section-icons'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type RoleKey = 'teacher' | 'student' | 'parent'

const ROLE_KEYS: RoleKey[] = ['teacher', 'student', 'parent']

/* ------------------------------------------------------------------ */
/*  Role icons (inline, small)                                         */
/* ------------------------------------------------------------------ */

function TeacherRoleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
      <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
    </svg>
  )
}

function StudentRoleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 6 3 6 3s3 0 6-3v-5" />
    </svg>
  )
}

function ParentRoleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87" />
      <path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  )
}

const ROLE_ICONS: Record<RoleKey, React.ReactNode> = {
  teacher: <TeacherRoleIcon className="w-5 h-5" />,
  student: <StudentRoleIcon className="w-5 h-5" />,
  parent: <ParentRoleIcon className="w-5 h-5" />,
}

/* ------------------------------------------------------------------ */
/*  Build section items per role                                       */
/* ------------------------------------------------------------------ */

function useTeacherItems(t: (key: string) => string): GuideItem[] {
  return [
    { key: 'getting_started', title: t('teacher.getting_started'), description: t('teacher.getting_started_desc'), icon: <GettingStartedIcon className="w-5 h-5" /> },
    { key: 'pipeline', title: t('teacher.pipeline'), description: t('teacher.pipeline_desc'), icon: <PipelineIcon className="w-5 h-5" /> },
    { key: 'student_profiles', title: t('teacher.student_profiles'), description: t('teacher.student_profiles_desc'), icon: <StudentProfilesIcon className="w-5 h-5" /> },
    { key: 'reviewing', title: t('teacher.reviewing'), description: t('teacher.reviewing_desc'), icon: <ReviewIcon className="w-5 h-5" /> },
    { key: 'monitoring', title: t('teacher.monitoring'), description: t('teacher.monitoring_desc'), icon: <MonitoringIcon className="w-5 h-5" /> },
    { key: 'tutoring', title: t('teacher.tutoring'), description: t('teacher.tutoring_desc'), icon: <TutoringIcon className="w-5 h-5" /> },
    { key: 'exports', title: t('teacher.exports'), description: t('teacher.exports_desc'), icon: <ExportIcon className="w-5 h-5" /> },
  ]
}

function useStudentItems(t: (key: string) => string): GuideItem[] {
  return [
    { key: 'your_tutor', title: t('student.your_tutor'), description: t('student.your_tutor_desc'), icon: <YourTutorIcon className="w-5 h-5" /> },
    { key: 'a11y_features', title: t('student.a11y_features'), description: t('student.a11y_features_desc'), icon: <AccessibilityFeaturesIcon className="w-5 h-5" /> },
    { key: 'your_progress', title: t('student.your_progress'), description: t('student.your_progress_desc'), icon: <YourProgressIcon className="w-5 h-5" /> },
    { key: 'getting_help', title: t('student.getting_help'), description: t('student.getting_help_desc'), icon: <GettingHelpIcon className="w-5 h-5" /> },
  ]
}

function useParentItems(t: (key: string) => string): GuideItem[] {
  return [
    { key: 'reports', title: t('parent.reports'), description: t('parent.reports_desc'), icon: <ReportsIcon className="w-5 h-5" /> },
    { key: 'child_plan', title: t('parent.child_plan'), description: t('parent.child_plan_desc'), icon: <ChildPlanIcon className="w-5 h-5" /> },
    { key: 'support_home', title: t('parent.support_home'), description: t('parent.support_home_desc'), icon: <SupportHomeIcon className="w-5 h-5" /> },
    { key: 'privacy', title: t('parent.privacy'), description: t('parent.privacy_desc'), icon: <PrivacyIcon className="w-5 h-5" /> },
  ]
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

/**
 * Interactive guide page with role-based tabs (Teacher | Student | Parent).
 * Implements WAI-ARIA tablist pattern with keyboard navigation.
 * Uses glass morphism, gradient accents, and motion animations.
 */
export function InteractiveGuide() {
  const t = useTranslations('guide')
  const prefersReducedMotion = useReducedMotion()
  const [activeRole, setActiveRole] = useState<RoleKey>('teacher')

  const teacherItems = useTeacherItems(t)
  const studentItems = useStudentItems(t)
  const parentItems = useParentItems(t)

  const roleItems: Record<RoleKey, GuideItem[]> = {
    teacher: teacherItems,
    student: studentItems,
    parent: parentItems,
  }

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = ROLE_KEYS.indexOf(activeRole)
      let nextIndex = currentIndex
      if (e.key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % ROLE_KEYS.length
        e.preventDefault()
      } else if (e.key === 'ArrowLeft') {
        nextIndex = (currentIndex - 1 + ROLE_KEYS.length) % ROLE_KEYS.length
        e.preventDefault()
      } else if (e.key === 'Home') {
        nextIndex = 0
        e.preventDefault()
      } else if (e.key === 'End') {
        nextIndex = ROLE_KEYS.length - 1
        e.preventDefault()
      }
      if (nextIndex !== currentIndex) {
        setActiveRole(ROLE_KEYS[nextIndex])
        const el = document.getElementById(`guide-tab-${ROLE_KEYS[nextIndex]}`)
        el?.focus()
      }
    },
    [activeRole],
  )

  return (
    <section aria-label={t('page_title')}>
      {/* Header */}
      <motion.div
        className="text-center mb-10"
        initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text-animated mb-3">
          {t('page_title')}
        </h1>
        <p className="text-[var(--color-muted)] text-lg max-w-2xl mx-auto">
          {t('page_subtitle')}
        </p>
      </motion.div>

      {/* Role tabs */}
      <motion.div
        className="flex justify-center mb-8"
        initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <div
          role="tablist"
          aria-label={t('role_tabs_label')}
          onKeyDown={handleKeyDown}
          className="glass rounded-xl p-1 inline-flex gap-1"
        >
          {ROLE_KEYS.map((role) => (
            <button
              key={role}
              id={`guide-tab-${role}`}
              type="button"
              role="tab"
              aria-selected={activeRole === role}
              aria-controls={`guide-panel-${role}`}
              tabIndex={activeRole === role ? 0 : -1}
              onClick={() => setActiveRole(role)}
              className={cn(
                'relative flex items-center gap-2 px-5 py-2.5 rounded-lg',
                'text-sm font-semibold whitespace-nowrap transition-colors',
                activeRole === role
                  ? 'text-[var(--color-primary)]'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]/50',
              )}
            >
              {ROLE_ICONS[role]}
              {t(`roles.${role}`)}
              {activeRole === role && (
                <motion.span
                  layoutId="guide-active-tab"
                  className="absolute inset-0 rounded-lg glass"
                  style={{ zIndex: -1 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Tab panels */}
      {ROLE_KEYS.map((role) => (
        <div
          key={role}
          id={`guide-panel-${role}`}
          role="tabpanel"
          aria-labelledby={`guide-tab-${role}`}
          hidden={activeRole !== role}
        >
          {activeRole === role && (
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {/* Role description card */}
              <div className="glass gradient-border-glass rounded-2xl p-6 mb-6 text-center">
                <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">
                  {t(`${role}.heading`)}
                </h2>
                <p className="text-[var(--color-muted)]">
                  {t(`${role}.intro`)}
                </p>
              </div>

              {/* Accordion sections */}
              <GuideRoleSection items={roleItems[role]} />
            </motion.div>
          )}
        </div>
      ))}
    </section>
  )
}
