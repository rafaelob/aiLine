'use client'

import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/cn'

interface LandingHowItWorksProps {
  title: string
  steps: {
    title: string
    description: string
  }[]
}

const STEP_ICONS = [
  // 1. Choose a Role
  (
    <svg key="role" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="text-white">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  // 2. Create or View Plans
  (
    <svg key="plans" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="text-white">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
      <path d="M12 18v-6" />
      <path d="M9 15h6" />
    </svg>
  ),
  // 3. AI Adapts Everything
  (
    <svg key="adapt" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="text-white">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  ),
  // 4. Track & Improve
  (
    <svg key="track" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="text-white">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
] as const

const STEP_GRADIENTS = [
  'from-blue-500 to-indigo-500',
  'from-emerald-500 to-teal-500',
  'from-orange-500 to-amber-500',
  'from-violet-500 to-purple-500',
] as const

function StepCard({
  step,
  index,
}: {
  step: { title: string; description: string }
  index: number
}) {
  const prefersReducedMotion = useReducedMotion()
  const noMotion = prefersReducedMotion ?? false

  return (
    <motion.article
      initial={noMotion ? undefined : { opacity: 0, y: 24 }}
      whileInView={noMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={noMotion ? undefined : { delay: index * 0.12, duration: 0.5 }}
      className={cn(
        'group relative overflow-hidden rounded-2xl p-6',
        'glass card-hover gradient-border-glass',
        'flex flex-col items-center text-center gap-4'
      )}
    >
      {/* Step number */}
      <div
        className="absolute top-3 right-4 text-5xl font-black opacity-[0.06] select-none"
        aria-hidden="true"
      >
        {index + 1}
      </div>

      {/* Icon */}
      <motion.div
        className={cn(
          'relative flex items-center justify-center w-14 h-14 rounded-xl',
          'bg-gradient-to-br shadow-lg',
          STEP_GRADIENTS[index]
        )}
        initial={noMotion ? undefined : { scale: 0.8 }}
        whileInView={noMotion ? undefined : { scale: [0.8, 1.05, 1] }}
        viewport={{ once: true, margin: '-40px' }}
        transition={
          noMotion
            ? undefined
            : { delay: index * 0.12 + 0.3, duration: 0.5, ease: 'easeOut' }
        }
        aria-hidden="true"
      >
        {STEP_ICONS[index]}
      </motion.div>

      <h3 className="relative text-lg font-semibold text-[var(--color-text)]">
        {step.title}
      </h3>
      <p className="relative text-sm text-[var(--color-muted)] leading-relaxed">
        {step.description}
      </p>
    </motion.article>
  )
}

/**
 * "How It Works" section with 4-step cards showing the AiLine workflow.
 * Glass morphism cards with numbered steps and animated entrance.
 */
export function LandingHowItWorks({ title, steps }: LandingHowItWorksProps) {
  return (
    <section
      className="py-12 px-6 bg-[var(--color-surface)]"
      aria-labelledby="how-it-works-heading"
    >
      <div className="max-w-5xl mx-auto">
        <h2
          id="how-it-works-heading"
          className="text-3xl sm:text-4xl font-bold text-center text-[var(--color-text)] mb-12"
        >
          {title}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <StepCard key={step.title} step={step} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
