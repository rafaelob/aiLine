'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence, LayoutGroup } from 'motion/react'
import { cn } from '@/lib/cn'

interface NavItem {
  key: string
  href: string
  icon: React.ReactNode
}

/**
 * Floating Shell sidebar with glass effect, accent bar active indicator,
 * hover glow, tooltips, and smooth collapse animation. WCAG AAA accessible.
 */
export function Sidebar() {
  const t = useTranslations('nav')
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const navItems: NavItem[] = [
    { key: 'dashboard', href: '/dashboard', icon: <DashboardIcon /> },
    { key: 'plans', href: '/plans', icon: <PlansIcon /> },
    { key: 'materials', href: '/materials', icon: <MaterialsIcon /> },
    { key: 'tutors', href: '/tutors', icon: <TutorsIcon /> },
    { key: 'sign_language', href: '/sign-language', icon: <SignLanguageIcon /> },
    { key: 'progress', href: '/progress', icon: <ProgressIcon /> },
    { key: 'observability', href: '/observability', icon: <ObservabilityIcon /> },
    { key: 'settings', href: '/settings', icon: <SettingsIcon /> },
  ]

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  function isActive(href: string): boolean {
    const fullPath = `${localePrefix}${href}`
    if (href === '/dashboard') {
      return pathname === `${localePrefix}/dashboard` || pathname === `${localePrefix}/dashboard/`
    }
    return pathname.startsWith(fullPath)
  }

  return (
    <motion.aside
      role="navigation"
      aria-label={t('main_nav_label')}
      initial={false}
      animate={{ width: collapsed ? 76 : 264 }}
      transition={{ type: 'spring', stiffness: 250, damping: 25, mass: 0.8 }}
      className={cn(
        'flex flex-col h-[calc(100vh-24px)] m-3 rounded-2xl',
        'glass shadow-[var(--shadow-lg)]'
      )}
    >
      {/* Logo area with shimmer on hover */}
      <div className="group flex items-center gap-3 px-4 py-5">
        <div
          className="flex items-center justify-center w-10 h-10 rounded-xl text-white font-bold text-lg shrink-0"
          style={{
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
            boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.3), 0 4px 12px color-mix(in srgb, var(--color-primary) 40%, transparent)',
          }}
          aria-hidden="true"
        >
          A
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="flex flex-col min-w-0"
            >
              <span className="text-xl font-bold tracking-tight gradient-text-animated">
                AiLine
              </span>
              <span className="text-[10px] text-[var(--color-muted)] -mt-0.5 whitespace-nowrap">
                Adaptive Inclusive Learning
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 py-2 overflow-y-auto">
        <LayoutGroup>
          <ul role="list" className="space-y-1 px-3">
            {navItems.map((item) => {
              const active = isActive(item.href)
              return (
                <li key={item.key}>
                  <Link
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed paths
                    href={`${localePrefix}${item.href}` as any}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'group/item relative flex items-center gap-3 px-3 py-2.5 rounded-xl overflow-hidden',
                      'transition-all duration-200',
                      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
                      active
                        ? 'text-[var(--color-primary)] bg-[var(--color-primary)]/5'
                        : 'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)] hover:shadow-[var(--shadow-sm)]'
                    )}
                  >
                    {/* Hover gradient overlay */}
                    <div
                      className="absolute inset-0 rounded-xl opacity-0 group-hover/item:opacity-100 transition-opacity duration-300 pointer-events-none"
                      style={{ background: 'radial-gradient(circle at 50% 50%, color-mix(in srgb, var(--color-primary) 5%, transparent), transparent 70%)' }}
                      aria-hidden="true"
                    />
                    {/* Animated active accent bar */}
                    {active && (
                      <motion.div
                        layoutId="sidebar-active-indicator"
                        className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-[var(--color-primary)]"
                        style={{ boxShadow: '0 0 16px 2px var(--color-primary)' }}
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                      />
                    )}
                    <span
                      className={cn(
                        'shrink-0 w-6 h-6 rounded-md transition-colors',
                        'group-hover/item:bg-[var(--color-primary)]/5'
                      )}
                      aria-hidden="true"
                    >
                      {item.icon}
                    </span>
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="whitespace-nowrap text-sm font-medium"
                        >
                          {t(item.key)}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {/* Tooltip when collapsed */}
                    {collapsed && (
                      <span
                        role="tooltip"
                        className={cn(
                          'absolute left-full ml-2 px-2 py-1 rounded-md',
                          'bg-[var(--color-surface-elevated)] text-xs font-medium',
                          'shadow-[var(--shadow-md)] border border-[var(--color-border)]',
                          'opacity-0 group-hover/item:opacity-100 transition-opacity',
                          'pointer-events-none whitespace-nowrap z-50'
                        )}
                      >
                        {t(item.key)}
                      </span>
                    )}
                  </Link>
                </li>
              )
            })}
          </ul>
        </LayoutGroup>
      </nav>

      {/* Subtle divider */}
      <div className="h-px mx-4 my-2 bg-gradient-to-r from-transparent via-[var(--color-border)] to-transparent" aria-hidden="true" />

      {/* Powered by badge */}
      <div className="px-3 py-2">
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className={cn(
                'flex items-center gap-2.5 px-3 py-1.5',
                'rounded-xl border border-[var(--color-border)]/40'
              )}
            >
              <div
                className="w-5 h-5 rounded-md shrink-0"
                style={{ background: 'linear-gradient(135deg, #CC785C, #D4A574)' }}
                aria-hidden="true"
              />
              <span className="text-[9px] text-[var(--color-muted)]/70 leading-tight">
                Powered by<br />Claude Opus 4.6
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Collapse toggle */}
      <div className="px-3 pb-3">
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? t('expand') : t('collapse')}
          className={cn(
            'flex items-center justify-center w-full py-2.5',
            'rounded-xl transition-all duration-200',
            'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
            'text-[var(--color-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]'
          )}
        >
          <motion.svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
            animate={{ rotate: collapsed ? 180 : 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            <path
              d="M12.5 15L7.5 10L12.5 5"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </motion.svg>
        </button>
      </div>
    </motion.aside>
  )
}

/* ===== Icon Components ===== */

function DashboardIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  )
}

function PlansIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  )
}

function MaterialsIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}

function TutorsIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  )
}

function SignLanguageIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 11V6a2 2 0 0 0-4 0v1" />
      <path d="M14 10V4a2 2 0 0 0-4 0v2" />
      <path d="M10 10.5V6a2 2 0 0 0-4 0v8" />
      <path d="M18 8a2 2 0 0 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-5.9-2.4L3.3 16.8a2 2 0 0 1 2.8-2.8L8 16" />
    </svg>
  )
}

function ProgressIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  )
}

function ObservabilityIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  )
}

function SettingsIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}
