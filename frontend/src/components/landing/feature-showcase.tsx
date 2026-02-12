'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

const FEATURES = [
  {
    key: 'pipeline',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    key: 'accessibility',
    icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
  },
  {
    key: 'sign',
    icon: 'M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11',
  },
  {
    key: 'curriculum',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  },
  {
    key: 'tutor',
    icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
  },
  {
    key: 'models',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
  },
] as const

const TECH_STACK = [
  'Next.js 16',
  'FastAPI',
  'Pydantic AI',
  'LangGraph',
  'Claude',
  'GPT',
  'Gemini',
]

/**
 * Feature showcase cards and tech stack badge bar for the landing page.
 * 6 feature cards with staggered scroll-reveal animation.
 */
export function FeatureShowcase() {
  const t = useTranslations('landing')

  return (
    <div className="mt-12 space-y-12">
      {/* Features heading */}
      <motion.h2
        className={cn(
          'text-2xl md:text-3xl font-bold text-center',
          'text-[var(--color-text)]'
        )}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {t('features_title')}
      </motion.h2>

      {/* Feature cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURES.map((feature, i) => (
          <motion.article
            key={feature.key}
            className={cn(
              'glass rounded-[var(--radius-lg)] p-6',
              'border border-[var(--color-border)]',
              'hover:shadow-[var(--shadow-lg)]',
              'transition-shadow duration-300',
              'group'
            )}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 * i }}
          >
            {/* Icon */}
            <div
              className={cn(
                'flex items-center justify-center w-12 h-12',
                'rounded-[var(--radius-md)]',
                'bg-[var(--color-primary)]/10',
                'group-hover:bg-[var(--color-primary)]/20',
                'transition-colors duration-300'
              )}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-primary)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d={feature.icon} />
              </svg>
            </div>

            {/* Title */}
            <h3 className="mt-4 text-base font-bold text-[var(--color-text)]">
              {t(`feature_${feature.key}` as Parameters<typeof t>[0])}
            </h3>

            {/* Description */}
            <p className="mt-2 text-sm text-[var(--color-muted)] leading-relaxed">
              {t(`feature_${feature.key}_desc` as Parameters<typeof t>[0])}
            </p>
          </motion.article>
        ))}
      </div>

      {/* Tech stack bar */}
      <motion.div
        className="flex flex-col items-center gap-4"
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.7 }}
      >
        <h3 className="text-sm font-semibold text-[var(--color-muted)] uppercase tracking-wider">
          {t('tech_title')}
        </h3>
        <div className="flex flex-wrap justify-center gap-2">
          {TECH_STACK.map((tech) => (
            <span
              key={tech}
              className={cn(
                'px-3 py-1.5 rounded-full text-xs font-medium',
                'bg-[var(--color-surface-elevated)]',
                'text-[var(--color-text)]',
                'border border-[var(--color-border)]'
              )}
            >
              {tech}
            </span>
          ))}
        </div>

        {/* Built with Opus badge */}
        <div
          className={cn(
            'mt-2 inline-flex items-center gap-2 px-4 py-2',
            'rounded-full',
            'bg-gradient-to-r from-[var(--color-primary)]/10 to-[var(--color-secondary)]/10',
            'border border-[var(--color-primary)]/20',
            'text-sm font-semibold text-[var(--color-primary)]'
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
            aria-hidden="true"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          {t('built_with')}
        </div>
      </motion.div>
    </div>
  )
}
