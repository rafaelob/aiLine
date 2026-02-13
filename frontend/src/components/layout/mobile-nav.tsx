'use client'

import { useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/cn'

interface MobileNavItem {
  key: string
  href: string
  icon: React.ReactNode
}

/**
 * Bottom navigation bar for mobile viewports (< md breakpoint).
 * Renders 5 main navigation items with active state highlighting.
 * Hidden on desktop where the sidebar is visible.
 */
export function MobileNav() {
  const t = useTranslations('nav')
  const pathname = usePathname()

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  const navItems: MobileNavItem[] = [
    { key: 'dashboard', href: '', icon: <MobileDashboardIcon /> },
    { key: 'plans', href: '/plans', icon: <MobilePlansIcon /> },
    { key: 'materials', href: '/materials', icon: <MobileMaterialsIcon /> },
    { key: 'tutors', href: '/tutors', icon: <MobileTutorsIcon /> },
    { key: 'settings', href: '/settings', icon: <MobileSettingsIcon /> },
  ]

  function isActive(href: string): boolean {
    const fullPath = `${localePrefix}${href}`
    if (href === '') {
      return pathname === localePrefix || pathname === `${localePrefix}/`
    }
    return pathname.startsWith(fullPath)
  }

  return (
    <nav
      role="navigation"
      aria-label={t('mobile_nav_label')}
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50 md:hidden',
        'border-t border-[var(--color-border)]',
        'bg-[var(--color-surface)]',
        'safe-area-bottom'
      )}
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      <ul role="list" className="flex items-stretch justify-around">
        {navItems.map((item) => {
          const active = isActive(item.href)
          return (
            <li key={item.key} className="flex-1">
              <a
                href={`${localePrefix}${item.href}`}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'flex flex-col items-center gap-1 py-2 px-1',
                  'text-xs font-medium transition-colors',
                  active
                    ? 'text-[var(--color-primary)]'
                    : 'text-[var(--color-muted)]'
                )}
              >
                <span
                  className={cn(
                    'flex items-center justify-center w-6 h-6',
                    active && 'scale-110'
                  )}
                  aria-hidden="true"
                >
                  {item.icon}
                </span>
                <span>{t(item.key)}</span>
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

/* ===== Compact Mobile Icons (20x20) ===== */

function MobileDashboardIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  )
}

function MobilePlansIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function MobileMaterialsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}

function MobileTutorsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function MobileSettingsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}
