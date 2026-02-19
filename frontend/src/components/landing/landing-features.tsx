'use client'

import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

interface Feature {
  title: string
  desc: string
  icon: 'pipeline' | 'a11y' | 'tutor' | 'models' | 'sign' | 'curriculum'
}

interface LandingFeaturesProps {
  title: string
  features: Feature[]
}

const iconColors: Record<Feature['icon'], string> = {
  pipeline: 'from-blue-500 to-violet-500',
  a11y: 'from-emerald-500 to-teal-500',
  tutor: 'from-orange-500 to-rose-500',
  models: 'from-violet-500 to-fuchsia-500',
  sign: 'from-cyan-500 to-blue-500',
  curriculum: 'from-amber-500 to-orange-500',
}

function FeatureIcon({ icon }: { icon: Feature['icon'] }) {
  const paths: Record<string, React.ReactNode> = {
    pipeline: (
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    ),
    a11y: (
      <>
        <circle cx="12" cy="4" r="2" stroke="currentColor" strokeWidth="2" fill="none" />
        <path d="M12 6v6M6 10l6 2 6-2M9 18l3-6 3 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      </>
    ),
    tutor: (
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    ),
    models: (
      <>
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" />
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2" stroke="currentColor" strokeWidth="2" fill="none" />
      </>
    ),
    sign: (
      <path d="M7 11V7a5 5 0 0 1 10 0v4M12 14v3M5 11h14a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    ),
    curriculum: (
      <>
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M8 7h8M8 11h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" />
      </>
    ),
  }

  return (
    <svg width="28" height="28" viewBox="0 0 24 24" aria-hidden="true" className="text-white">
      {paths[icon]}
    </svg>
  )
}

function FeatureCard({ feature, index }: { feature: Feature; index: number }) {
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  return (
    <motion.article
      initial={noMotion ? undefined : { opacity: 0, y: 24 }}
      whileInView={noMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={noMotion ? undefined : { delay: index * 0.1, duration: 0.5 }}
      className={cn(
        'group relative overflow-hidden rounded-2xl p-6',
        'glass card-hover gradient-border-glass aurora-glow',
        'flex flex-col gap-4'
      )}
    >
      {/* Hover gradient overlay */}
      <div
        className={cn(
          'absolute inset-0 opacity-0 transition-opacity duration-300',
          'group-hover:opacity-100 pointer-events-none'
        )}
        style={{
          background: 'radial-gradient(ellipse at 50% 0%, color-mix(in srgb, var(--color-primary) 6%, transparent) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />
      <motion.div
        className={cn(
          'relative flex items-center justify-center w-14 h-14 rounded-xl',
          'bg-gradient-to-br shadow-lg',
          iconColors[feature.icon]
        )}
        initial={noMotion ? undefined : { scale: 0.8 }}
        whileInView={noMotion ? undefined : { scale: [0.8, 1.05, 1] }}
        viewport={{ once: true, margin: '-40px' }}
        transition={noMotion ? undefined : { delay: index * 0.1 + 0.3, duration: 0.5, ease: 'easeOut' }}
        aria-hidden="true"
      >
        <FeatureIcon icon={feature.icon} />
      </motion.div>
      <h3 className="relative text-lg font-semibold text-[var(--color-text)]">
        {feature.title}
      </h3>
      <p className="relative text-sm text-[var(--color-muted)] leading-relaxed">
        {feature.desc}
      </p>
    </motion.article>
  )
}

/**
 * Bento-style feature grid with glass cards, gradient border on hover,
 * icon entrance animation, and scroll-triggered entrance.
 */
export function LandingFeatures({ title, features }: LandingFeaturesProps) {
  return (
    <section className="py-12 px-6" aria-labelledby="features-heading">
      <div className="max-w-5xl mx-auto">
        <h2
          id="features-heading"
          className="text-3xl sm:text-4xl font-bold text-center text-[var(--color-text)] mb-12"
        >
          {title}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <FeatureCard key={feature.icon} feature={feature} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
