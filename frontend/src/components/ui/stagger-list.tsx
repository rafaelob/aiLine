'use client'

import { motion } from 'motion/react'

interface StaggerListProps {
  children: React.ReactNode
  className?: string
  /** Delay between each child animation (seconds) */
  staggerDelay?: number
}

export const staggerItemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring' as const, stiffness: 200, damping: 20 },
  },
}

/**
 * Container that staggers entrance animations for child elements.
 * Wrap each child with <motion.div variants={staggerItemVariants}>.
 */
export function StaggerList({ children, className, staggerDelay = 0.08 }: StaggerListProps) {
  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: staggerDelay },
        },
      }}
      initial="hidden"
      animate="visible"
    >
      {children}
    </motion.div>
  )
}

/**
 * Individual item within a StaggerList.
 */
export function StaggerItem({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <motion.div className={className} variants={staggerItemVariants}>
      {children}
    </motion.div>
  )
}
