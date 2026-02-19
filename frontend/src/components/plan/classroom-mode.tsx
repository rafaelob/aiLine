'use client'

import { useState, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

interface ClassroomModeProps {
  /** Optional CSS class. */
  className?: string
}

interface StudentProfile {
  id: string
  nameKey: string
  profileKey: string
  adaptationKey: string
  snippetKey: string
  accent: string
  accentBg: string
  icon: React.ReactNode
  badges: string[]
}

const STUDENTS: StudentProfile[] = [
  {
    id: 'lucas',
    nameKey: 'student_lucas',
    profileKey: 'student_lucas_profile',
    adaptationKey: 'student_lucas_adaptation',
    snippetKey: 'student_lucas_snippet',
    accent: 'rgb(59, 130, 246)',
    accentBg: 'rgb(59, 130, 246, 0.1)',
    icon: <CalendarIcon />,
    badges: ['badge_visual_schedule', 'badge_calm_colors', 'badge_predictable'],
  },
  {
    id: 'sofia',
    nameKey: 'student_sofia',
    profileKey: 'student_sofia_profile',
    adaptationKey: 'student_sofia_adaptation',
    snippetKey: 'student_sofia_snippet',
    accent: 'rgb(249, 115, 22)',
    accentBg: 'rgb(249, 115, 22, 0.1)',
    icon: <TimerIcon />,
    badges: ['badge_timer', 'badge_focus_mode', 'badge_chunked'],
  },
  {
    id: 'pedro',
    nameKey: 'student_pedro',
    profileKey: 'student_pedro_profile',
    adaptationKey: 'student_pedro_adaptation',
    snippetKey: 'student_pedro_snippet',
    accent: 'rgb(34, 197, 94)',
    accentBg: 'rgb(34, 197, 94, 0.1)',
    icon: <TextIcon />,
    badges: ['badge_bionic_reading', 'badge_warm_tones', 'badge_wide_spacing'],
  },
  {
    id: 'ana',
    nameKey: 'student_ana',
    profileKey: 'student_ana_profile',
    adaptationKey: 'student_ana_adaptation',
    snippetKey: 'student_ana_snippet',
    accent: 'rgb(168, 85, 247)',
    accentBg: 'rgb(168, 85, 247, 0.1)',
    icon: <SignLanguageIcon />,
    badges: ['badge_sign_language', 'badge_captions', 'badge_visual_cues'],
  },
]

/**
 * Inclusive Classroom Mode — teacher cockpit view showing how one lesson
 * plan adapts simultaneously for 4 student profiles with different
 * accessibility needs. Uses a responsive 2x2 grid layout.
 */
export function ClassroomMode({ className }: ClassroomModeProps) {
  const t = useTranslations('classroom')
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  const cards = useMemo(
    () =>
      STUDENTS.map((student) => ({
        ...student,
        name: t(student.nameKey),
        profile: t(student.profileKey),
        adaptation: t(student.adaptationKey),
        snippet: t(student.snippetKey),
        badgeLabels: student.badges.map((b) => t(b)),
      })),
    [t],
  )

  return (
    <section
      className={cn('flex flex-col gap-6', className)}
      aria-label={t('title')}
    >
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-[var(--color-text)]">
          {t('subtitle')}
        </h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {t('description')}
        </p>
      </div>

      {/* 2x2 Grid */}
      <div
        className="grid gap-4 md:grid-cols-2"
        role="list"
        aria-label={t('title')}
      >
        {cards.map((card, i) => (
          <motion.article
            key={card.id}
            role="listitem"
            className={cn(
              'relative flex flex-col gap-3 rounded-xl p-4',
              'border-2 transition-shadow',
              'bg-[var(--color-surface-elevated)]',
              'hover:shadow-lg',
              'focus-within:ring-2 focus-within:ring-[var(--color-primary)]',
            )}
            style={{
              borderColor: card.accent,
            }}
            initial={noMotion ? undefined : { opacity: 0, y: 16 }}
            animate={noMotion ? undefined : { opacity: 1, y: 0 }}
            transition={
              noMotion
                ? undefined
                : { delay: i * 0.1, type: 'spring', stiffness: 300, damping: 25 }
            }
          >
            {/* Card header */}
            <div className="flex items-center gap-3">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                style={{ backgroundColor: card.accentBg, color: card.accent }}
                aria-hidden="true"
              >
                {card.icon}
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-[var(--color-text)]">
                  {card.name}
                </h3>
                <span
                  className="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{ backgroundColor: card.accentBg, color: card.accent }}
                >
                  {card.profile}
                </span>
              </div>
            </div>

            {/* Key adaptation */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                {t('card_adaptation')}
              </h4>
              <p className="mt-0.5 text-sm text-[var(--color-text)]">
                {card.adaptation}
              </p>
            </div>

            {/* Plan snippet (expandable) */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                {t('card_snippet')}
              </h4>
              <button
                type="button"
                onClick={() =>
                  setExpandedCard(expandedCard === card.id ? null : card.id)
                }
                className={cn(
                  'mt-0.5 w-full text-left text-xs leading-relaxed',
                  'text-[var(--color-text)]/80',
                  'cursor-pointer rounded-lg p-2',
                  'border border-[var(--color-border)]',
                  'bg-[var(--color-surface)]',
                  'hover:bg-[var(--color-surface-elevated)]',
                  'focus-visible:outline-2 focus-visible:outline-offset-2',
                  'focus-visible:outline-[var(--color-primary)]',
                  'transition-colors',
                )}
                aria-expanded={expandedCard === card.id}
              >
                {expandedCard === card.id ? (
                  card.snippet
                ) : (
                  <span>
                    {card.snippet.length > 120
                      ? card.snippet.slice(0, 120) + '...'
                      : card.snippet}
                  </span>
                )}
              </button>
            </div>

            {/* Accommodation badges */}
            <div
              className="flex flex-wrap gap-1.5"
              aria-label={t('card_badges_label', { name: card.name })}
            >
              {card.badgeLabels.map((badge) => (
                <span
                  key={badge}
                  className={cn(
                    'inline-flex items-center rounded-full px-2 py-0.5',
                    'text-[10px] font-medium',
                    'border border-[var(--color-border)]',
                    'text-[var(--color-text)]',
                    'bg-[var(--color-surface)]',
                  )}
                >
                  {badge}
                </span>
              ))}
            </div>

            {/* Accent top stripe */}
            <div
              className="absolute left-0 top-0 h-1 w-full rounded-t-xl"
              style={{ backgroundColor: card.accent }}
              aria-hidden="true"
            />
          </motion.article>
        ))}
      </div>
    </section>
  )
}

/* --- Icons --- */

function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  )
}

function TimerIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l2 2" />
      <path d="M5 3L2 6" />
      <path d="M22 6l-3-3" />
      <line x1="12" y1="1" x2="12" y2="3" />
    </svg>
  )
}

function TextIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="4 7 4 4 20 4 20 7" />
      <line x1="9" y1="20" x2="15" y2="20" />
      <line x1="12" y1="4" x2="12" y2="20" />
    </svg>
  )
}

function SignLanguageIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2" />
      <path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2" />
      <path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8" />
      <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15" />
    </svg>
  )
}
