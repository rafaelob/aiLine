'use client'

import { useEffect, useRef, useCallback, useState, useSyncExternalStore } from 'react'
import { createPortal } from 'react-dom'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { useViewTransition } from '@/hooks/use-view-transition'

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
  open: boolean
  onClose: () => void
}

/**
 * Accessibility preferences panel (ADR-019).
 * Renders via Portal to document.body to avoid layout shifts.
 * Theme switch via data-theme attribute on body — no React re-render.
 * Persisted to localStorage.
 */
export function PreferencesPanel({ open, onClose }: PreferencesPanelProps) {
  const t = useTranslations('accessibility')
  const panelRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)
  const tHints = useTranslations('accessibility.theme_hints')
  const mounted = useSyncExternalStore(emptySubscribe, returnTrue, returnFalse)
  const {
    theme, fontSize, reducedMotion, focusMode, bionicReading,
    setTheme, setFontSize, setReducedMotion, toggleFocusMode, toggleBionicReading,
  } = useAccessibilityStore()
  const { startTransition } = useViewTransition()

  // Save previously focused element and restore on unmount
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement | null
    }
    return () => {
      if (!open) {
        previousFocusRef.current?.focus()
      }
    }
  }, [open])

  // Lock body scroll when panel is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = ''
      }
    }
  }, [open])

  // Focus trap: focus close button on mount and trap Tab within panel
  useEffect(() => {
    if (!open) return

    const timer = requestAnimationFrame(() => {
      closeButtonRef.current?.focus()
    })

    const panel = panelRef.current
    if (!panel) return () => cancelAnimationFrame(timer)

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
    return () => {
      cancelAnimationFrame(timer)
      document.removeEventListener('keydown', handleFocusTrap)
    }
  }, [open])

  // Close on Escape
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    },
    [onClose]
  )

  const [themeAnnouncement, setThemeAnnouncement] = useState('')

  function handleThemeChange(newTheme: ThemeId) {
    startTransition(
      () => {
        setTheme(newTheme)
        document.body.setAttribute('data-theme', newTheme)
        setThemeAnnouncement(t('switched_to', { persona: t(`themes.${newTheme}`) }))
      },
      { type: 'theme' },
    )
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

  if (!mounted) return null

  const content = (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop overlay */}
          <motion.div
            initial={reducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reducedMotion ? undefined : { opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[55] bg-black/30"
            aria-hidden="true"
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-label={t('title')}
            aria-modal="true"
            initial={reducedMotion ? false : { opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reducedMotion ? undefined : { opacity: 0, x: 300 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            onKeyDown={handleKeyDown}
            className={cn(
              'fixed right-0 top-0 z-[60] h-full w-full sm:w-80 sm:max-w-full',
              'border-l bg-[var(--color-surface)] border-[var(--color-border)]',
              'overflow-y-auto shadow-lg p-6'
            )}
          >
            {/* SR-only live region for theme change announcements */}
            <div className="sr-only" aria-live="assertive" aria-atomic="true">
              {themeAnnouncement}
            </div>

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
                    <span className="flex flex-col">
                      <span className="text-sm text-[var(--color-text)]">
                        {t(`themes.${id}`)}
                      </span>
                      <span className="text-xs text-[var(--color-muted)] mt-0.5">
                        {tHints(id)}
                      </span>
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
            <fieldset className="mb-6">
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

            {/* Focus Mode (Cognitive Curtain) */}
            <fieldset className="mb-6">
              <legend className="text-sm font-semibold text-[var(--color-text)] mb-3">
                {t('focusMode')}
              </legend>
              <button
                type="button"
                role="switch"
                aria-checked={focusMode}
                aria-label={t('focusMode')}
                onClick={toggleFocusMode}
                className={cn(
                  'relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors',
                  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
                  focusMode
                    ? 'bg-[var(--color-primary)]'
                    : 'bg-[var(--color-border)]'
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm',
                    'transform transition-transform mt-0.5',
                    focusMode ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'
                  )}
                  aria-hidden="true"
                />
              </button>
            </fieldset>

            {/* Bionic Reading */}
            <fieldset>
              <legend className="text-sm font-semibold text-[var(--color-text)] mb-3">
                {t('bionicReading')}
              </legend>
              <button
                type="button"
                role="switch"
                aria-checked={bionicReading}
                aria-label={t('bionicReading')}
                onClick={toggleBionicReading}
                className={cn(
                  'relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors',
                  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
                  bionicReading
                    ? 'bg-[var(--color-primary)]'
                    : 'bg-[var(--color-border)]'
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm',
                    'transform transition-transform mt-0.5',
                    bionicReading ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'
                  )}
                  aria-hidden="true"
                />
              </button>
            </fieldset>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )

  return createPortal(content, document.body)
}

/* useSyncExternalStore SSR guard — returns true on client, false on server */
const emptySubscribe = () => () => {}
const returnTrue = () => true
const returnFalse = () => false

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
