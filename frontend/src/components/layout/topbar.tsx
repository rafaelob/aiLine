'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname, useRouter } from 'next/navigation'
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

  // Extract current locale from pathname
  const localeMatch = pathname.match(/^\/([^/]+)/)
  const currentLocale = (localeMatch?.[1] ?? 'pt-BR') as Locale

  // Build breadcrumbs from pathname
  const pathWithoutLocale = pathname.replace(/^\/[^/]+/, '')
  const segments = pathWithoutLocale.split('/').filter(Boolean)

  function switchLocale(newLocale: Locale) {
    router.push(`/${newLocale}${pathWithoutLocale}`)
  }

  return (
    <>
      <header
        role="banner"
        className={cn(
          'flex items-center justify-between gap-4 px-6 py-2.5',
          'border-b border-[var(--color-border)]/50',
          'glass'
        )}
      >
        {/* Breadcrumbs */}
        <nav aria-label={t('breadcrumbs')} className="flex items-center gap-1.5 text-sm min-w-0">
          <a
            href={`/${currentLocale}`}
            className="text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors shrink-0"
          >
            {tNav('dashboard')}
          </a>
          {segments.map((segment, i) => {
            const href = `/${currentLocale}/${segments.slice(0, i + 1).join('/')}`
            const isLast = i === segments.length - 1
            const label = tNav.has(segment) ? tNav(segment) : segment
            return (
              <span key={href} className="flex items-center gap-1.5 min-w-0">
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
                  <a
                    href={href}
                    className="text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors truncate"
                  >
                    {label}
                  </a>
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
            >
              {(Object.entries(LOCALE_LABELS) as [Locale, string][]).map(([code, label]) => {
                const isActive = code === currentLocale
                return (
                  <button
                    key={code}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
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
              'transition-all duration-200',
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

      {/* Accessibility panel overlay */}
      {showA11y && (
        <PreferencesPanel onClose={() => setShowA11y(false)} />
      )}
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

function SystemStatusButton() {
  const t = useTranslations('topbar')
  const [status, setStatus] = useState<'healthy' | 'degraded' | 'unknown'>('unknown')
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/health/ready`)
      .then((res) => setStatus(res.ok ? 'healthy' : 'degraded'))
      .catch(() => setStatus('degraded'))
  }, [])

  const dotColor =
    status === 'healthy'
      ? 'bg-[var(--color-success)]'
      : status === 'degraded'
        ? 'bg-[var(--color-error)]'
        : 'bg-[var(--color-muted)]'

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setShowDropdown((s) => !s)}
        aria-label={t('system_status')}
        aria-expanded={showDropdown}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-2',
          'rounded-[var(--radius-md)]',
          'text-sm text-[var(--color-muted)]',
          'hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]',
          'transition-all duration-200',
        )}
      >
        <span className={cn('w-2 h-2 rounded-full', dotColor)} aria-hidden="true" />
        <StatusIcon />
      </button>

      {showDropdown && (
        <div
          className={cn(
            'absolute right-0 top-full mt-2 w-64 z-50',
            'rounded-[var(--radius-lg)] glass border border-[var(--color-border)]',
            'shadow-[var(--shadow-lg)] p-4 space-y-3',
          )}
          role="dialog"
          aria-label={t('system_status')}
        >
          <div className="flex items-center gap-2">
            <span className={cn('w-2.5 h-2.5 rounded-full', dotColor)} />
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
