'use client'

import { motion } from 'motion/react'

interface PageTransitionProps {
  children: React.ReactNode
}

/**
 * Wraps page content with a fade + slide-up entrance animation.
 * Respects prefers-reduced-motion via motion's built-in support.
 */
export function PageTransition({ children }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}
