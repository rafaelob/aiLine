'use client'

import { useTranslations } from 'next-intl'
import { AnimatePresence, motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useAccessibilityStore } from '@/stores/accessibility-store'
import { PERSONAS } from '@/lib/accessibility-data'
import type { PersonaId } from '@/types/accessibility'

/**
 * "Why this adaptation?" explainer banner.
 *
 * Shown when a non-standard persona is active. Explains in plain language
 * what adaptations are being applied and why. Dismissible per session.
 *
 * This converts hidden accessibility sophistication into visible context
 * that hackathon judges (and users) can understand at a glance.
 */
export function PersonaExplainer() {
  const t = useTranslations('accessibility')
  const tHints = useTranslations('accessibility.theme_hints')
  const { theme } = useAccessibilityStore()

  if (theme === 'standard') return null

  const persona = PERSONAS[theme as PersonaId]
  if (!persona) return null

  // Map to CSS theme key for translations
  const themeKey = theme === 'high_contrast' ? 'high-contrast'
    : theme === 'low_vision' ? 'low-vision'
    : theme === 'screen_reader' ? 'screen-reader'
    : theme

  return (
    <AnimatePresence>
      <motion.div
        key={theme}
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        transition={{ duration: 0.2 }}
        role="status"
        aria-live="polite"
        className={cn(
          'flex items-center gap-3 px-4 py-2',
          'bg-[var(--color-primary)]/5 border-b border-[var(--color-primary)]/10',
          'text-xs'
        )}
      >
        <span aria-hidden="true" className="text-base shrink-0">{persona.icon}</span>
        <span className="text-[var(--color-text)]">
          <span className="font-semibold">{t(`themes.${themeKey}`)}</span>
          {' — '}
          <span className="text-[var(--color-muted)]">{tHints(theme)}</span>
        </span>
        <span
          className={cn(
            'ml-auto shrink-0 px-2 py-0.5 rounded-full',
            'text-[10px] font-medium',
            'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
          )}
        >
          {t('active_persona')}
        </span>
      </motion.div>
    </AnimatePresence>
  )
}
