import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
  /** Auto-dismiss duration in ms. 0 = persistent. Default: 5000 for success, 0 for error. */
  duration: number
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, variant?: ToastVariant, duration?: number) => string
  removeToast: (id: string) => void
  clearAll: () => void
}

let nextId = 0

const DEFAULT_DURATIONS: Record<ToastVariant, number> = {
  success: 5000,
  info: 5000,
  warning: 7000,
  error: 0,
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (message, variant = 'info', duration?) => {
    const id = `toast-${++nextId}`
    const finalDuration = duration ?? DEFAULT_DURATIONS[variant]

    set((state) => ({
      toasts: [...state.toasts, { id, message, variant, duration: finalDuration }],
    }))

    if (finalDuration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      }, finalDuration)
    }

    return id
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },

  clearAll: () => {
    set({ toasts: [] })
  },
}))
