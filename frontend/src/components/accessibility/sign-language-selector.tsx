'use client'

import { useState, useRef, useCallback, useEffect, useId } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

/* ------------------------------------------------------------------ */
/*  Sign language definitions (mirrors backend registry)               */
/* ------------------------------------------------------------------ */

export interface SignLanguageOption {
  code: string
  name: string
  nameNative: string
  country: string
  flag: string
  estimatedUsers: string
}

const SIGN_LANGUAGES: SignLanguageOption[] = [
  {
    code: 'asl',
    name: 'American Sign Language',
    nameNative: 'American Sign Language',
    country: 'United States',
    flag: '\u{1F1FA}\u{1F1F8}',
    estimatedUsers: '500K - 2M',
  },
  {
    code: 'bsl',
    name: 'British Sign Language',
    nameNative: 'British Sign Language',
    country: 'United Kingdom',
    flag: '\u{1F1EC}\u{1F1E7}',
    estimatedUsers: '150K+',
  },
  {
    code: 'libras',
    name: 'Brazilian Sign Language',
    nameNative: 'Lingua Brasileira de Sinais',
    country: 'Brazil',
    flag: '\u{1F1E7}\u{1F1F7}',
    estimatedUsers: '5M+',
  },
  {
    code: 'lsf',
    name: 'French Sign Language',
    nameNative: 'Langue des Signes Fran\u00e7aise',
    country: 'France',
    flag: '\u{1F1EB}\u{1F1F7}',
    estimatedUsers: '100K+',
  },
  {
    code: 'dgs',
    name: 'German Sign Language',
    nameNative: 'Deutsche Geb\u00e4rdensprache',
    country: 'Germany',
    flag: '\u{1F1E9}\u{1F1EA}',
    estimatedUsers: '200K+',
  },
  {
    code: 'lse',
    name: 'Spanish Sign Language',
    nameNative: 'Lengua de Signos Espa\u00f1ola',
    country: 'Spain',
    flag: '\u{1F1EA}\u{1F1F8}',
    estimatedUsers: '100K+',
  },
  {
    code: 'lgp',
    name: 'Portuguese Sign Language',
    nameNative: 'Lingua Gestual Portuguesa',
    country: 'Portugal',
    flag: '\u{1F1F5}\u{1F1F9}',
    estimatedUsers: '60K+',
  },
  {
    code: 'isl',
    name: 'Irish Sign Language',
    nameNative: 'Teanga Chomhartha\u00edochta na h\u00c9ireann',
    country: 'Ireland',
    flag: '\u{1F1EE}\u{1F1EA}',
    estimatedUsers: '5K+',
  },
]

/* ------------------------------------------------------------------ */
/*  Component props                                                    */
/* ------------------------------------------------------------------ */

interface SignLanguageSelectorProps {
  value?: string
  onChange?: (code: string) => void
  label?: string
  className?: string
}

/**
 * Dropdown selector for choosing one of 8 supported sign languages.
 * Shows flag, language name, native name, and estimated user count.
 * Fully accessible with keyboard navigation and ARIA attributes.
 */
export function SignLanguageSelector({
  value = 'asl',
  onChange,
  label = 'Sign Language',
  className,
}: SignLanguageSelectorProps) {
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const [isOpen, setIsOpen] = useState(false)
  const [focusIndex, setFocusIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const listboxRef = useRef<HTMLUListElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const selected =
    SIGN_LANGUAGES.find((sl) => sl.code === value) ?? SIGN_LANGUAGES[0]

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return

    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
        setFocusIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return

    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setIsOpen(false)
        setFocusIndex(-1)
        buttonRef.current?.focus()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  // Scroll focused item into view
  useEffect(() => {
    if (!isOpen || focusIndex < 0) return
    const items = listboxRef.current?.querySelectorAll('[role="option"]')
    items?.[focusIndex]?.scrollIntoView({ block: 'nearest' })
  }, [isOpen, focusIndex])

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => {
      if (!prev) {
        // Opening: set focus index to current selection
        const idx = SIGN_LANGUAGES.findIndex((sl) => sl.code === value)
        setFocusIndex(idx >= 0 ? idx : 0)
      }
      return !prev
    })
  }, [value])

  const handleSelect = useCallback(
    (code: string) => {
      onChange?.(code)
      setIsOpen(false)
      setFocusIndex(-1)
      buttonRef.current?.focus()
    },
    [onChange],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen) {
        if (
          e.key === 'ArrowDown' ||
          e.key === 'ArrowUp' ||
          e.key === 'Enter' ||
          e.key === ' '
        ) {
          e.preventDefault()
          handleToggle()
        }
        return
      }

      switch (e.key) {
        case 'ArrowDown': {
          e.preventDefault()
          setFocusIndex((prev) =>
            prev < SIGN_LANGUAGES.length - 1 ? prev + 1 : 0,
          )
          break
        }
        case 'ArrowUp': {
          e.preventDefault()
          setFocusIndex((prev) =>
            prev > 0 ? prev - 1 : SIGN_LANGUAGES.length - 1,
          )
          break
        }
        case 'Home': {
          e.preventDefault()
          setFocusIndex(0)
          break
        }
        case 'End': {
          e.preventDefault()
          setFocusIndex(SIGN_LANGUAGES.length - 1)
          break
        }
        case 'Enter':
        case ' ': {
          e.preventDefault()
          if (focusIndex >= 0 && focusIndex < SIGN_LANGUAGES.length) {
            handleSelect(SIGN_LANGUAGES[focusIndex].code)
          }
          break
        }
      }
    },
    [isOpen, focusIndex, handleToggle, handleSelect],
  )

  const instanceId = useId()
  const listboxId = `sl-listbox-${instanceId}`
  const labelId = `sl-label-${instanceId}`

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {/* Label */}
      <span
        id={labelId}
        className="block text-sm font-medium text-[var(--color-text)] mb-1.5"
      >
        {label}
      </span>

      {/* Trigger button */}
      <button
        ref={buttonRef}
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={listboxId}
        aria-labelledby={labelId}
        aria-activedescendant={isOpen && focusIndex >= 0 ? `sl-option-${SIGN_LANGUAGES[focusIndex]?.code}` : undefined}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={cn(
          'w-full flex items-center gap-3 px-4 py-3 rounded-xl',
          'bg-[var(--color-surface)] border border-[var(--color-border)]',
          'text-sm text-[var(--color-text)]',
          'input-focus-ring',
          'transition-colors duration-200',
          'hover:border-[var(--color-primary)]',
          'cursor-pointer',
        )}
      >
        <span className="text-lg shrink-0" aria-hidden="true">
          {selected.flag}
        </span>
        <span className="flex-1 text-left truncate">
          {selected.name}
        </span>
        <svg
          className={cn(
            'w-4 h-4 shrink-0 text-[var(--color-muted)] transition-transform duration-200',
            isOpen && 'rotate-180',
          )}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {/* Dropdown listbox */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={
              noMotion ? undefined : { opacity: 0, y: -8, scale: 0.98 }
            }
            animate={
              noMotion ? undefined : { opacity: 1, y: 0, scale: 1 }
            }
            exit={
              noMotion ? undefined : { opacity: 0, y: -8, scale: 0.98 }
            }
            transition={
              noMotion ? undefined : { duration: 0.15 }
            }
            className={cn(
              'absolute z-50 mt-2 w-full rounded-xl',
              'glass border border-[var(--color-border)]',
              'shadow-xl overflow-hidden',
            )}
          >
            {/* Screen reader count announcement */}
            <div className="sr-only" aria-live="polite" aria-atomic="true">
              {SIGN_LANGUAGES.length} {label}
            </div>
            <ul
              ref={listboxRef}
              id={listboxId}
              role="listbox"
              aria-labelledby={labelId}
              className="max-h-80 overflow-y-auto py-1"
            >
              {SIGN_LANGUAGES.map((sl, idx) => {
                const isSelected = sl.code === value
                const isFocused = idx === focusIndex

                return (
                  <li
                    key={sl.code}
                    id={`sl-option-${sl.code}`}
                    role="option"
                    aria-selected={isSelected}
                    data-focused={isFocused || undefined}
                    onClick={() => handleSelect(sl.code)}
                    onMouseEnter={() => setFocusIndex(idx)}
                    className={cn(
                      'flex items-start gap-3 px-4 py-3 cursor-pointer',
                      'transition-colors duration-100',
                      isFocused && 'bg-[var(--color-surface-elevated)]',
                      isSelected &&
                        'bg-[color-mix(in_srgb,var(--color-primary)_8%,transparent)]',
                    )}
                  >
                    <span
                      className="text-xl shrink-0 mt-0.5"
                      aria-hidden="true"
                    >
                      {sl.flag}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--color-text)] truncate">
                          {sl.name}
                        </span>
                        {isSelected && (
                          <svg
                            className="w-4 h-4 text-[var(--color-primary)] shrink-0"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                          >
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        )}
                      </div>
                      <p className="text-xs text-[var(--color-muted)] truncate">
                        {sl.nameNative}
                      </p>
                      <div className="mt-1 flex items-center gap-3 text-[10px] text-[var(--color-muted)]">
                        <span>{sl.country}</span>
                        <span
                          className="w-px h-3 bg-[var(--color-border)]"
                          aria-hidden="true"
                        />
                        <span>{sl.estimatedUsers}</span>
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export { SIGN_LANGUAGES }
