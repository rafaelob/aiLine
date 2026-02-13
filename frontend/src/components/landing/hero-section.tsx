'use client'

import { useTranslations } from 'next-intl'
import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

interface HeroSectionProps {
  onStartDemo?: () => void
}

const STATS = [
  { key: 'stats_personas', value: '9' },
  { key: 'stats_languages', value: '3' },
  { key: 'stats_models', value: '3' },
  { key: 'stats_standards', value: 'BNCC + US' },
] as const

/**
 * Landing page hero section with animated headline, subtitle, stats, and CTA.
 * Uses CSS gradient animation for a premium background effect.
 * Respects reduced-motion via motion library.
 */
export function HeroSection({ onStartDemo }: HeroSectionProps) {
  const t = useTranslations('landing')

  return (
    <section
      className={cn(
        'relative overflow-hidden',
        'rounded-[var(--radius-lg)]',
        'px-6 py-16 md:px-12 md:py-24',
        'text-center'
      )}
      aria-labelledby="hero-title"
    >
      {/* Animated gradient background */}
      <div
        className={cn(
          'absolute inset-0 -z-10',
          'bg-gradient-to-br from-[var(--color-primary)] via-[var(--color-secondary)] to-[var(--color-primary)]',
          'bg-[length:200%_200%] animate-[gradientShift_8s_ease_infinite]',
          'opacity-90'
        )}
        aria-hidden="true"
      />

      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 -z-10 opacity-[0.07]"
        style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
          backgroundSize: '32px 32px',
        }}
        aria-hidden="true"
      />

      {/* Brand name */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <span className="inline-block text-sm font-bold tracking-[0.2em] uppercase text-white/80 mb-4">
          AiLine
        </span>
      </motion.div>

      {/* Main title */}
      <motion.h1
        id="hero-title"
        className={cn(
          'text-3xl md:text-5xl lg:text-6xl font-extrabold',
          'text-white leading-tight',
          'max-w-3xl mx-auto'
        )}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        {t('hero_title')}
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        className={cn(
          'mt-6 text-lg md:text-xl',
          'text-white/85 font-medium',
          'max-w-2xl mx-auto'
        )}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25 }}
      >
        {t('hero_subtitle')}
      </motion.p>

      {/* Stats badges */}
      <motion.div
        className="flex flex-wrap justify-center gap-3 mt-10"
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        {STATS.map(({ key, value }) => (
          <div
            key={key}
            className={cn(
              'flex items-center gap-2 px-4 py-2',
              'rounded-full',
              'bg-white/15 backdrop-blur-sm',
              'border border-white/20',
              'text-white text-sm font-medium'
            )}
          >
            <span className="font-bold">{value}</span>
            <span className="text-white/80">
              {t(key as Parameters<typeof t>[0])}
            </span>
          </div>
        ))}
      </motion.div>

      {/* CTA button */}
      <motion.div
        className="mt-10"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.55, type: 'spring', stiffness: 200 }}
      >
        <motion.button
          onClick={onStartDemo}
          whileTap={{ scale: 0.97 }}
          className={cn(
            'inline-flex items-center gap-2 px-8 py-4',
            'rounded-full text-lg font-bold',
            'bg-white text-[var(--color-primary)]',
            'shadow-[var(--shadow-xl)]',
            'hover:shadow-2xl hover:scale-105',
            'transition-all duration-300',
            'focus-visible:ring-4 focus-visible:ring-white/50'
          )}
        >
          {t('start_demo')}
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </motion.button>
      </motion.div>

      {/* Hackathon badge */}
      <motion.div
        className="mt-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.7 }}
      >
        <span
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1.5',
            'rounded-full text-xs font-semibold',
            'bg-white/10 border border-white/20 text-white/70'
          )}
        >
          {t('built_with')}
        </span>
      </motion.div>
    </section>
  )
}
