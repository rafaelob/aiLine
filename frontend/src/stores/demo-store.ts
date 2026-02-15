import { create } from 'zustand'

interface DemoState {
  isDemoMode: boolean
  currentStep: number
  dismissed: boolean
  startDemo: () => void
  nextStep: () => void
  exitDemo: () => void
  dismiss: () => void
}

export const useDemoStore = create<DemoState>((set) => ({
  isDemoMode: false,
  currentStep: 0,
  dismissed:
    typeof window !== 'undefined'
      ? localStorage.getItem('ailine-demo-dismissed') === 'true'
      : false,
  startDemo: () => set({ isDemoMode: true, currentStep: 1 }),
  nextStep: () =>
    set((s) => ({ currentStep: Math.min(s.currentStep + 1, 3) })),
  exitDemo: () => set({ isDemoMode: false, currentStep: 0 }),
  dismiss: () => {
    if (typeof window !== 'undefined')
      localStorage.setItem('ailine-demo-dismissed', 'true')
    set({ dismissed: true, isDemoMode: false, currentStep: 0 })
  },
}))
