'use client'

import { AnimatePresence } from 'motion/react'
import { useToastStore } from '@/stores/toast-store'
import { Toast } from './toast'

/**
 * Toast container rendered as a fixed stack.
 * Position: bottom-right, above mobile nav (bottom-20 on mobile).
 * Mount once in the root layout.
 */
export function ToastProvider() {
  const toasts = useToastStore((s) => s.toasts)

  if (toasts.length === 0) return null

  return (
    <div
      aria-label="Notificações"
      className="fixed bottom-20 right-4 z-[60] flex flex-col gap-2 pointer-events-none sm:bottom-6 sm:right-6 sm:max-w-sm"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  )
}
