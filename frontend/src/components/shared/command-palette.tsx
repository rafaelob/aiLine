'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import type { Locale } from '@/i18n/routing'

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

interface CommandItem {
  id: string
  label: string
  category: 'navigation' | 'quickActions' | 'accessibility' | 'language'
  icon: React.ReactNode
  action: () => void
}

/**
 * Command Palette (Cmd+K / Ctrl+K).
 * Combobox ARIA pattern with fuzzy search, grouped results,
 * keyboard navigation, and glass morphism overlay.
 */
export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const t = useTranslations('commandPalette')
  const tNav = useTranslations('nav')
  const tDash = useTranslations('dashboard')
  const tThemes = useTranslations('accessibility.themes')
  const tExports = useTranslations('exports')
  const router = useRouter()
  const pathname = usePathname()
  const { setTheme } = useAccessibilityStore()

  const localeMatch = pathname.match(/^\/([^/]+)/)
  const localePrefix = localeMatch ? `/${localeMatch[1]}` : '/pt-BR'

  const navigate = useCallback(
    (path: string) => {
      router.push(`${localePrefix}${path}` as Parameters<typeof router.push>[0])
      setOpen(false)
    },
    [router, localePrefix],
  )

  const switchLocale = useCallback(
    (locale: Locale) => {
      const pathWithoutLocale = pathname.replace(/^\/[^/]+/, '')
      router.push(`/${locale}${pathWithoutLocale}` as Parameters<typeof router.push>[0])
      setOpen(false)
    },
    [router, pathname],
  )

  const switchTheme = useCallback(
    (themeId: string) => {
      setTheme(themeId)
      if (typeof document !== 'undefined') {
        document.body.setAttribute('data-theme', themeId)
        document.documentElement.setAttribute('data-theme', themeId)
      }
      setOpen(false)
    },
    [setTheme],
  )

  const items: CommandItem[] = useMemo(
    () => [
      // Navigation
      { id: 'nav-dashboard', label: tNav('dashboard'), category: 'navigation', icon: <NavIcon d="M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z" />, action: () => navigate('') },
      { id: 'nav-plans', label: tNav('plans'), category: 'navigation', icon: <NavIcon d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />, action: () => navigate('/plans') },
      { id: 'nav-tutors', label: tNav('tutors'), category: 'navigation', icon: <NavIcon d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />, action: () => navigate('/tutors') },
      { id: 'nav-materials', label: tNav('materials'), category: 'navigation', icon: <NavIcon d="M4 19.5A2.5 2.5 0 016.5 17H20" />, action: () => navigate('/materials') },
      { id: 'nav-progress', label: tNav('progress'), category: 'navigation', icon: <NavIcon d="M18 20V10M12 20V4M6 20v-6" />, action: () => navigate('/progress') },
      { id: 'nav-sign-language', label: tNav('sign_language'), category: 'navigation', icon: <NavIcon d="M18 11V6a2 2 0 00-4 0v1" />, action: () => navigate('/sign-language') },
      { id: 'nav-exports', label: tExports('title'), category: 'navigation', icon: <NavIcon d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />, action: () => navigate('/exports') },
      { id: 'nav-observability', label: tNav('observability'), category: 'navigation', icon: <NavIcon d="M22 12h-4l-3 9L9 3l-3 9H2" />, action: () => navigate('/observability') },
      { id: 'nav-settings', label: tNav('settings'), category: 'navigation', icon: <NavIcon d="M12 15a3 3 0 100-6 3 3 0 000 6z" />, action: () => navigate('/settings') },

      // Quick Actions
      { id: 'qa-generate-plan', label: tDash('create_plan'), category: 'quickActions', icon: <ActionIcon d="M12 5v14M5 12h14" />, action: () => navigate('/plans') },
      { id: 'qa-start-tutor', label: tDash('start_tutor'), category: 'quickActions', icon: <ActionIcon d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />, action: () => navigate('/tutors') },
      { id: 'qa-upload-material', label: tDash('upload_material'), category: 'quickActions', icon: <ActionIcon d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />, action: () => navigate('/materials') },

      // Accessibility — theme switching
      ...THEME_IDS.map((themeId) => ({
        id: `a11y-${themeId}`,
        label: tThemes(themeId as Parameters<typeof tThemes>[0]),
        category: 'accessibility' as const,
        icon: <ThemeIcon />,
        action: () => switchTheme(themeId),
      })),

      // Language switching
      { id: 'lang-en', label: 'English', category: 'language', icon: <LangIcon />, action: () => switchLocale('en') },
      { id: 'lang-pt-BR', label: 'Portugues (BR)', category: 'language', icon: <LangIcon />, action: () => switchLocale('pt-BR') },
      { id: 'lang-es', label: 'Espanol', category: 'language', icon: <LangIcon />, action: () => switchLocale('es') },
    ],
    [tNav, tDash, tThemes, tExports, navigate, switchLocale, switchTheme],
  )

  const filtered = useMemo(() => {
    if (!query.trim()) return items
    const lower = query.toLowerCase()
    return items.filter((item) => item.label.toLowerCase().includes(lower))
  }, [items, query])

  const grouped = useMemo(() => {
    const categories = ['navigation', 'quickActions', 'accessibility', 'language'] as const
    return categories
      .map((cat) => ({
        key: cat,
        label: t(cat),
        items: filtered.filter((i) => i.category === cat),
      }))
      .filter((g) => g.items.length > 0)
  }, [filtered, t])

  const flatItems = useMemo(() => grouped.flatMap((g) => g.items), [grouped])

  // Global keyboard shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Focus input when opened
  useEffect(() => {
    if (open) {
      // Use microtask to avoid cascading render warning from React Compiler
      queueMicrotask(() => {
        setQuery('')
        setActiveIndex(0)
      })
      // Small delay for animation
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  // Scroll active item into view
  useEffect(() => {
    if (!open || flatItems.length === 0) return
    const activeItem = flatItems[activeIndex]
    if (!activeItem) return
    const el = document.getElementById(`cmd-item-${activeItem.id}`)
    el?.scrollIntoView?.({ block: 'nearest' })
  }, [activeIndex, open, flatItems])

  // Active index is clamped to filtered results length
  const effectiveIndex = activeIndex >= flatItems.length ? 0 : activeIndex

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        setOpen(false)
        return
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setActiveIndex((prev) => (prev + 1) % Math.max(flatItems.length, 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setActiveIndex((prev) => (prev - 1 + flatItems.length) % Math.max(flatItems.length, 1))
        return
      }
      if (e.key === 'Enter') {
        e.preventDefault()
        const item = flatItems[activeIndex]
        item?.action()
        return
      }
    },
    [flatItems, activeIndex],
  )

  const activeItem = flatItems[effectiveIndex]

  return (
    <AnimatePresence>
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
          data-testid="command-palette"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />

          {/* Dialog */}
          <motion.div
            role="dialog"
            aria-label={t('placeholder')}
            aria-modal="true"
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'relative w-full max-w-lg mx-4',
              'rounded-[var(--radius-lg)] overflow-hidden',
              'shadow-[var(--shadow-xl)]',
              'glass',
              'border border-[var(--color-border)]/20',
            )}
            onKeyDown={handleKeyDown}
          >
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--color-border)]/30">
              <SearchIcon />
              <input
                ref={inputRef}
                type="text"
                role="combobox"
                aria-expanded={true}
                aria-controls="cmd-listbox"
                aria-activedescendant={activeItem ? `cmd-item-${activeItem.id}` : undefined}
                aria-autocomplete="list"
                placeholder={t('placeholder')}
                value={query}
                onChange={(e) => { setQuery(e.target.value); setActiveIndex(0) }}
                className={cn(
                  'flex-1 bg-transparent border-none outline-none',
                  'text-[var(--color-text)] placeholder:text-[var(--color-muted)]',
                  'text-sm',
                )}
              />
              <kbd
                className={cn(
                  'hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5',
                  'rounded-[var(--radius-sm)] text-[10px] font-medium',
                  'bg-[var(--color-surface-elevated)] text-[var(--color-muted)]',
                  'border border-[var(--color-border)]/50',
                )}
              >
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div
              id="cmd-listbox"
              ref={listRef}
              role="listbox"
              aria-label={t('placeholder')}
              className="max-h-72 overflow-y-auto p-2"
            >
              {flatItems.length === 0 ? (
                <p className="px-3 py-6 text-center text-sm text-[var(--color-muted)]">
                  {t('noResults')}
                </p>
              ) : (
                grouped.map((group) => (
                  <div key={group.key} role="group" aria-label={group.label}>
                    <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                      {group.label}
                    </p>
                    {group.items.map((item) => {
                      const isActive = activeItem?.id === item.id
                      return (
                        <div
                          key={item.id}
                          id={`cmd-item-${item.id}`}
                          role="option"
                          aria-selected={isActive}
                          onClick={() => item.action()}
                          onMouseEnter={() =>
                            setActiveIndex(flatItems.indexOf(item))
                          }
                          className={cn(
                            'flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] cursor-pointer',
                            'transition-colors duration-100',
                            isActive
                              ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
                              : 'text-[var(--color-text)] hover:bg-[var(--color-surface-elevated)]',
                          )}
                        >
                          <span className="shrink-0 w-5 h-5" aria-hidden="true">
                            {item.icon}
                          </span>
                          <span className="text-sm font-medium truncate">
                            {item.label}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                ))
              )}
            </div>

            {/* Footer hint */}
            <div className="flex items-center gap-4 px-4 py-2 border-t border-[var(--color-border)]/30 text-[10px] text-[var(--color-muted)]">
              <span className="flex items-center gap-1">
                <kbd className="px-1 rounded bg-[var(--color-surface-elevated)] border border-[var(--color-border)]/50 font-mono">
                  &uarr;&darr;
                </kbd>
                navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 rounded bg-[var(--color-surface-elevated)] border border-[var(--color-border)]/50 font-mono">
                  &crarr;
                </kbd>
                select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1 rounded bg-[var(--color-surface-elevated)] border border-[var(--color-border)]/50 font-mono">
                  esc
                </kbd>
                close
              </span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

/** Trigger button for topbar. */
export function CommandPaletteTrigger() {
  const t = useTranslations('commandPalette')

  function handleClick() {
    // Dispatch Cmd+K to trigger the palette
    document.dispatchEvent(
      new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
        bubbles: true,
      }),
    )
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={t('placeholder')}
      className={cn(
        'flex items-center gap-2 px-2.5 py-2',
        'rounded-[var(--radius-md)]',
        'text-sm text-[var(--color-muted)]',
        'hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text)]',
        'transition-all duration-200',
      )}
    >
      <SearchIcon />
      <span className="hidden sm:inline text-xs font-medium">{t('hint')}</span>
    </button>
  )
}

/* ===== Icon Components ===== */

function SearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  )
}

function NavIcon({ d }: { d: string }) {
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
      <path d={d} />
    </svg>
  )
}

function ActionIcon({ d }: { d: string }) {
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
      <path d={d} />
    </svg>
  )
}

function ThemeIcon() {
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
      <circle cx="12" cy="12" r="5" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  )
}

function LangIcon() {
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
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
    </svg>
  )
}
