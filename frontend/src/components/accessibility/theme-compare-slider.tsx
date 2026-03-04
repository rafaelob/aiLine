'use client'

import { useCallback, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { PERSONAS } from '@/lib/accessibility-data'
import type { PersonaId } from '@/types/accessibility'

/**
 * Essential CSS custom property values for each theme.
 * Extracted from globals.css persona themes for inline rendering
 * in the before/after comparison panels.
 */
const THEME_VARS: Record<
  string,
  {
    bg: string
    text: string
    primary: string
    surface: string
    surfaceElevated: string
    border: string
    muted: string
    onPrimary: string
    radius: string
    fontSize: string
    lineHeight: string
    font: string
  }
> = {
  standard: {
    bg: '#FFFFFF',
    text: '#1A1A2E',
    primary: '#2563EB',
    surface: '#F8FAFC',
    surfaceElevated: '#F1F5F9',
    border: '#E2E8F0',
    muted: '#4B5563',
    onPrimary: '#FFFFFF',
    radius: '12px',
    fontSize: '16px',
    lineHeight: '1.6',
    font: 'system-ui, -apple-system, sans-serif',
  },
  high_contrast: {
    bg: '#000000',
    text: '#FFFFFF',
    primary: '#5EEAD4',
    surface: '#0A0A0A',
    surfaceElevated: '#171717',
    border: '#525252',
    muted: '#A3A3A3',
    onPrimary: '#000000',
    radius: '8px',
    fontSize: '18px',
    lineHeight: '1.8',
    font: 'system-ui, -apple-system, sans-serif',
  },
  tea: {
    bg: '#F0F7F4',
    text: '#1B3A33',
    primary: '#2D8B6E',
    surface: '#E8F3EE',
    surfaceElevated: '#D5EAE1',
    border: '#B8D5CA',
    muted: '#5F8A7C',
    onPrimary: '#FFFFFF',
    radius: '14px',
    fontSize: '17px',
    lineHeight: '1.8',
    font: 'system-ui, -apple-system, sans-serif',
  },
  tdah: {
    bg: '#FFFDF7',
    text: '#2D2A24',
    primary: '#E07E34',
    surface: '#FFF8EC',
    surfaceElevated: '#FFEDD5',
    border: '#E8D5B8',
    muted: '#8B7355',
    onPrimary: '#FFFFFF',
    radius: '12px',
    fontSize: '17px',
    lineHeight: '1.8',
    font: 'system-ui, -apple-system, sans-serif',
  },
  dyslexia: {
    bg: '#FBF5E6',
    text: '#2C2416',
    primary: '#3B7DD8',
    surface: '#F5EDD6',
    surfaceElevated: '#EDE3C8',
    border: '#D4C9A8',
    muted: '#786A4E',
    onPrimary: '#FFFFFF',
    radius: '12px',
    fontSize: '18px',
    lineHeight: '2.0',
    font: "'OpenDyslexic', system-ui, sans-serif",
  },
  low_vision: {
    bg: '#FFFEF5',
    text: '#1A1400',
    primary: '#1A56DB',
    surface: '#FFF9E0',
    surfaceElevated: '#FFF3C4',
    border: '#D4C06A',
    muted: '#5C4E00',
    onPrimary: '#FFFFFF',
    radius: '14px',
    fontSize: '22px',
    lineHeight: '2.0',
    font: 'system-ui, -apple-system, sans-serif',
  },
  hearing: {
    bg: '#F8F9FE',
    text: '#1E1E3A',
    primary: '#4338CA',
    surface: '#EEEEF8',
    surfaceElevated: '#E0E0F0',
    border: '#C7C7E0',
    muted: '#5B5B8A',
    onPrimary: '#FFFFFF',
    radius: '12px',
    fontSize: '17px',
    lineHeight: '1.7',
    font: 'system-ui, -apple-system, sans-serif',
  },
  motor: {
    bg: '#FAFBFF',
    text: '#1C1C3A',
    primary: '#3B82F6',
    surface: '#F0F2FF',
    surfaceElevated: '#E2E5F0',
    border: '#C5CAE0',
    muted: '#5A5E80',
    onPrimary: '#FFFFFF',
    radius: '16px',
    fontSize: '18px',
    lineHeight: '1.8',
    font: 'system-ui, -apple-system, sans-serif',
  },
  screen_reader: {
    bg: '#FFFFFF',
    text: '#111827',
    primary: '#1D4ED8',
    surface: '#F9FAFB',
    surfaceElevated: '#F3F4F6',
    border: '#D1D5DB',
    muted: '#6B7280',
    onPrimary: '#FFFFFF',
    radius: '8px',
    fontSize: '16px',
    lineHeight: '1.8',
    font: 'system-ui, -apple-system, sans-serif',
  },
}

/** Sample content rendered in each panel to demonstrate theme differences. */
function SampleContent({
  vars,
  themeLabel,
}: {
  vars: (typeof THEME_VARS)[string]
  themeLabel: string
}) {
  return (
    <div
      className="h-full w-full p-4 select-none"
      style={{
        backgroundColor: vars.bg,
        color: vars.text,
        fontFamily: vars.font,
        fontSize: vars.fontSize,
        lineHeight: vars.lineHeight,
      }}
    >
      {/* Theme label */}
      <div
        className="text-xs font-bold uppercase tracking-wider mb-3 pb-2"
        style={{ color: vars.muted, borderBottom: `1px solid ${vars.border}` }}
      >
        {themeLabel}
      </div>

      {/* Card */}
      <div
        className="p-3 mb-3"
        style={{
          backgroundColor: vars.surface,
          border: `1px solid ${vars.border}`,
          borderRadius: vars.radius,
        }}
      >
        <h3
          className="font-bold mb-1"
          style={{ fontSize: `calc(${vars.fontSize} * 1.1)` }}
        >
          Lesson: Photosynthesis
        </h3>
        <p className="mb-2" style={{ color: vars.muted, fontSize: `calc(${vars.fontSize} * 0.85)` }}>
          Plants convert sunlight into energy through a process called photosynthesis.
        </p>
        {/* Button */}
        <button
          type="button"
          className="px-3 py-1.5 font-medium"
          style={{
            backgroundColor: vars.primary,
            color: vars.onPrimary,
            borderRadius: `calc(${vars.radius} / 2)`,
            fontSize: `calc(${vars.fontSize} * 0.85)`,
          }}
          tabIndex={-1}
          aria-hidden="true"
        >
          Start Learning
        </button>
      </div>

      {/* Badge row */}
      <div className="flex gap-2 flex-wrap">
        <span
          className="px-2 py-0.5 font-medium"
          style={{
            backgroundColor: vars.surfaceElevated,
            border: `1px solid ${vars.border}`,
            borderRadius: `calc(${vars.radius} / 2)`,
            fontSize: `calc(${vars.fontSize} * 0.75)`,
            color: vars.primary,
          }}
        >
          Biology
        </span>
        <span
          className="px-2 py-0.5 font-medium"
          style={{
            backgroundColor: vars.surfaceElevated,
            border: `1px solid ${vars.border}`,
            borderRadius: `calc(${vars.radius} / 2)`,
            fontSize: `calc(${vars.fontSize} * 0.75)`,
            color: vars.muted,
          }}
        >
          Grade 5
        </span>
      </div>
    </div>
  )
}

export interface ThemeCompareSliderProps {
  /** The persona to compare against standard. Defaults to current active theme. */
  compareTheme?: string
  /** Fixed height in px. Defaults to 260. */
  height?: number
}

/**
 * Before/After accessibility theme comparison slider.
 * Left side shows "standard" theme, right side shows the selected persona theme.
 * Drag the divider to reveal more of either side.
 * Keyboard: Left/Right arrows move divider by 5%.
 */
export function ThemeCompareSlider({
  compareTheme,
  height = 260,
}: ThemeCompareSliderProps) {
  const t = useTranslations('accessibility')
  const { theme: activeTheme } = useAccessibilityStore()
  const rightTheme = compareTheme ?? activeTheme
  const containerRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState(50) // percentage 0-100
  const isDragging = useRef(false)

  const leftVars = THEME_VARS.standard
  const rightVars = THEME_VARS[rightTheme] ?? THEME_VARS.standard
  const persona = PERSONAS[rightTheme as PersonaId]

  const updatePosition = useCallback((clientX: number) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const pct = ((clientX - rect.left) / rect.width) * 100
    setPosition(Math.max(5, Math.min(95, pct)))
  }, [])

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      isDragging.current = true
      ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
      updatePosition(e.clientX)
    },
    [updatePosition],
  )

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isDragging.current) return
      updatePosition(e.clientX)
    },
    [updatePosition],
  )

  const handlePointerUp = useCallback(() => {
    isDragging.current = false
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      setPosition((p) => Math.max(5, p - 5))
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      setPosition((p) => Math.min(95, p + 5))
    }
  }, [])

  // If the right theme is standard, show a message instead of identical panels
  if (rightTheme === 'standard') {
    return (
      <div
        className="rounded-xl border border-[var(--color-border)] p-6 text-center text-sm text-[var(--color-muted)]"
        role="region"
        aria-label={t('compare_label')}
      >
        {t('compare_select_persona')}
      </div>
    )
  }

  return (
    <div role="region" aria-label={t('compare_label')}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
          {t('compare_title')}
        </span>
        {persona && (
          <span className="text-xs text-[var(--color-muted)]">
            {persona.icon}{' '}
            {t(
              `themes.${rightTheme === 'high_contrast' ? 'high-contrast' : rightTheme === 'low_vision' ? 'low-vision' : rightTheme === 'screen_reader' ? 'screen-reader' : rightTheme}`,
            )}
          </span>
        )}
      </div>

      {/* Slider container */}
      <div
        ref={containerRef}
        className={cn(
          'relative overflow-hidden rounded-xl border border-[var(--color-border)]',
          'select-none touch-none',
        )}
        style={{ height }}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {/* Left panel (standard) — full width, clipped by right overlay */}
        <div className="absolute inset-0" aria-hidden="true">
          <SampleContent vars={leftVars} themeLabel={`${t('themes.standard')} ←`} />
        </div>

        {/* Right panel (persona) — positioned right, clipped left at divider */}
        <div
          className="absolute inset-0"
          style={{ clipPath: `inset(0 0 0 ${position}%)` }}
          aria-hidden="true"
        >
          <SampleContent
            vars={rightVars}
            themeLabel={`→ ${t(`themes.${rightTheme === 'high_contrast' ? 'high-contrast' : rightTheme === 'low_vision' ? 'low-vision' : rightTheme === 'screen_reader' ? 'screen-reader' : rightTheme}`)}`}
          />
        </div>

        {/* Draggable divider */}
        <div
          role="slider"
          aria-label={t('compare_divider')}
          aria-valuemin={5}
          aria-valuemax={95}
          aria-valuenow={Math.round(position)}
          tabIndex={0}
          className={cn(
            'absolute top-0 bottom-0 w-1 cursor-col-resize z-10',
            'bg-[var(--color-primary)] shadow-lg',
            'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[var(--color-primary)]',
          )}
          style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
          onPointerDown={handlePointerDown}
          onKeyDown={handleKeyDown}
        >
          {/* Drag handle grip */}
          <div
            className={cn(
              'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
              'w-6 h-8 rounded-md flex items-center justify-center',
              'bg-[var(--color-primary)] shadow-md',
            )}
          >
            <svg
              width="12"
              height="16"
              viewBox="0 0 12 16"
              fill="none"
              className="text-[var(--color-on-primary,#fff)]"
              aria-hidden="true"
            >
              <path d="M4 2v12M8 2v12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  )
}
