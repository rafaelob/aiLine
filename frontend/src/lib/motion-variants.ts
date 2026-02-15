import type { Variants } from 'motion/react'

/**
 * Shared stagger animation variants used across plan, pipeline, and dashboard components.
 * Container uses opacity fade with staggered children; items slide up with spring physics.
 */

export const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
}

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 24, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: 'spring', stiffness: 200, damping: 24 },
  },
}
