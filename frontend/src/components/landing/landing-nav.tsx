'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { cn } from '@/lib/cn'

interface LandingNavProps {
  locale: string
  startDemo: string
}

/**
 * Floating glass navbar that appears on scroll.
 * Shows on focus-within so keyboard users can always reach it.
 */
export function LandingNav({ locale, startDemo }: LandingNavProps) {
  const [scrolled, setScrolled] = useState(false)
  const [focusWithin, setFocusWithin] = useState(false)
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false
  const tNav = useTranslations('nav')

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 80)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleFocus = useCallback(() => setFocusWithin(true), [])
  const handleBlur = useCallback(() => setFocusWithin(false), [])

  const visible = scrolled || focusWithin

  return (
    <motion.nav
      aria-label={tNav('landing_nav_label')}
      initial={noMotion ? undefined : { y: -80 }}
      animate={noMotion ? { opacity: visible ? 1 : 0 } : { y: visible ? 0 : -80 }}
      transition={noMotion ? { duration: 0 } : { type: 'spring', stiffness: 300, damping: 30 }}
      {...(!visible ? { inert: true } : {})}
      onFocus={handleFocus}
      onBlur={handleBlur}
      className={cn(
        'fixed top-0 left-0 right-0 z-50',
        'flex items-center justify-between px-6 py-3',
        'glass shadow-[var(--shadow-lg)]'
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-9 h-9 rounded-xl text-white font-bold text-sm"
          style={{
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
          }}
          aria-hidden="true"
        >
          A
        </div>
        <span className="font-bold text-lg gradient-text-animated">AiLine</span>
      </div>

      <div className="flex items-center gap-4">
        <Link
          href={`/${locale}/guide`}
          tabIndex={visible ? 0 : -1}
          className={cn(
            'px-4 py-2 rounded-xl',
            'text-sm font-semibold text-[var(--color-text)]',
            'hover:bg-[var(--color-surface-hover)] transition-colors duration-200',
            'focus-visible:shadow-[var(--focus-ring)]'
          )}
        >
          {tNav('guide')}
        </Link>

        <Link
          href={`/${locale}/dashboard`}
          tabIndex={visible ? 0 : -1}
          className={cn(
            'px-5 py-2.5 rounded-xl btn-shimmer btn-press',
            'text-sm font-semibold text-[var(--color-on-primary)]',
            'focus-visible:shadow-[var(--focus-ring)]'
          )}
          style={{ background: 'var(--gradient-hero)' }}
        >
          {startDemo}
        </Link>
      </div>
    </motion.nav>
  )
}
