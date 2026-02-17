'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { DEMO_TRACES, DEMO_STUDENT_COUNT } from '@/lib/demo-data'
import { useDemoStore } from '@/stores/demo-store'
import { API_BASE, getAuthHeaders } from '@/lib/api'
import { AnimatedCounter } from '@/components/shared/animated-counter'
import {
  StatPlansIcon,
  StatStudentsIcon,
  StatScoreIcon,
  PlanIcon,
  UploadIcon,
  TutorIcon,
  ArrowRightIcon,
  PlayIcon,
} from './dashboard-icons'
import { PlanHistoryCard, type TraceRecord } from './plan-history-card'

/** Showcase plans displayed when the dashboard has no real data. */
const SHOWCASE_PLANS = [
  {
    title: 'Calculus for Visual Learners',
    icon: '\u{1F4D0}',
    color: 'var(--color-primary)',
    badges: ['Low Vision', 'Visual Schedule', 'Large Print'],
    score: 94,
    model: 'Claude Opus 4.6',
  },
  {
    title: 'Brazilian History for ADHD',
    icon: '\u{1F3AF}',
    color: 'var(--color-warning)',
    badges: ['ADHD', 'Focus Mode', 'Chunked Content'],
    score: 91,
    model: 'GPT-5.2',
  },
  {
    title: 'Science for Hearing Impaired',
    icon: '\u{1F91F}',
    color: 'var(--color-secondary)',
    badges: ['Sign Language', 'Captions', 'Visual Cues'],
    score: 96,
    model: 'Gemini 3 Pro',
  },
] as const

/**
 * Dashboard content with mesh gradient hero, glass stat cards with rotating
 * gradient borders, spotlight quick-action cards, and premium empty state.
 * Bento Grid layout: 12-col desktop, single-col mobile.
 */
export function DashboardContent() {
  const t = useTranslations('dashboard')
  const pathname = usePathname()
  const [spotlightPos, setSpotlightPos] = useState<Record<string, { x: number; y: number }>>({})
  const { dismissed, dismiss, isApiOffline, setApiOffline } = useDemoStore()

  /* ===== Live data fetch ===== */
  const [traces, setTraces] = useState<TraceRecord[]>([])
  const [studentCount, setStudentCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function fetchData() {
      try {
        const [tracesRes, progressRes] = await Promise.all([
          fetch(`${API_BASE}/traces/recent`, { headers: getAuthHeaders() }),
          fetch(`${API_BASE}/progress/dashboard`, { headers: getAuthHeaders() }),
        ])
        if (!cancelled && tracesRes.ok) {
          const data = await tracesRes.json()
          setTraces(data)
        }
        if (!cancelled && progressRes.ok) {
          const prog = await progressRes.json()
          setStudentCount(prog.students?.length ?? 0)
        }
      } catch {
        if (!cancelled) {
          setTraces([...DEMO_TRACES] as TraceRecord[])
          setStudentCount(DEMO_STUDENT_COUNT)
          setApiOffline(true)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once on mount; setters are stable
  }, [])

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  /* ===== Derived stats ===== */
  const planCount = traces.length
  const scoredTraces = traces.filter((tr) => tr.final_score !== null)
  const avgScore =
    scoredTraces.length > 0
      ? Math.round(
          scoredTraces.reduce((sum, tr) => sum + (tr.final_score ?? 0), 0) /
            scoredTraces.length
        )
      : null

  const stats = [
    { key: 'stat_plans', numericValue: planCount, suffix: '', icon: <StatPlansIcon />, color: 'var(--color-primary)' },
    { key: 'stat_students', numericValue: studentCount, suffix: '', icon: <StatStudentsIcon />, color: 'var(--color-secondary)' },
    { key: 'stat_score', numericValue: avgScore, suffix: '', icon: <StatScoreIcon />, color: 'var(--color-success)' },
  ]

  const quickActions = [
    { key: 'create_plan', href: `${localePrefix}/plans`, icon: <PlanIcon />, color: 'var(--color-primary)' },
    { key: 'upload_material', href: `${localePrefix}/materials`, icon: <UploadIcon />, color: 'var(--color-secondary)' },
    { key: 'start_tutor', href: `${localePrefix}/tutors`, icon: <TutorIcon />, color: 'var(--color-success)' },
  ]

  const recentTraces = traces.slice(0, 6)

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      {/* API offline demo mode banner */}
      {isApiOffline && (
        <motion.div variants={itemVariants} className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-xs text-[var(--color-muted)]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="shrink-0">
            <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
          </svg>
          <span className="truncate">{t('demo_mode')}</span>
        </motion.div>
      )}

      {/* Demo banner */}
      {!dismissed && (
        <motion.div
          variants={itemVariants}
          className={cn(
            'relative overflow-hidden gradient-border-glass rounded-2xl p-4 sm:p-5',
            'flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4',
          )}
        >
          <div
            className="icon-orb flex items-center justify-center w-12 h-12 shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))' }}
            aria-hidden="true"
          >
            <PlayIcon />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--color-text)]">{t('demo.title')}</p>
            <p className="text-xs text-[var(--color-muted)] mt-0.5">{t('demo.description')}</p>
          </div>
          <a
            href={`${localePrefix}/plans?demo=true`}
            className={cn(
              'shrink-0 px-4 py-2.5 rounded-xl btn-shimmer btn-press',
              'text-sm font-semibold text-[var(--color-on-primary)]',
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            {t('demo.start')}
          </a>
          <button
            type="button"
            onClick={() => dismiss()}
            className="absolute top-2 right-2 p-1 text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors"
            aria-label={t('demo.dismiss')}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <path d="M3 3l8 8M11 3l-8 8" />
            </svg>
          </button>
        </motion.div>
      )}

      {/* Hero welcome section — mesh gradient with noise grain */}
      <motion.section
        variants={itemVariants}
        className={cn(
          'relative overflow-hidden rounded-2xl p-8 md:p-10',
          'text-[var(--color-on-primary)]',
          'mesh-gradient-hero hero-noise'
        )}
        style={{ backgroundColor: 'var(--color-primary)' }}
        aria-labelledby="welcome-heading"
      >
        {/* Decorative floating shapes */}
        <div
          className="absolute -top-16 -right-16 w-56 h-56 rounded-full opacity-10 animate-float-slow"
          style={{ background: 'rgba(255,255,255,0.3)' }}
          aria-hidden="true"
        />
        <div
          className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full opacity-10 animate-float-medium"
          style={{ background: 'rgba(255,255,255,0.25)' }}
          aria-hidden="true"
        />
        <div
          className="absolute top-1/2 right-1/4 w-24 h-24 rounded-full opacity-5 animate-float-slow"
          style={{ background: 'rgba(255,255,255,0.4)', animationDelay: '-3s' }}
          aria-hidden="true"
        />

        <div className="relative z-10">
          <h1
            id="welcome-heading"
            className="text-2xl md:text-3xl font-bold"
          >
            {t('title')}
          </h1>
          <p className="mt-2 text-base opacity-90 max-w-lg">
            {t('subtitle')}
          </p>
        </div>
      </motion.section>

      {/* Stats row — rotating gradient border glass cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.key}
            className="gradient-border-glass rounded-2xl glass p-5 flex items-center gap-4 card-hover group relative overflow-hidden"
          >
            <div
              className="flex items-center justify-center w-12 h-12 icon-orb shrink-0"
              style={{ background: `linear-gradient(135deg, ${stat.color}, var(--color-secondary))` }}
              aria-hidden="true"
            >
              <span className="text-white">{stat.icon}</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-text)]">
                {stat.numericValue !== null ? (
                  <AnimatedCounter value={stat.numericValue} suffix={stat.suffix} />
                ) : (
                  '--'
                )}
              </p>
              <p className="text-xs text-[var(--color-muted)]">{t(stat.key)}</p>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Quick actions — spotlight effect on hover */}
      <motion.section variants={itemVariants} aria-labelledby="quick-actions-heading">
        <h2 id="quick-actions-heading" className="text-sm font-semibold text-[var(--color-text)] mb-3">
          {t('quick_actions')}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <a
              key={action.key}
              href={action.href}
              className={cn(
                'group relative overflow-hidden flex items-center gap-4 p-5',
                'rounded-xl glass card-hover'
              )}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                setSpotlightPos((prev) => ({
                  ...prev,
                  [action.key]: { x: e.clientX - rect.left, y: e.clientY - rect.top },
                }))
              }}
            >
              {/* Spotlight overlay */}
              <div
                className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{
                  background: spotlightPos[action.key]
                    ? `radial-gradient(400px circle at ${spotlightPos[action.key].x}px ${spotlightPos[action.key].y}px, color-mix(in srgb, var(--color-primary) 8%, transparent), transparent 40%)`
                    : undefined,
                }}
                aria-hidden="true"
              />
              <div
                className="flex items-center justify-center w-12 h-12 icon-orb shrink-0 group-hover:scale-110 transition-transform duration-300"
                style={{ background: `linear-gradient(135deg, ${action.color}, var(--color-secondary))` }}
                aria-hidden="true"
              >
                <span className="text-white">{action.icon}</span>
              </div>
              <div className="min-w-0 flex-1">
                <span className="font-medium text-sm text-[var(--color-text)]">{t(action.key)}</span>
                <span className="block text-xs text-[var(--color-muted)] mt-0.5">{t(`${action.key}_hint`)}</span>
              </div>
              <ArrowRightIcon className="shrink-0 text-[var(--color-muted)] group-hover:text-[var(--color-text)] group-hover:translate-x-1 transition-all duration-300" />
            </a>
          ))}
        </div>
      </motion.section>

      {/* Recent plans — live data or empty state */}
      <motion.section variants={itemVariants} aria-labelledby="recent-plans-heading">
        <div className="flex items-center justify-between mb-3">
          <h2 id="recent-plans-heading" className="text-sm font-semibold text-[var(--color-text)]">
            {t('recent_plans')}
          </h2>
          <a
            href={`${localePrefix}/plans`}
            className={cn('text-sm text-[var(--color-primary)]', 'hover:underline underline-offset-4')}
          >
            {t('view_all')}
          </a>
        </div>

        {loading ? (
          /* Loading skeleton */
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" data-testid="loading-skeleton">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="animate-pulse glass rounded-2xl h-24"
                aria-hidden="true"
              />
            ))}
          </div>
        ) : recentTraces.length > 0 ? (
          /* Plan history cards */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="plan-history-grid">
            {recentTraces.map((trace) => (
              <motion.div key={trace.run_id} variants={itemVariants}>
                <PlanHistoryCard trace={trace} localePrefix={localePrefix} t={t} />
              </motion.div>
            ))}
          </div>
        ) : (
          /* Showcase cards when no real plans exist */
          <div className="relative">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 opacity-60">
              {SHOWCASE_PLANS.map((plan) => (
                <div
                  key={plan.title}
                  className="rounded-2xl glass p-5 flex flex-col gap-3"
                  aria-hidden="true"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm shrink-0"
                      style={{ background: plan.color }}
                    >
                      {plan.icon}
                    </div>
                    <span className="text-sm font-semibold text-[var(--color-text)] truncate">
                      {plan.title}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {plan.badges.map((badge) => (
                      <span
                        key={badge}
                        className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-surface-elevated)] text-[var(--color-muted)] border border-[var(--color-border)]"
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 mt-auto">
                    <span className="text-xs text-[var(--color-success)] font-medium">{t('plan_score')}: {plan.score}</span>
                    <span className="text-xs text-[var(--color-muted)]">{plan.model}</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Overlay CTA */}
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--color-bg)]/60 rounded-2xl backdrop-blur-[2px]">
              <p className="text-sm font-semibold text-[var(--color-text)]">{t('no_plans')}</p>
              <p className="mt-1 text-xs text-[var(--color-muted)]">{t('empty_hint')}</p>
              <a
                href={`${localePrefix}/plans`}
                className={cn(
                  'mt-4 inline-flex items-center gap-2 px-6 py-3',
                  'rounded-xl btn-shimmer btn-press',
                  'text-sm font-semibold',
                  'text-[var(--color-on-primary)]',
                  'shadow-[var(--shadow-md)]',
                  'hover:shadow-[var(--shadow-lg)] hover:scale-[1.02]',
                  'transition-all duration-300'
                )}
                style={{ background: 'var(--gradient-hero)' }}
              >
                {t('empty_cta')}
              </a>
            </div>
          </div>
        )}
      </motion.section>
    </motion.div>
  )
}
