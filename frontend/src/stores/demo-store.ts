import { create } from 'zustand'

interface DemoState {
  isDemoMode: boolean
  currentStep: number
  dismissed: boolean
  isApiOffline: boolean
  _hydrated: boolean
  startDemo: () => void
  nextStep: () => void
  exitDemo: () => void
  dismiss: () => void
  setApiOffline: (offline: boolean) => void
  hydrate: () => void
}

export const useDemoStore = create<DemoState>((set) => ({
  isDemoMode: false,
  currentStep: 0,
  dismissed: false,
  isApiOffline: false,
  _hydrated: false,
  startDemo: () => set({ isDemoMode: true, currentStep: 1 }),
  nextStep: () =>
    set((s) => ({ currentStep: Math.min(s.currentStep + 1, 3) })),
  exitDemo: () => set({ isDemoMode: false, currentStep: 0 }),
  dismiss: () => {
    if (typeof window !== 'undefined')
      localStorage.setItem('ailine-demo-dismissed', 'true')
    set({ dismissed: true, isDemoMode: false, currentStep: 0 })
  },
  setApiOffline: (offline) => set({ isApiOffline: offline }),
  hydrate: () =>
    set((s) => {
      if (s._hydrated) return s
      const wasDismissed =
        typeof window !== 'undefined'
          ? localStorage.getItem('ailine-demo-dismissed') === 'true'
          : false
      return { _hydrated: true, dismissed: wasDismissed }
    }),
}))

// Hydrate from localStorage after module loads (deferred to avoid SSR issues)
if (typeof window !== 'undefined') {
  // Use queueMicrotask to defer past module evaluation
  queueMicrotask(() => useDemoStore.getState().hydrate())
}
