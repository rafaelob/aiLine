'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, LayoutGroup, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'

interface MobileNavItem {
  key: string
  href: string
  icon: React.ReactNode
}

/**
 * Bottom navigation bar for mobile viewports (< md breakpoint).
 * Glass effect with pill-style active state and accessible touch targets.
 * Hidden on desktop where the sidebar is visible.
 *
 * Primary items (5) are shown directly; overflow items (Sign Language,
 * Observability) are accessible via a "More" popover menu to keep the
 * bottom bar uncluttered per mobile UX best practices.
 */
export function MobileNav() {
  const t = useTranslations('nav')
  const pathname = usePathname()
  const [moreOpen, setMoreOpen] = useState(false)
  const moreRef = useRef<HTMLLIElement>(null)

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : ''

  /** Primary items shown directly in the bottom bar. */
  const primaryItems: MobileNavItem[] = [
    { key: 'dashboard', href: '/dashboard', icon: <MobileDashboardIcon /> },
    { key: 'plans', href: '/plans', icon: <MobilePlansIcon /> },
    { key: 'tutors', href: '/tutors', icon: <MobileTutorsIcon /> },
    { key: 'progress', href: '/progress', icon: <MobileProgressIcon /> },
  ]

  /** Overflow items revealed by the More menu. */
  const overflowItems: MobileNavItem[] = [
    { key: 'materials', href: '/materials', icon: <MobileMaterialsIcon /> },
    { key: 'sign_language', href: '/sign-language', icon: <MobileSignLanguageIcon /> },
    { key: 'observability', href: '/observability', icon: <MobileObservabilityIcon /> },
    { key: 'settings', href: '/settings', icon: <MobileSettingsIcon /> },
  ]

  function isActive(href: string): boolean {
    const fullPath = `${localePrefix}${href}`
    if (href === '/dashboard') {
      return pathname === `${localePrefix}/dashboard` || pathname === `${localePrefix}/dashboard/`
    }
    return pathname.startsWith(fullPath)
  }

  /** Whether any overflow item is currently active. */
  const overflowActive = overflowItems.some((item) => isActive(item.href))

  /** Close overflow menu when clicking outside. */
  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
      setMoreOpen(false)
    }
  }, [])

  useEffect(() => {
    if (moreOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [moreOpen, handleClickOutside])

  /** Close overflow menu on Escape key. */
  useEffect(() => {
    if (!moreOpen) return
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setMoreOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [moreOpen])

  return (
    <nav
      aria-label={t('mobile_nav_label')}
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50 md:hidden',
        'border-t border-[var(--color-border)]/50',
        'backdrop-blur-xl bg-[var(--color-bg)]/80'
      )}
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      <LayoutGroup>
        <ul role="list" className="flex items-stretch justify-around">
          {/* Primary nav items */}
          {primaryItems.map((item) => {
            const active = isActive(item.href)
            return (
              <li key={item.key} className="flex-1">
                <Link
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed paths
                  href={`${localePrefix}${item.href}` as any}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'relative flex flex-col items-center gap-1 py-3 px-1',
                    'text-[10px] font-semibold transition-colors duration-200',
                    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
                    'btn-press',
                    active
                      ? 'text-[var(--color-primary)]'
                      : 'text-[var(--color-muted)]'
                  )}
                >
                  {active && (
                    <motion.div
                      layoutId="mobile-active-pill"
                      className="absolute inset-0 rounded-full bg-[var(--color-primary)]/10"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                  <motion.span
                    animate={{ scale: active ? 1.15 : 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="relative z-10 flex items-center justify-center w-10 h-7 rounded-full"
                    aria-hidden="true"
                  >
                    {item.icon}
                  </motion.span>
                  <span className="relative z-10">{t(item.key)}</span>
                </Link>
              </li>
            )
          })}

          {/* More overflow trigger */}
          <li ref={moreRef} className="flex-1 relative">
            <button
              type="button"
              onClick={() => setMoreOpen((prev) => !prev)}
              aria-expanded={moreOpen}
              aria-haspopup="true"
              aria-label={t('more_menu_label')}
              className={cn(
                'relative flex flex-col items-center gap-1 py-3 px-1 w-full',
                'text-[10px] font-semibold transition-colors duration-200',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-primary)]',
                'btn-press',
                overflowActive || moreOpen
                  ? 'text-[var(--color-primary)]'
                  : 'text-[var(--color-muted)]'
              )}
            >
              {(overflowActive && !moreOpen) && (
                <motion.div
                  layoutId="mobile-active-pill"
                  className="absolute inset-0 rounded-full bg-[var(--color-primary)]/10"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <span
                className="relative z-10 flex items-center justify-center w-10 h-7 rounded-full"
                aria-hidden="true"
              >
                <MobileMoreIcon />
              </span>
              <span className="relative z-10">{t('more')}</span>
            </button>

            {/* Overflow popover menu */}
            <AnimatePresence>
              {moreOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.95 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  role="menu"
                  aria-label={t('more_menu_label')}
                  className={cn(
                    'absolute bottom-full right-0 mb-2 w-48',
                    'rounded-xl border border-[var(--color-border)]',
                    'bg-[var(--color-surface)] shadow-[var(--shadow-lg)]',
                    'backdrop-blur-xl overflow-hidden z-50'
                  )}
                >
                  {overflowItems.map((item) => {
                    const active = isActive(item.href)
                    return (
                      <Link
                        key={item.key}
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed paths
                        href={`${localePrefix}${item.href}` as any}
                        role="menuitem"
                        aria-current={active ? 'page' : undefined}
                        onClick={() => setMoreOpen(false)}
                        className={cn(
                          'flex items-center gap-3 px-4 py-3',
                          'text-sm font-medium transition-colors duration-150',
                          'focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--color-primary)]',
                          active
                            ? 'text-[var(--color-primary)] bg-[var(--color-primary)]/5'
                            : 'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
                        )}
                      >
                        <span className="w-5 h-5 shrink-0" aria-hidden="true">
                          {item.icon}
                        </span>
                        <span>{t(item.key)}</span>
                      </Link>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </li>
        </ul>
      </LayoutGroup>
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

function MobileProgressIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  )
}

function MobileSignLanguageIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 11V6a2 2 0 0 0-4 0v1" />
      <path d="M14 10V4a2 2 0 0 0-4 0v2" />
      <path d="M10 10.5V6a2 2 0 0 0-4 0v8" />
      <path d="M18 8a2 2 0 0 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.9-5.9-2.4L3.3 16.8a2 2 0 0 1 2.8-2.8L8 16" />
    </svg>
  )
}

function MobileObservabilityIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
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

function MobileMoreIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="5" r="1.5" fill="currentColor" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
      <circle cx="12" cy="19" r="1.5" fill="currentColor" />
    </svg>
  )
}
