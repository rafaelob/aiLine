'use client'

import { useRef, useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import {
  motion,
  useMotionValue,
  animate,
  useInView,
} from 'motion/react'
import { cn } from '@/lib/cn'
import { containerVariants, itemVariants } from '@/lib/motion-variants'
import { useDemoStore } from '@/stores/demo-store'
import { API_BASE, getAuthHeaders } from '@/lib/api'

/* ===== Types ===== */

interface TraceRecord {
  run_id: string
  status: string
  total_time_ms: number
  node_count: number
  final_score: number | null
  model_used: string
  refinement_count: number
}

/* ===== Animated Counter (spring physics count-up on scroll) ===== */

function AnimatedCounter({
  value,
  suffix = '',
}: {
  value: number
  suffix?: string
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const motionValue = useMotionValue(0)
  const isInView = useInView(ref, { once: true, margin: '-10px' })

  useEffect(() => {
    if (isInView) {
      const controls = animate(motionValue, value, {
        type: 'spring',
        stiffness: 100,
        damping: 15,
        mass: 0.5,
      })
      return () => controls.stop()
    }
  }, [value, isInView, motionValue])

  useEffect(() => {
    const unsubscribe = motionValue.on('change', (latest) => {
      if (ref.current) {
        ref.current.textContent = `${Math.round(latest)}${suffix}`
      }
    })
    return unsubscribe
  }, [motionValue, suffix])

  return <span ref={ref}>{`${value}${suffix}`}</span>
}

/* ===== Stagger animation variants ===== */

/* ===== Plan History Card ===== */

function PlanHistoryCard({
  trace,
  localePrefix,
  t,
}: {
  trace: TraceRecord
  localePrefix: string
  t: ReturnType<typeof useTranslations<'dashboard'>>
}) {
  const isCompleted = trace.status === 'completed'
  const timeFormatted = `${(trace.total_time_ms / 1000).toFixed(1)}s`
  const shortId = trace.run_id.slice(0, 8)

  return (
    <a
      href={`${localePrefix}/plans`}
      className="glass card-hover rounded-xl p-4 flex flex-col gap-2 group"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-mono text-[var(--color-muted)] truncate">
          {shortId}
        </span>
        <span
          className={cn(
            'text-[10px] font-semibold px-2 py-0.5 rounded-full',
            isCompleted
              ? 'bg-[color-mix(in_srgb,var(--color-success)_15%,transparent)] text-[var(--color-success)]'
              : 'bg-[color-mix(in_srgb,var(--color-error,#ef4444)_15%,transparent)] text-[var(--color-error,#ef4444)]'
          )}
        >
          {isCompleted ? t('plan_status_completed') : t('plan_status_failed')}
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
        <span className="px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[10px] font-medium truncate max-w-[120px]">
          {trace.model_used}
        </span>
      </div>

      <div className="flex items-center justify-between mt-auto pt-1">
        <span className="text-xs text-[var(--color-muted)]">
          {t('plan_time')}: {timeFormatted}
        </span>
        {trace.final_score !== null && (
          <span className="text-xs font-semibold text-[var(--color-text)]">
            {t('plan_score')}: {trace.final_score}
          </span>
        )}
      </div>
    </a>
  )
}

/**
 * Dashboard content with mesh gradient hero, glass stat cards with rotating
 * gradient borders, spotlight quick-action cards, and premium empty state.
 * Bento Grid layout: 12-col desktop, single-col mobile.
 */
export function DashboardContent() {
  const t = useTranslations('dashboard')
  const pathname = usePathname()
  const [spotlightPos, setSpotlightPos] = useState<Record<string, { x: number; y: number }>>({})
  const { dismissed, dismiss } = useDemoStore()

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
        // Silent fallback — show 0 values
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchData()
    return () => { cancelled = true }
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
      {/* Demo banner */}
      {!dismissed && (
        <motion.div
          variants={itemVariants}
          className={cn(
            'relative overflow-hidden gradient-border-glass rounded-2xl p-5',
            'flex items-center gap-4',
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
              'shrink-0 px-4 py-2.5 rounded-xl btn-shimmer',
              'text-sm font-semibold text-[var(--color-on-primary)]',
            )}
            style={{ background: 'var(--gradient-hero)' }}
          >
            {t('demo.start')}
          </a>
          <button
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
          <motion.h1
            id="welcome-heading"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="text-2xl md:text-3xl font-bold"
          >
            {t('title')}
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="mt-2 text-base opacity-90 max-w-lg"
          >
            {t('subtitle')}
          </motion.p>
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
          /* Empty state with premium SVG illustration */
          <div
            className={cn(
              'flex flex-col items-center justify-center py-12 gap-4',
              'rounded-xl glass',
              'border border-dashed border-[var(--color-border)]'
            )}
          >
            <svg width="160" height="120" viewBox="0 0 160 120" fill="none" className="animate-float-slow" aria-hidden="true">
              {/* Document */}
              <rect x="50" y="15" width="60" height="80" rx="8" fill="var(--color-bg)" stroke="var(--color-primary)" strokeWidth="1.5" />
              <line x1="65" y1="35" x2="95" y2="35" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
              <line x1="65" y1="48" x2="95" y2="48" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
              <line x1="65" y1="61" x2="85" y2="61" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
              {/* Orbiting dots */}
              <g className="empty-state-orbit" style={{ transformOrigin: '80px 55px' }}>
                <circle cx="80" cy="5" r="4" fill="var(--color-primary)" opacity="0.6" />
              </g>
              <g className="empty-state-orbit" style={{ transformOrigin: '80px 55px', animationDuration: '8s', animationDirection: 'reverse' }}>
                <circle cx="80" cy="105" r="3" fill="var(--color-secondary)" opacity="0.5" />
              </g>
              {/* Sparkles */}
              <path d="M130 25L132 29L136 31L132 33L130 37L128 33L124 31L128 29Z" fill="var(--color-primary)" className="empty-state-pulse-scale" opacity="0.6" />
              <path d="M25 75L26 77L28 78L26 79L25 81L24 79L22 78L24 77Z" fill="var(--color-secondary)" className="empty-state-pulse-scale" style={{ animationDelay: '1s' }} opacity="0.5" />
            </svg>
            <p className="mt-4 text-sm font-medium text-[var(--color-text)]">{t('no_plans')}</p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">{t('empty_hint')}</p>
            <a
              href={`${localePrefix}/plans`}
              className={cn(
                'inline-flex items-center gap-2 px-6 py-3',
                'rounded-xl btn-shimmer',
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
        )}
      </motion.section>
    </motion.div>
  )
}

/* ===== Stat Icons ===== */

function StatPlansIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function StatStudentsIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function StatScoreIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 20V10" />
      <path d="M18 20V4" />
      <path d="M6 20v-4" />
    </svg>
  )
}

/* ===== Quick Action Icons ===== */

function PlanIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </svg>
  )
}

function UploadIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )
}

function TutorIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d="M6 3l5 5-5 5" />
    </svg>
  )
}

function PlayIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M8 5v14l11-7z" fill="white" />
    </svg>
  )
}
