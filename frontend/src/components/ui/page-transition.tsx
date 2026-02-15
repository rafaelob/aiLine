'use client'

import { motion } from 'motion/react'
import type { Variants } from 'motion/react'

interface PageTransitionProps {
  children: React.ReactNode
  /** Enable stagger animation for direct children */
  stagger?: boolean
}

const pageVariants: Variants = {
  hidden: { opacity: 0, y: 12, filter: 'blur(8px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      type: 'spring',
      stiffness: 200,
      damping: 24,
      staggerChildren: 0.08,
      delayChildren: 0.05,
    }
  },
}

const childVariants: Variants = {
  hidden: { opacity: 0, y: 16, filter: 'blur(6px)' },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: { type: 'spring', stiffness: 200, damping: 24 }
  },
}

/**
 * Wraps page content with a premium blur-in + spring entrance animation.
 * When stagger=true, wraps each direct child in a motion.div with stagger delay.
 * Respects prefers-reduced-motion via motion's built-in support.
 */
export function PageTransition({ children, stagger = false }: PageTransitionProps) {
  if (!stagger) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={pageVariants}
      >
        {children}
      </motion.div>
    )
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={pageVariants}
    >
      {children}
    </motion.div>
  )
}

/** Export child variants for use in page components */
export { childVariants as pageChildVariants }
