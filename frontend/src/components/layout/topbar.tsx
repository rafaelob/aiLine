'use client'

import { useState, useEffect, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, LayoutGroup } from 'motion/react'
import { cn } from '@/lib/cn'
import { PreferencesPanel } from '@/components/accessibility/preferences-panel'
import type { Locale } from '@/i18n/routing'
import { API_BASE } from '@/lib/api'
import { CommandPaletteTrigger } from '@/components/shared/command-palette'

const LOCALE_LABELS: Record<Locale, string> = {
  'en': 'EN',
  'pt-BR': 'PT',
  'es': 'ES',
}

const LOCALE_FULL: Record<Locale, string> = {
  'en': 'English',
  'pt-BR': 'Português (BR)',
  'es': 'Español',
}

/**
 * Top bar with breadcrumbs, pill-style locale switcher, and accessibility panel toggle.
 * Glass background for lightweight visual presence.
 */
export function TopBar() {
  const t = useTranslations('topbar')
  const tNav = useTranslations('nav')
  const pathname = usePathname()
  const router = useRouter()
  const [showA11y, setShowA11y] = useState(false)
  const [localeSwitching, setLocaleSwitching] = useState(false)

  // Extract current locale from pathname
  const localeMatch = pathname.match(/^\/([^/]+)/)
  const currentLocale = (localeMatch?.[1] ?? 'en') as Locale

  // Build breadcrumbs from pathname
  const pathWithoutLocale = pathname.replace(/^\/[^/]+/, '')
  const segments = pathWithoutLocale.split('/').filter(Boolean)

  function switchLocale(newLocale: Locale) {
    setLocaleSwitching(true)
    router.push(`/${newLocale}${pathWithoutLocale}`)
    // Clear loading state after navigation completes (or timeout as fallback)
    setTimeout(() => setLocaleSwitching(false), 1500)
  }

  return (
    <>
      <header
        className={cn(
          'flex items-center justify-between gap-4 px-6 py-2.5',
          'border-b border-[var(--color-border)]/50',
          'glass'
        )}
      >
        {/* Breadcrumbs — collapse to page title on mobile */}
        <nav aria-label={t('breadcrumbs')} className="flex items-center gap-1.5 text-sm min-w-0">
          {/* Mobile: show only current page title */}
          {segments.length > 0 ? (
            <motion.span
              key={pathname}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="text-[var(--color-text)] font-medium truncate sm:hidden"
            >
              {tNav.has(segments[segments.length - 1]) ? tNav(segments[segments.length - 1]) : segments[segments.length - 1]}
            </motion.span>
          ) : (
            <span className="text-[var(--color-text)] font-medium sm:hidden">
              {tNav('dashboard')}
            </span>
          )}

          {/* Desktop: full breadcrumb trail */}
          <Link
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed path
            href={`/${currentLocale}/dashboard` as any}
            className="hidden sm:inline text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors shrink-0"
          >
            {tNav('dashboard')}
          </Link>
          {segments.map((segment, i) => {
            const href = `/${currentLocale}/${segments.slice(0, i + 1).join('/')}`
            const isLast = i === segments.length - 1
            const label = tNav.has(segment) ? tNav(segment) : segment
            return (
              <span key={href} className="hidden sm:flex items-center gap-1.5 min-w-0">
                <ChevronIcon />
                {isLast ? (
                  <motion.span
                    key={pathname}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-[var(--color-text)] font-medium truncate"
                  >
                    {label}
                  </motion.span>
                ) : (
                  <Link
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- dynamic locale-prefixed path
                    href={href as any}
                    className="text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors truncate"
                  >
                    {label}
                  </Link>
                )}
              </span>
            )
          })}
        </nav>

        {/* Right section */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Command Palette trigger */}
          <CommandPaletteTrigger />

          {/* Locale switcher — pill buttons */}
          <LayoutGroup>
            <div
              className={cn(
                'flex items-center gap-0.5 p-1',
                'rounded-[var(--radius-md)] bg-[var(--color-surface-elevated)]/70'
              )}
              role="radiogroup"
              aria-label={t('locale_label')}
              onKeyDown={(e) => {
                const locales = Object.keys(LOCALE_LABELS) as Locale[]
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                  e.preventDefault()
                  const idx = locales.indexOf(currentLocale)
                  const next = locales[(idx + 1) % locales.length]
                  switchLocale(next)
                  const container = e.currentTarget
                  requestAnimationFrame(() => {
                    container.querySelector<HTMLElement>('[aria-checked="true"]')?.focus()
                  })
                } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                  e.preventDefault()
                  const idx = locales.indexOf(currentLocale)
                  const prev = locales[(idx - 1 + locales.length) % locales.length]
                  switchLocale(prev)
                  const container = e.currentTarget
                  requestAnimationFrame(() => {
                    container.querySelector<HTMLElement>('[aria-checked="true"]')?.focus()
                  })
                }
              }}
            >
              {(Object.entries(LOCALE_LABELS) as [Locale, string][]).map(([code, label]) => {
                const isActive = code === currentLocale
                return (
                  <button
                    key={code}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
                    tabIndex={isActive ? 0 : -1}
                    aria-label={LOCALE_FULL[code]}
                    onClick={() => switchLocale(code)}
                    className={cn(
                      'relative px-2.5 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold',
                      'transition-colors duration-200',
                      isActive
                        ? 'text-[var(--color-text)]'
                        : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="locale-pill"
                        className="absolute inset-0 rounded-[var(--radius-sm)] bg-[var(--color-bg)] shadow-[var(--shadow-sm)]"
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10">{label}</span>
                  </button>
                )
              })}
            </div>
          </LayoutGroup>

          {/* Locale switching indicator */}
          {localeSwitching && (
            <span className="w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" aria-hidden="true" />
          )}

          {/* System status indicator */}
          <SystemStatusButton />

          {/* Accessibility toggle */}
          <button
            type="button"
            onClick={() => setShowA11y((s) => !s)}
            aria-label={t('accessibility')}
            aria-expanded={showA11y}
            className={cn(
              'flex items-center gap-2 px-3 py-2',
              'rounded-[var(--radius-md)]',
              'text-sm text-[var(--color-muted)]',
              'hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]',
              'transition-all duration-200 btn-press',
              showA11y && 'bg-[var(--color-primary)]/5 text-[var(--color-primary)] shadow-[0_0_12px_var(--color-primary)]'
            )}
          >
            <AccessibilityIcon />
            <span className="hidden sm:inline text-xs font-medium">
              {t('accessibility')}
            </span>
          </button>
        </div>
      </header>

      {/* Accessibility panel overlay (portal to body) */}
      <PreferencesPanel open={showA11y} onClose={() => setShowA11y(false)} />
    </>
  )
}

function AccessibilityIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="4" r="2" />
      <path d="M12 6v6" />
      <path d="M6 10l6 2 6-2" />
      <path d="M9 18l3-6 3 6" />
    </svg>
  )
}

/** Simple TTL cache for health check to avoid re-fetching on every render. */
let healthCache: { status: 'healthy' | 'degraded' | 'unknown'; ts: number } | null = null
const HEALTH_TTL_MS = 30_000

function SystemStatusButton() {
  const t = useTranslations('topbar')
  const [status, setStatus] = useState<'healthy' | 'degraded' | 'unknown'>('unknown')
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelId = 'system-status-panel'

  useEffect(() => {
    if (healthCache && Date.now() - healthCache.ts < HEALTH_TTL_MS) {
      setStatus(healthCache.status)
      return
    }
    fetch(`${API_BASE}/health/ready`)
      .then((res) => {
        const s = res.ok ? 'healthy' : 'degraded'
        healthCache = { status: s, ts: Date.now() }
        setStatus(s)
      })
      .catch(() => {
        healthCache = { status: 'degraded', ts: Date.now() }
        setStatus('degraded')
      })
  }, [])

  useEffect(() => {
    if (!showDropdown) return
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
        triggerRef.current?.focus()
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setShowDropdown(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [showDropdown])

  const dotColor =
    status === 'healthy'
      ? 'bg-[var(--color-success)]'
      : status === 'degraded'
        ? 'bg-[var(--color-error)]'
        : 'bg-[var(--color-muted)]'

  return (
    <div ref={dropdownRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setShowDropdown((s) => !s)}
        aria-label={t('system_status')}
        aria-expanded={showDropdown}
        aria-controls={showDropdown ? panelId : undefined}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-2',
          'rounded-[var(--radius-md)]',
          'text-sm text-[var(--color-muted)]',
          'hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]',
          'transition-all duration-200',
        )}
      >
        <span className={cn('w-2 h-2 rounded-full', dotColor)} aria-hidden="true" />
        <span className="sr-only">
          {status === 'healthy' ? t('api_healthy') : status === 'degraded' ? t('api_degraded') : t('system_status')}
        </span>
        <StatusIcon />
      </button>

      {showDropdown && (
        <div
          id={panelId}
          className={cn(
            'absolute right-0 top-full mt-2 w-64 z-50',
            'rounded-[var(--radius-lg)] glass border border-[var(--color-border)]',
            'shadow-[var(--shadow-lg)] p-4 space-y-3',
          )}
          role="status"
          aria-label={t('system_status')}
        >
          <div className="flex items-center gap-2">
            <span className={cn('w-2.5 h-2.5 rounded-full', dotColor)} aria-hidden="true" />
            <span className="text-sm font-medium text-[var(--color-text)]">
              {status === 'healthy' ? t('api_healthy') : t('api_degraded')}
            </span>
          </div>
          <div className="text-xs text-[var(--color-muted)] space-y-1">
            <p>
              <span className="font-medium">{t('model_label')}:</span>{' '}
              {process.env.NEXT_PUBLIC_DEFAULT_MODEL ?? 'Auto-routed'}
            </p>
            <p className="flex items-center gap-1.5">
              <PrivacyIcon />
              {t('privacy_note')}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  )
}

function PrivacyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  )
}

function ChevronIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      stroke="var(--color-muted)"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <path d="M5 3l4 4-4 4" />
    </svg>
  )
}
