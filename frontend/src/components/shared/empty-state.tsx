'use client'

import { motion } from 'motion/react'
import { cn } from '@/lib/cn'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

/**
 * Reusable empty state for list views.
 * Shows a friendly message when no data is available.
 */
export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className
      )}
    >
      {icon && (
        <div className="mb-4 text-[var(--color-muted)]" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-[var(--color-text)] mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-[var(--color-muted)] max-w-sm mb-4">
          {description}
        </p>
      )}
      {action && <div>{action}</div>}
    </motion.div>
  )
}
