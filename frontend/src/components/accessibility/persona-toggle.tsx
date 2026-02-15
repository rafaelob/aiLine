'use client'

import { useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useTheme } from '@/hooks/use-theme'
import { useViewTransition } from '@/hooks/use-view-transition'
import { PERSONA_LIST } from '@/lib/accessibility-data'
import type { PersonaId } from '@/types/accessibility'

/**
 * Animated persona selector with horizontal pill/chip layout.
 * Uses motion layoutId for smooth sliding indicator animation.
 * Uses View Transitions API for cross-fade theme morphing.
 * On select: sets data-theme on document.body and persists to localStorage.
 */
export function PersonaToggle() {
  const { activePersona, switchTheme } = useTheme()
  const { startTransition } = useViewTransition()
  const tp = useTranslations('personas')

  const handleSelect = useCallback(
    (personaId: PersonaId, e?: React.MouseEvent | React.KeyboardEvent) => {
      let x: number | undefined
      let y: number | undefined
      if (e) {
        const rect = e.currentTarget.getBoundingClientRect()
        x = rect.left + rect.width / 2
        y = rect.top + rect.height / 2
      }
      startTransition(
        () => { switchTheme(personaId) },
        { type: 'theme', x, y },
      )
    },
    [switchTheme, startTransition],
  )

  return (
    <nav
      role="radiogroup"
      aria-label={tp('select_label')}
      className="flex flex-wrap gap-2"
    >
      {PERSONA_LIST.map((persona) => {
        const isActive = activePersona === persona.id
        const personaLabel = tp(persona.label)
        const personaDesc = tp(persona.description)
        return (
          <button
            key={persona.id}
            role="radio"
            aria-checked={isActive}
            aria-label={`${personaLabel}: ${personaDesc}`}
            onClick={(e) => handleSelect(persona.id, e)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                handleSelect(persona.id, e)
              }
            }}
            className={cn(
              'relative flex items-center gap-2 rounded-full px-4 py-2',
              'text-sm font-medium transition-colors duration-200',
              'focus-visible:outline-2 focus-visible:outline-offset-2',
              'focus-visible:outline-[var(--color-primary)]',
              isActive
                ? 'text-[var(--color-on-primary)]'
                : 'bg-[var(--color-surface-elevated)] text-[var(--color-text)] hover:bg-[var(--color-border)]',
            )}
          >
            {isActive && (
              <motion.span
                layoutId="persona-pill"
                className="absolute inset-0 rounded-full bg-[var(--color-primary)]"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                aria-hidden="true"
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              <span aria-hidden="true">{persona.icon}</span>
              <span>{personaLabel}</span>
            </span>
          </button>
        )
      })}
    </nav>
  )
}
