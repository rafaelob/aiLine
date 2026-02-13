'use client'

import { motion, type HTMLMotionProps } from 'motion/react'
import { cn } from '@/lib/cn'

interface InteractiveCardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
}

/**
 * Reusable interactive card with hover lift and tap feedback.
 * Uses theme-aware colors and border-radius tokens.
 */
export function InteractiveCard({ className, children, ...props }: InteractiveCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      tabIndex={0}
      className={cn(
        'rounded-[var(--radius-lg)] border',
        'bg-[var(--color-surface)] border-[var(--color-border)]',
        'cursor-pointer transition-shadow',
        'hover:shadow-[var(--shadow-md)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:ring-offset-2',
        className,
      )}
      {...props}
    >
      {children}
    </motion.div>
  )
}
