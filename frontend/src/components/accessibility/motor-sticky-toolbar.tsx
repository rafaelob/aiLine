'use client'

import { useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { cn } from '@/lib/cn'

/**
 * Sticky bottom toolbar for the motor accessibility persona (F-235).
 *
 * Renders only when `theme === 'motor'`. Provides large, pill-shaped
 * action buttons for common tasks:  scroll-to-top, font size +/-,
 * focus mode toggle, and a "back to top" shortcut.
 *
 * Positioned above MobileNav (which is fixed bottom-0 on < md).
 * The CSS in globals.css reserves `padding-bottom: 80px` on `main`
 * for this toolbar when `[data-theme="motor"]` is active.
 */
export function MotorStickyToolbar() {
  const t = useTranslations('motor_toolbar')
  const theme = useAccessibilityStore((s) => s.theme)
  const fontSize = useAccessibilityStore((s) => s.fontSize)
  const setFontSize = useAccessibilityStore((s) => s.setFontSize)
  const focusMode = useAccessibilityStore((s) => s.focusMode)
  const toggleFocusMode = useAccessibilityStore((s) => s.toggleFocusMode)

  const scrollToTop = useCallback(() => {
    const main = document.getElementById('main-content')
    if (main) {
      main.scrollTo({ top: 0, behavior: 'smooth' })
      main.focus({ preventScroll: true })
    }
  }, [])

  const increaseFontSize = useCallback(() => {
    const sizes = ['small', 'medium', 'large', 'xlarge']
    const idx = sizes.indexOf(fontSize)
    if (idx < sizes.length - 1) {
      setFontSize(sizes[idx + 1])
    }
  }, [fontSize, setFontSize])

  const decreaseFontSize = useCallback(() => {
    const sizes = ['small', 'medium', 'large', 'xlarge']
    const idx = sizes.indexOf(fontSize)
    if (idx > 0) {
      setFontSize(sizes[idx - 1])
    }
  }, [fontSize, setFontSize])

  if (theme !== 'motor') return null

  return (
    <div
      role="toolbar"
      aria-label={t('label')}
      className={cn(
        'fixed bottom-0 left-0 right-0 z-40',
        'md:bottom-0 bottom-[56px]',
        'flex items-center justify-center gap-3 px-4 py-2',
        'border-t border-[var(--color-border)]/50',
        'backdrop-blur-xl bg-[var(--color-surface)]/90',
        'shadow-[var(--shadow-md)]'
      )}
      style={{
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      <ToolbarButton
        onClick={scrollToTop}
        label={t('scroll_top')}
        icon={<ArrowUpIcon />}
      />
      <ToolbarButton
        onClick={decreaseFontSize}
        label={t('font_decrease')}
        icon={<FontDecreaseIcon />}
        disabled={fontSize === 'small'}
      />
      <ToolbarButton
        onClick={increaseFontSize}
        label={t('font_increase')}
        icon={<FontIncreaseIcon />}
        disabled={fontSize === 'xlarge'}
      />
      <ToolbarButton
        onClick={toggleFocusMode}
        label={focusMode ? t('focus_off') : t('focus_on')}
        icon={<FocusIcon />}
        active={focusMode}
      />
    </div>
  )
}

interface ToolbarButtonProps {
  onClick: () => void
  label: string
  icon: React.ReactNode
  disabled?: boolean
  active?: boolean
}

function ToolbarButton({ onClick, label, icon, disabled, active }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      className={cn(
        'flex items-center justify-center',
        'min-h-[56px] min-w-[56px] px-4',
        'rounded-full font-semibold text-sm',
        'transition-colors duration-150',
        'focus-visible:outline-3 focus-visible:outline-[var(--color-primary)]',
        'focus-visible:outline-offset-2',
        active
          ? 'bg-[var(--color-primary)] text-white'
          : 'bg-[var(--color-surface-elevated)] text-[var(--color-text)]',
        disabled && 'opacity-40 cursor-not-allowed'
      )}
    >
      <span className="flex items-center gap-2" aria-hidden="true">
        {icon}
      </span>
    </button>
  )
}

function ArrowUpIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 19V5" />
      <path d="M5 12l7-7 7 7" />
    </svg>
  )
}

function FontDecreaseIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <text x="4" y="18" fontSize="16" fontWeight="bold" fill="currentColor" stroke="none">A</text>
      <text x="16" y="18" fontSize="10" fontWeight="bold" fill="currentColor" stroke="none">a</text>
      <path d="M15 4l-6 0" />
    </svg>
  )
}

function FontIncreaseIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <text x="4" y="18" fontSize="16" fontWeight="bold" fill="currentColor" stroke="none">A</text>
      <text x="16" y="18" fontSize="10" fontWeight="bold" fill="currentColor" stroke="none">a</text>
      <path d="M12 1v6M9 4h6" />
    </svg>
  )
}

function FocusIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
    </svg>
  )
}
