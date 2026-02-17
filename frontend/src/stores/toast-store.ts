import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
  /** Auto-dismiss duration in ms. 0 = persistent. Default: 5000 for success, 0 for error. */
  duration: number
  /** Optional undo callback. When present, the toast shows an "Undo" button. */
  onUndo?: () => void
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, variant?: ToastVariant, duration?: number, onUndo?: () => void) => string
  removeToast: (id: string) => void
  clearAll: () => void
}

let nextId = 0

/** Map of toast ID to its auto-dismiss timer, so we can cancel on manual removal. */
const timerMap = new Map<string, ReturnType<typeof setTimeout>>()

const DEFAULT_DURATIONS: Record<ToastVariant, number> = {
  success: 5000,
  info: 5000,
  warning: 7000,
  error: 0,
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (message, variant = 'info', duration?, onUndo?) => {
    const id = `toast-${++nextId}`
    const finalDuration = duration ?? DEFAULT_DURATIONS[variant]

    set((state) => ({
      toasts: [...state.toasts, { id, message, variant, duration: finalDuration, onUndo }],
    }))

    if (finalDuration > 0) {
      const timer = setTimeout(() => {
        timerMap.delete(id)
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      }, finalDuration)
      timerMap.set(id, timer)
    }

    return id
  },

  removeToast: (id) => {
    const timer = timerMap.get(id)
    if (timer) {
      clearTimeout(timer)
      timerMap.delete(id)
    }
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },

  clearAll: () => {
    // Cancel all pending auto-dismiss timers
    for (const timer of timerMap.values()) {
      clearTimeout(timer)
    }
    timerMap.clear()
    set({ toasts: [] })
  },
}))
