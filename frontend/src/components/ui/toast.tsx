'use client'

import { motion } from 'motion/react'
import { cn } from '@/lib/cn'
import { useToastStore, type Toast as ToastType, type ToastVariant } from '@/stores/toast-store'

const VARIANT_STYLES: Record<ToastVariant, string> = {
  success: 'border-l-4 border-l-[var(--color-success)]',
  error: 'border-l-4 border-l-[var(--color-error)]',
  warning: 'border-l-4 border-l-[var(--color-warning)]',
  info: 'border-l-4 border-l-[var(--color-primary)]',
}

const VARIANT_ICONS: Record<ToastVariant, string> = {
  success: '\u2713',
  error: '\u2715',
  warning: '!',
  info: 'i',
}

interface ToastProps {
  toast: ToastType
}

export function Toast({ toast }: ToastProps) {
  const removeToast = useToastStore((s) => s.removeToast)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 40, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 40, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      role="status"
      aria-live="polite"
      className={cn(
        'pointer-events-auto flex items-start gap-3 rounded-[var(--radius-md)] px-4 py-3',
        'bg-[var(--color-surface)] border border-[var(--color-border)]',
        'shadow-[var(--shadow-lg)]',
        VARIANT_STYLES[toast.variant],
      )}
    >
      <span
        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface-elevated)] text-xs font-bold"
        aria-hidden="true"
      >
        {VARIANT_ICONS[toast.variant]}
      </span>
      <p className="flex-1 text-sm text-[var(--color-text)]">{toast.message}</p>
      <button
        type="button"
        onClick={() => removeToast(toast.id)}
        className="shrink-0 text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors"
        aria-label="Fechar notificação"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </motion.div>
  )
}
