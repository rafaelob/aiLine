'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'

const THEME_IDS = [
  'standard',
  'high-contrast',
  'tea',
  'tdah',
  'dyslexia',
  'low-vision',
  'hearing',
  'motor',
  'screen-reader',
] as const

type ThemeId = (typeof THEME_IDS)[number]

interface PreferencesPanelProps {
  onClose: () => void
}

/**
 * Accessibility preferences panel (ADR-019).
 * Theme switch via data-theme attribute on body -- no React re-render.
 * Persisted to localStorage.
 */
export function PreferencesPanel({ onClose }: PreferencesPanelProps) {
  const t = useTranslations('accessibility')
  const panelRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)
  const { theme, fontSize, reducedMotion, setTheme, setFontSize, setReducedMotion } =
    useAccessibilityStore()

  // Save previously focused element and restore on unmount
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement | null
    return () => {
      previousFocusRef.current?.focus()
    }
  }, [])

  // Focus trap: focus close button on mount and trap Tab within panel
  useEffect(() => {
    closeButtonRef.current?.focus()

    const panel = panelRef.current
    if (!panel) return

    function handleFocusTrap(e: KeyboardEvent) {
      if (e.key !== 'Tab') return

      const focusableEls = panel!.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (focusableEls.length === 0) return

      const first = focusableEls[0]
      const last = focusableEls[focusableEls.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', handleFocusTrap)
    return () => document.removeEventListener('keydown', handleFocusTrap)
  }, [])

  // Close on Escape
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    },
    [onClose]
  )

  function handleThemeChange(newTheme: ThemeId) {
    setTheme(newTheme)
    // Direct DOM manipulation -- no React re-render (ADR-019)
    document.body.setAttribute('data-theme', newTheme)
  }

  function handleFontSizeChange(size: string) {
    setFontSize(size)
    document.documentElement.style.setProperty(
      '--font-size-base',
      fontSizeMap[size] ?? '16px'
    )
  }

  function handleMotionChange(reduced: boolean) {
    setReducedMotion(reduced)
  }

  return (
    <>
      {/* Backdrop overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-black/30"
        aria-hidden="true"
      />
      <motion.div
        ref={panelRef}
        role="dialog"
        aria-label={t('title')}
        aria-modal="true"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        onKeyDown={handleKeyDown}
        className={cn(
          'fixed right-0 top-0 z-50 h-full w-full sm:w-80 sm:max-w-full',
          'border-l bg-[var(--color-surface)] border-[var(--color-border)]',
          'overflow-y-auto shadow-lg p-6'
        )}
      >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-[var(--color-text)]">{t('title')}</h2>
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onClose}
          aria-label={t('close')}
          className={cn(
            'rounded-[var(--radius-sm)] p-2',
            'text-[var(--color-muted)] hover:bg-[var(--color-surface-elevated)]'
          )}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M15 5L5 15M5 5l10 10" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* Theme selector */}
      <fieldset className="mb-6">
        <legend className="text-sm font-semibold text-[var(--color-text)] mb-3">
          {t('theme')}
        </legend>
        <div className="grid grid-cols-1 gap-2" role="radiogroup" aria-label={t('theme')}>
          {THEME_IDS.map((id) => (
            <label
              key={id}
              className={cn(
                'flex items-center gap-3 px-3 py-3 rounded-[var(--radius-md)]',
                'cursor-pointer transition-colors border',
                theme === id
                  ? 'border-[var(--color-primary)] bg-[var(--color-surface-elevated)]'
                  : 'border-transparent hover:bg-[var(--color-surface-elevated)]'
              )}
            >
              <input
                type="radio"
                name="theme"
                value={id}
                checked={theme === id}
                onChange={() => handleThemeChange(id)}
                className="sr-only"
              />
              <span
                className={cn(
                  'w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0',
                  theme === id
                    ? 'border-[var(--color-primary)]'
                    : 'border-[var(--color-border)]'
                )}
                aria-hidden="true"
              >
                {theme === id && (
                  <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-primary)]" />
                )}
              </span>
              <span className="text-sm text-[var(--color-text)]">
                {t(`themes.${id}`)}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Font size */}
      <fieldset className="mb-6">
        <legend className="text-sm font-semibold text-[var(--color-text)] mb-3">
          {t('font_size')}
        </legend>
        <div className="flex gap-2" role="radiogroup" aria-label={t('font_size')}>
          {FONT_SIZES.map(({ key, label }) => (
            <label
              key={key}
              className={cn(
                'flex-1 text-center py-2 rounded-[var(--radius-sm)]',
                'cursor-pointer text-sm transition-colors border',
                fontSize === key
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                  : 'border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
              )}
            >
              <input
                type="radio"
                name="font-size"
                value={key}
                checked={fontSize === key}
                onChange={() => handleFontSizeChange(key)}
                className="sr-only"
              />
              {t(label)}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Motion */}
      <fieldset>
        <legend className="text-sm font-semibold text-[var(--color-text)] mb-3">
          {t('motion')}
        </legend>
        <div className="flex gap-2" role="radiogroup" aria-label={t('motion')}>
          <label
            className={cn(
              'flex-1 text-center py-2 rounded-[var(--radius-sm)]',
              'cursor-pointer text-sm transition-colors border',
              !reducedMotion
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
            )}
          >
            <input
              type="radio"
              name="motion"
              value="full"
              checked={!reducedMotion}
              onChange={() => handleMotionChange(false)}
              className="sr-only"
            />
            {t('motion_full')}
          </label>
          <label
            className={cn(
              'flex-1 text-center py-2 rounded-[var(--radius-sm)]',
              'cursor-pointer text-sm transition-colors border',
              reducedMotion
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-on-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]'
            )}
          >
            <input
              type="radio"
              name="motion"
              value="reduced"
              checked={reducedMotion}
              onChange={() => handleMotionChange(true)}
              className="sr-only"
            />
            {t('motion_reduced')}
          </label>
        </div>
      </fieldset>
    </motion.div>
    </>
  )
}

/* Font size mapping */
const fontSizeMap: Record<string, string> = {
  small: '14px',
  medium: '16px',
  large: '20px',
  xlarge: '24px',
}

const FONT_SIZES = [
  { key: 'small', label: 'font_size_small' as const },
  { key: 'medium', label: 'font_size_medium' as const },
  { key: 'large', label: 'font_size_large' as const },
  { key: 'xlarge', label: 'font_size_xlarge' as const },
]
