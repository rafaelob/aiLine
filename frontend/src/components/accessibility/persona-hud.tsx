'use client'

import { useState, useCallback, useRef, startTransition } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { useTheme } from '@/hooks/use-theme'
import { PERSONA_LIST } from '@/lib/accessibility-data'
import type { PersonaId, Persona } from '@/types/accessibility'

/** The 3 "hero" personas always visible in the HUD. */
const HERO_IDS: PersonaId[] = ['low_vision', 'dyslexia', 'tdah']

/** Map PersonaId to the CSS data-theme value. */
const THEME_MAP: Record<PersonaId, string> = {
  standard: 'standard',
  high_contrast: 'high-contrast',
  tea: 'tea',
  tdah: 'tdah',
  dyslexia: 'dyslexia',
  low_vision: 'low-vision',
  hearing: 'hearing',
  motor: 'motor',
  screen_reader: 'screen-reader',
}

interface PersonaHUDProps {
  className?: string
}

/**
 * Floating Persona Switcher HUD for live mid-stream persona switching.
 *
 * Features:
 * - 3 hero buttons always visible (Low Vision, Dyslexia, ADHD)
 * - Expandable "All personas" panel for the full 9
 * - Ripple animation on switch
 * - Toast notification on switch
 * - Uses startTransition for smooth mid-stream switching
 * - CSS-based theme swap (no React re-render for styling)
 */
export function PersonaHUD({ className }: PersonaHUDProps) {
  const t = useTranslations('accessibility')
  const { activePersona, switchTheme } = useTheme()
  const [isExpanded, setIsExpanded] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const [ripple, setRipple] = useState<{ x: number; y: number } | null>(null)
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const heroPersonas = PERSONA_LIST.filter((p) => HERO_IDS.includes(p.id))
  const allPersonas = PERSONA_LIST

  const handleSwitch = useCallback(
    (persona: Persona, event: React.MouseEvent<HTMLButtonElement>) => {
      if (persona.id === activePersona) return

      // Trigger ripple from button position
      const rect = event.currentTarget.getBoundingClientRect()
      setRipple({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
      setTimeout(() => setRipple(null), 600)

      // Apply theme via hook (instant CSS swap, persists in localStorage)
      startTransition(() => {
        switchTheme(persona.id)
      })

      // Show toast
      if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current)
      const personaLabel = t(`themes.${THEME_MAP[persona.id]}` as Parameters<typeof t>[0])
      setToast(t('switched_to', { persona: personaLabel }))
      toastTimeoutRef.current = setTimeout(() => setToast(null), 2500)
    },
    [activePersona, switchTheme, t]
  )

  return (
    <>
      {/* HUD container */}
      <nav
        aria-label={t('hud_label')}
        className={cn(
          'fixed bottom-4 right-4 z-40 flex flex-col items-end gap-2',
          className
        )}
      >
        {/* Expanded panel */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={cn(
                'glass rounded-[var(--radius-lg)] p-3',
                'shadow-[var(--shadow-xl)]',
                'grid grid-cols-3 gap-2 w-[280px]'
              )}
              role="radiogroup"
              aria-label={t('all_personas')}
            >
              {allPersonas.map((persona) => (
                <PersonaButton
                  key={persona.id}
                  persona={persona}
                  isActive={activePersona === persona.id}
                  onClick={handleSwitch}
                  compact
                  t={t}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main HUD bar */}
        <div
          role="radiogroup"
          aria-label={t('hud_label')}
          className={cn(
            'glass rounded-full px-2 py-1.5',
            'shadow-[var(--shadow-lg)]',
            'flex items-center gap-1.5'
          )}
        >
          {/* Hero buttons */}
          {heroPersonas.map((persona) => (
            <PersonaButton
              key={persona.id}
              persona={persona}
              isActive={activePersona === persona.id}
              onClick={handleSwitch}
              compact={false}
              t={t}
            />
          ))}

          {/* Divider */}
          <div
            className="w-px h-6 bg-[var(--color-border)] mx-0.5"
            aria-hidden="true"
          />

          {/* Expand toggle */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-label={t('all_personas')}
            className={cn(
              'flex items-center justify-center',
              'w-9 h-9 rounded-full',
              'text-[var(--color-muted)]',
              'hover:bg-[var(--color-surface-elevated)]',
              'transition-colors duration-150'
            )}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={cn(
                'transition-transform duration-200',
                isExpanded && 'rotate-180'
              )}
              aria-hidden="true"
            >
              <path d="M18 15l-6-6-6 6" />
            </svg>
          </button>
        </div>
      </nav>

      {/* Ripple effect */}
      <AnimatePresence>
        {ripple && (
          <motion.div
            initial={{ scale: 0, opacity: 0.4 }}
            animate={{ scale: 4, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="fixed w-24 h-24 rounded-full bg-[var(--color-primary)] pointer-events-none z-50"
            style={{
              left: ripple.x - 48,
              top: ripple.y - 48,
            }}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      {/* Toast notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3 }}
            role="status"
            aria-live="polite"
            className={cn(
              'fixed bottom-20 right-4 z-50',
              'glass rounded-[var(--radius-md)] px-4 py-2',
              'shadow-[var(--shadow-lg)]',
              'text-sm font-medium text-[var(--color-text)]'
            )}
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

interface PersonaButtonProps {
  persona: Persona
  isActive: boolean
  onClick: (persona: Persona, e: React.MouseEvent<HTMLButtonElement>) => void
  compact: boolean
  t: ReturnType<typeof useTranslations<'accessibility'>>
}

function PersonaButton({ persona, isActive, onClick, compact, t }: PersonaButtonProps) {
  const themeKey = THEME_MAP[persona.id] ?? persona.id

  return (
    <button
      role="radio"
      aria-checked={isActive}
      aria-label={t(`themes.${themeKey}` as Parameters<typeof t>[0])}
      onClick={(e) => onClick(persona, e)}
      className={cn(
        'relative flex items-center gap-1.5 rounded-full',
        'transition-all duration-200',
        compact
          ? 'flex-col px-2 py-2 text-[10px] rounded-[var(--radius-md)]'
          : 'px-3 py-1.5 text-xs',
        isActive
          ? 'bg-[var(--color-primary)] text-[var(--color-on-primary)] shadow-sm'
          : cn(
              'text-[var(--color-text)]',
              'hover:bg-[var(--color-surface-elevated)]'
            )
      )}
    >
      <span aria-hidden="true" className={compact ? 'text-base' : 'text-sm'}>
        {persona.icon}
      </span>
      <span className="font-medium whitespace-nowrap">
        {compact
          ? t(`themes.${themeKey}` as Parameters<typeof t>[0])
          : t(`hero_${persona.id}` as Parameters<typeof t>[0])}
      </span>
    </button>
  )
}
