'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { usePathname, useRouter } from 'next/navigation'
import { cn } from '@/lib/cn'
import { PreferencesPanel } from '@/components/accessibility/preferences-panel'
import type { Locale } from '@/i18n/routing'

const LOCALE_LABELS: Record<Locale, string> = {
  'en': 'English',
  'pt-BR': 'Portugues (BR)',
  'es': 'Espanol',
}

/**
 * Top bar with breadcrumbs, locale switcher, and accessibility panel toggle.
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
          'flex items-center justify-between gap-4 px-6 py-3',
          'border-b bg-[var(--color-surface)] border-[var(--color-border)]'
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
                  <span className="text-[var(--color-text)] font-medium truncate">
                    {label}
                  </span>
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
          {/* Locale switcher */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="locale-select"
              className="text-sm text-[var(--color-muted)] sr-only"
            >
              {t('locale_label')}
            </label>
            <select
              id="locale-select"
              value={currentLocale}
              onChange={(e) => switchLocale(e.target.value as Locale)}
              aria-label={t('locale_label')}
              className={cn(
                'rounded-[var(--radius-sm)] border border-[var(--color-border)]',
                'bg-[var(--color-bg)] text-[var(--color-text)]',
                'px-3 py-2 text-sm'
              )}
            >
              {Object.entries(LOCALE_LABELS).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Accessibility toggle */}
          <button
            type="button"
            onClick={() => setShowA11y((s) => !s)}
            aria-label={t('accessibility')}
            aria-expanded={showA11y}
            className={cn(
              'flex items-center gap-2 px-3 py-2',
              'rounded-[var(--radius-md)] border border-[var(--color-border)]',
              'text-sm text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)] transition-colors'
            )}
          >
            <AccessibilityIcon />
            <span className="hidden sm:inline">{t('accessibility')}</span>
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
      width="20"
      height="20"
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
