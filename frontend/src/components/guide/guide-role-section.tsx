'use client'

import { useState, useCallback, useId } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface GuideItem {
  /** Unique key for this item */
  key: string
  /** Translated title */
  title: string
  /** Translated description (can contain paragraphs separated by \n) */
  description: string
  /** Icon component to render */
  icon: React.ReactNode
}

interface GuideRoleSectionProps {
  /** Section items to render as accordion */
  items: GuideItem[]
  /** Step numbering offset (default 1) */
  startIndex?: number
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

/**
 * Accordion section for a single role in the interactive guide.
 * Implements WAI-ARIA accordion pattern with keyboard navigation.
 * Each item shows a numbered step with icon, title, and expandable content.
 */
export function GuideRoleSection({ items, startIndex = 1 }: GuideRoleSectionProps) {
  const [openKey, setOpenKey] = useState<string | null>(null)
  const prefersReducedMotion = useReducedMotion()
  const groupId = useId()

  const toggle = useCallback((key: string) => {
    setOpenKey((prev) => (prev === key ? null : key))
  }, [])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, index: number) => {
      let targetIndex = -1
      if (e.key === 'ArrowDown') {
        targetIndex = (index + 1) % items.length
        e.preventDefault()
      } else if (e.key === 'ArrowUp') {
        targetIndex = (index - 1 + items.length) % items.length
        e.preventDefault()
      } else if (e.key === 'Home') {
        targetIndex = 0
        e.preventDefault()
      } else if (e.key === 'End') {
        targetIndex = items.length - 1
        e.preventDefault()
      }
      if (targetIndex >= 0) {
        const btn = document.getElementById(`${groupId}-trigger-${items[targetIndex].key}`)
        btn?.focus()
      }
    },
    [items, groupId],
  )

  return (
    <div className="space-y-3" role="region">
      {items.map((item, idx) => {
        const stepNum = startIndex + idx
        const isOpen = openKey === item.key
        const triggerId = `${groupId}-trigger-${item.key}`
        const panelId = `${groupId}-panel-${item.key}`

        return (
          <div
            key={item.key}
            className={cn(
              'glass rounded-xl overflow-hidden transition-shadow',
              isOpen && 'shadow-[var(--shadow-md)]',
            )}
          >
            {/* Accordion trigger */}
            <button
              id={triggerId}
              type="button"
              aria-expanded={isOpen}
              aria-controls={panelId}
              onClick={() => toggle(item.key)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className={cn(
                'w-full flex items-center gap-4 p-4 text-left',
                'hover:bg-[var(--color-surface-elevated)]/50 transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/50 focus-visible:rounded-xl',
              )}
            >
              {/* Step number */}
              <span
                className={cn(
                  'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center',
                  'text-sm font-bold text-[var(--color-on-primary)]',
                  'bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)]',
                )}
                aria-hidden="true"
              >
                {stepNum}
              </span>

              {/* Icon */}
              <span className="flex-shrink-0 w-5 h-5 text-[var(--color-primary)]" aria-hidden="true">
                {item.icon}
              </span>

              {/* Title */}
              <span className="flex-1 font-semibold text-[var(--color-text)]">
                {item.title}
              </span>

              {/* Chevron */}
              <svg
                className={cn(
                  'w-5 h-5 text-[var(--color-muted)] transition-transform',
                  isOpen && 'rotate-180',
                )}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {/* Accordion panel */}
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  id={panelId}
                  role="region"
                  aria-labelledby={triggerId}
                  initial={prefersReducedMotion ? false : { height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={prefersReducedMotion ? undefined : { height: 0, opacity: 0 }}
                  transition={{ duration: prefersReducedMotion ? 0 : 0.25, ease: 'easeInOut' }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-5 pt-1 pl-[4.25rem]">
                    {item.description.split('\n').map((paragraph, pIdx) => (
                      <p
                        key={pIdx}
                        className="text-[var(--color-muted)] leading-relaxed mb-2 last:mb-0"
                      >
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}
