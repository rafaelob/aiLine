'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { motion, AnimatePresence } from 'motion/react'
import { cn } from '@/lib/cn'
import type { SmartRouterRationale } from '@/types/trace'

interface SmartRouterCardProps {
  rationale: SmartRouterRationale | null
  className?: string
}

const WEIGHT_KEYS = ['tokens', 'structured', 'tools', 'history', 'intent'] as const

/**
 * Small expandable card showing "Why this model?" rationale.
 * Displays task_type, weighted_scores breakdown, and model selected.
 */
export function SmartRouterCard({ rationale, className }: SmartRouterCardProps) {
  const t = useTranslations('smart_router')
  const [isExpanded, setIsExpanded] = useState(false)

  if (!rationale) return null

  return (
    <div className={cn('inline-flex flex-col', className)}>
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        className={cn(
          'inline-flex items-center gap-1.5 px-2 py-1',
          'rounded-full text-[10px] font-semibold glass',
          'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)]',
          'hover:bg-[var(--color-secondary)]/20 transition-colors',
          'focus-visible:outline-2 focus-visible:outline-offset-2',
          'focus-visible:outline-[var(--color-primary)]'
        )}
        aria-label={t('why_model')}
      >
        <ModelIcon />
        <span>{rationale.model_selected}</span>
        <svg
          width="10"
          height="10"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={cn('transition-transform duration-150', isExpanded && 'rotate-180')}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div
              className={cn(
                'mt-1 p-3 rounded-xl',
                'glass card-hover',
                'shadow-[var(--shadow-md)]',
                'text-xs'
              )}
              role="tooltip"
            >
              <p className="font-semibold text-[var(--color-text)] mb-2">
                {t('why_model')}
              </p>

              <div className="space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-[var(--color-muted)]">{t('task_type')}</span>
                  <span className="font-mono text-[var(--color-text)]">{rationale.task_type}</span>
                </div>

                {WEIGHT_KEYS.map((key) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[var(--color-muted)] w-16 shrink-0">{t(key)}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-[var(--color-border)]">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, rationale.weighted_scores[key] * 100)}%`,
                          background: 'linear-gradient(90deg, var(--color-secondary), var(--color-primary))',
                        }}
                      />
                    </div>
                    <span className="font-mono text-[10px] text-[var(--color-muted)] w-8 text-right">
                      {(rationale.weighted_scores[key] * 100).toFixed(0)}
                    </span>
                  </div>
                ))}

                <div className="flex justify-between pt-2 mt-1 border-t border-[var(--color-border)] glass rounded-lg px-2 py-1">
                  <span className="font-semibold text-[var(--color-text)]">{t('total')}</span>
                  <span className="font-mono font-semibold text-[var(--color-text)]">
                    {(rationale.total_score * 100).toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ModelIcon() {
  return (
    <div
      className="flex items-center justify-center w-4 h-4 rounded-full icon-orb"
      style={{
        background: 'linear-gradient(135deg, var(--color-secondary), var(--color-primary))',
      }}
      aria-hidden="true"
    >
      <svg
        width="8"
        height="8"
        viewBox="0 0 24 24"
        fill="none"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    </div>
  )
}
