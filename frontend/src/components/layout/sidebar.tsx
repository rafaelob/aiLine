'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'

interface NavItem {
  key: string
  href: string
  icon: React.ReactNode
}

/**
 * Sidebar navigation with smooth collapse animation.
 * Active route is highlighted. Keyboard accessible with proper ARIA.
 */
export function Sidebar() {
  const t = useTranslations('nav')
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const navItems: NavItem[] = [
    {
      key: 'dashboard',
      href: '',
      icon: <DashboardIcon />,
    },
    {
      key: 'plans',
      href: '/plans',
      icon: <PlansIcon />,
    },
    {
      key: 'materials',
      href: '/materials',
      icon: <MaterialsIcon />,
    },
    {
      key: 'tutors',
      href: '/tutors',
      icon: <TutorsIcon />,
    },
    {
      key: 'settings',
      href: '/settings',
      icon: <SettingsIcon />,
    },
  ]

  // Extract locale from pathname (e.g., /pt-BR/plans -> pt-BR)
  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  function isActive(href: string): boolean {
    const fullPath = `${localePrefix}${href}`
    if (href === '') {
      return pathname === localePrefix || pathname === `${localePrefix}/`
    }
    return pathname.startsWith(fullPath)
  }

  return (
    <motion.aside
      role="navigation"
      aria-label={t('main_nav_label')}
      initial={false}
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={cn(
        'flex h-screen flex-col border-r',
        'bg-[var(--color-surface)] border-[var(--color-border)]'
      )}
    >
      {/* Logo area */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-[var(--color-border)]">
        <div
          className={cn(
            'flex items-center justify-center rounded-[var(--radius-md)]',
            'h-10 w-10 bg-[var(--color-primary)] text-[var(--color-on-primary)]',
            'font-bold text-lg shrink-0'
          )}
          aria-hidden="true"
        >
          A
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              className="text-lg font-bold text-[var(--color-text)] whitespace-nowrap"
            >
              AiLine
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 py-4">
        <ul role="list" className="space-y-1 px-2">
          {navItems.map((item) => {
            const active = isActive(item.href)
            return (
              <li key={item.key}>
                <a
                  href={`${localePrefix}${item.href}`}
                  aria-current={active ? 'page' : undefined}
                  title={collapsed ? t(item.key) : undefined}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-[var(--radius-md)]',
                    'transition-colors',
                    'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]',
                    active && 'bg-[var(--color-primary)] text-[var(--color-on-primary)] hover:bg-[var(--color-primary-hover)]'
                  )}
                  style={{ transitionDuration: 'var(--transition-fast)' }}
                >
                  <span className="shrink-0 w-6 h-6" aria-hidden="true">
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
                </a>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-[var(--color-border)] p-3">
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? t('expand') : t('collapse')}
          className={cn(
            'flex items-center justify-center w-full py-2',
            'rounded-[var(--radius-md)] transition-colors',
            'text-[var(--color-muted)] hover:bg-[var(--color-surface-elevated)]'
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

function SettingsIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}
