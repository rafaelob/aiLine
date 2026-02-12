'use client'

import { useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { StaggerList, StaggerItem } from '@/components/ui/stagger-list'

/**
 * Dashboard content with hero welcome, stat cards, quick actions,
 * and recent plans. Premium SaaS-grade layout.
 */
export function DashboardContent() {
  const t = useTranslations('dashboard')
  const pathname = usePathname()

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  const stats = [
    {
      key: 'stat_plans',
      value: '0',
      icon: <StatPlansIcon />,
      color: 'var(--color-primary)',
    },
    {
      key: 'stat_students',
      value: '0',
      icon: <StatStudentsIcon />,
      color: 'var(--color-secondary)',
    },
    {
      key: 'stat_score',
      value: '--',
      icon: <StatScoreIcon />,
      color: 'var(--color-success)',
    },
  ]

  const quickActions = [
    {
      key: 'create_plan',
      href: `${localePrefix}/plans`,
      icon: <PlanIcon />,
      color: 'var(--color-primary)',
    },
    {
      key: 'upload_material',
      href: `${localePrefix}/materials`,
      icon: <UploadIcon />,
      color: 'var(--color-secondary)',
    },
    {
      key: 'start_tutor',
      href: `${localePrefix}/tutors`,
      icon: <TutorIcon />,
      color: 'var(--color-success)',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Hero welcome section */}
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className={cn(
          'relative overflow-hidden rounded-[var(--radius-lg)] p-8',
          'text-[var(--color-on-primary)]'
        )}
        style={{ background: 'var(--gradient-hero)' }}
        aria-labelledby="welcome-heading"
      >
        {/* Decorative circles */}
        <div
          className="absolute -top-12 -right-12 w-48 h-48 rounded-full opacity-15"
          style={{ background: 'rgba(255,255,255,0.2)' }}
          aria-hidden="true"
        />
        <div
          className="absolute -bottom-8 -left-8 w-32 h-32 rounded-full opacity-10"
          style={{ background: 'rgba(255,255,255,0.2)' }}
          aria-hidden="true"
        />

        <div className="relative z-10">
          <h1
            id="welcome-heading"
            className="text-2xl font-bold"
          >
            {t('title')}
          </h1>
          <p className="mt-2 text-base opacity-90 max-w-lg">
            {t('subtitle')}
          </p>
        </div>
      </motion.section>

      {/* Stats cards */}
      <StaggerList className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <StaggerItem key={stat.key}>
            <div
              className={cn(
                'flex items-center gap-4 p-5',
                'rounded-[var(--radius-lg)] border',
                'bg-[var(--color-surface)] border-[var(--color-border)]',
                'hover:shadow-[var(--shadow-md)] transition-shadow'
              )}
              style={{ transitionDuration: 'var(--transition-normal)' }}
            >
              <div
                className="flex items-center justify-center w-12 h-12 rounded-[var(--radius-md)]"
                style={{
                  backgroundColor: `color-mix(in srgb, ${stat.color} 12%, transparent)`,
                  color: stat.color,
                }}
                aria-hidden="true"
              >
                {stat.icon}
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--color-text)]">
                  {stat.value}
                </p>
                <p className="text-xs text-[var(--color-muted)]">
                  {t(stat.key)}
                </p>
              </div>
            </div>
          </StaggerItem>
        ))}
      </StaggerList>

      {/* Quick actions */}
      <section aria-labelledby="quick-actions-heading">
        <h2
          id="quick-actions-heading"
          className="text-lg font-semibold text-[var(--color-text)] mb-4"
        >
          {t('quick_actions')}
        </h2>
        <StaggerList className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <StaggerItem key={action.key}>
              <a
                href={action.href}
                className={cn(
                  'flex items-center gap-4 p-5',
                  'rounded-[var(--radius-lg)] border',
                  'bg-[var(--color-surface)] border-[var(--color-border)]',
                  'hover:shadow-[var(--shadow-md)]',
                  'group'
                )}
                style={{
                  transitionProperty: 'box-shadow, border-color',
                  transitionDuration: 'var(--transition-normal)',
                }}
              >
                <div
                  className={cn(
                    'flex items-center justify-center w-12 h-12',
                    'rounded-[var(--radius-md)]',
                    'group-hover:scale-105 transition-transform'
                  )}
                  style={{
                    backgroundColor: `color-mix(in srgb, ${action.color} 12%, transparent)`,
                  }}
                  aria-hidden="true"
                >
                  <span style={{ color: action.color }}>{action.icon}</span>
                </div>
                <div>
                  <span className="font-medium text-[var(--color-text)]">
                    {t(action.key)}
                  </span>
                  <span className="block text-xs text-[var(--color-muted)] mt-0.5">
                    {t(`${action.key}_hint`)}
                  </span>
                </div>
              </a>
            </StaggerItem>
          ))}
        </StaggerList>
      </section>

      {/* Recent plans */}
      <section aria-labelledby="recent-plans-heading">
        <div className="flex items-center justify-between mb-4">
          <h2
            id="recent-plans-heading"
            className="text-lg font-semibold text-[var(--color-text)]"
          >
            {t('recent_plans')}
          </h2>
          <a
            href={`${localePrefix}/plans`}
            className={cn(
              'text-sm text-[var(--color-primary)]',
              'hover:underline underline-offset-4'
            )}
          >
            {t('view_all')}
          </a>
        </div>

        {/* Empty state with onboarding hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className={cn(
            'flex flex-col items-center justify-center py-16 gap-4',
            'rounded-[var(--radius-lg)] border border-dashed',
            'border-[var(--color-border)] bg-[var(--color-surface)]'
          )}
        >
          <div
            className={cn(
              'flex items-center justify-center w-16 h-16',
              'rounded-full bg-[var(--color-surface-elevated)]'
            )}
            aria-hidden="true"
          >
            <EmptyPlansIcon />
          </div>
          <p className="text-sm text-[var(--color-muted)] text-center max-w-sm">
            {t('no_plans')}
          </p>
          <a
            href={`${localePrefix}/plans`}
            className={cn(
              'inline-flex items-center gap-2 px-5 py-2.5',
              'rounded-[var(--radius-md)]',
              'bg-[var(--color-primary)] text-[var(--color-on-primary)]',
              'text-sm font-medium',
              'hover:bg-[var(--color-primary-hover)]'
            )}
            style={{ transitionDuration: 'var(--transition-fast)' }}
          >
            {t('empty_cta')}
          </a>
        </motion.div>
      </section>
    </div>
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

function EmptyPlansIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </svg>
  )
}
