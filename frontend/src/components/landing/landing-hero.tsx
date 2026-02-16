'use client'

import { motion, useReducedMotion } from 'motion/react'
import Link from 'next/link'
import { cn } from '@/lib/cn'

interface LandingHeroProps {
  locale: string
  title: string
  subtitle: string
  cta: string
}

/**
 * Full-screen hero section with animated mesh gradient background,
 * animated tagline, and glass CTA button.
 */
export function LandingHero({ locale, title, subtitle, cta }: LandingHeroProps) {
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  return (
    <section
      className={cn(
        'relative flex flex-col items-center justify-center text-center',
        'min-h-[90vh] px-6 py-20 overflow-hidden',
        'mesh-gradient-hero hero-noise'
      )}
      style={{ backgroundColor: 'var(--color-primary)' }}
      aria-labelledby="hero-heading"
    >
      {/* Decorative floating shapes */}
      <div
        className="absolute -top-20 -right-20 w-72 h-72 rounded-full opacity-10 animate-float-slow"
        style={{ background: 'rgba(255,255,255,0.3)' }}
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-16 -left-16 w-56 h-56 rounded-full opacity-10 animate-float-medium"
        style={{ background: 'rgba(255,255,255,0.25)' }}
        aria-hidden="true"
      />
      <div
        className="absolute top-1/3 right-1/3 w-32 h-32 rounded-full opacity-5 animate-float-slow"
        style={{ background: 'rgba(255,255,255,0.4)', animationDelay: '-3s' }}
        aria-hidden="true"
      />

      <div className="relative z-10 max-w-3xl mx-auto">
        {/* Logo orb with glow pulse */}
        <motion.div
          initial={noMotion ? undefined : { opacity: 0, scale: 0.8 }}
          animate={noMotion ? undefined : { opacity: 1, scale: 1 }}
          transition={noMotion ? undefined : { duration: 0.5, type: 'spring', stiffness: 200 }}
          className="relative mx-auto mb-8 w-20 h-20"
          aria-hidden="true"
        >
          {/* Glow ring behind orb */}
          <div
            className="absolute inset-0 rounded-2xl animate-hero-orb-glow"
            style={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.3), rgba(255,255,255,0.05))',
              filter: 'blur(12px)',
            }}
          />
          <div
            className="relative flex items-center justify-center w-full h-full rounded-2xl text-white font-bold text-3xl"
            style={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.25), rgba(255,255,255,0.05))',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255,255,255,0.25)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.2)',
            }}
          >
            A
          </div>
        </motion.div>

        <motion.h1
          id="hero-heading"
          initial={noMotion ? undefined : { opacity: 0, y: 20 }}
          animate={noMotion ? undefined : { opacity: 1, y: 0 }}
          transition={noMotion ? undefined : { delay: 0.15, duration: 0.5 }}
          className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight hero-title-gradient"
        >
          {title}
        </motion.h1>

        <motion.p
          initial={noMotion ? undefined : { opacity: 0, y: 16 }}
          animate={noMotion ? undefined : { opacity: 1, y: 0 }}
          transition={noMotion ? undefined : { delay: 0.3, duration: 0.5 }}
          className="mt-6 text-lg sm:text-xl max-w-xl mx-auto"
          style={{ color: 'rgba(255, 255, 255, 0.95)' }}
        >
          {subtitle}
        </motion.p>

        <motion.div
          initial={noMotion ? undefined : { opacity: 0, y: 16 }}
          animate={noMotion ? undefined : { opacity: 1, y: 0 }}
          transition={noMotion ? undefined : { delay: 0.45, duration: 0.5 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link
            href={`/${locale}/dashboard`}
            className={cn(
              'inline-flex items-center gap-2 px-8 py-4',
              'rounded-2xl btn-shimmer btn-press border-beam',
              'text-base font-semibold',
              'text-[var(--color-primary)] bg-white',
              'shadow-xl hover:shadow-2xl hover:scale-[1.02]',
              'transition-all duration-300',
              'focus-visible:ring-4 focus-visible:ring-white/50'
            )}
          >
            {cta}
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 10h10M12 5l5 5-5 5" />
            </svg>
          </Link>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={noMotion ? undefined : { opacity: 0 }}
        animate={noMotion ? undefined : { opacity: 1 }}
        transition={noMotion ? undefined : { delay: 1, duration: 0.8 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        aria-hidden="true"
      >
        <motion.div
          animate={noMotion ? undefined : { y: [0, 8, 0] }}
          transition={noMotion ? undefined : { repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.5">
            <path d="M12 5v14M5 12l7 7 7-7" />
          </svg>
        </motion.div>
      </motion.div>
    </section>
  )
}
