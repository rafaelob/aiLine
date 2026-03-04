import { create } from 'zustand'

export type DemoTrack = 'teacher' | 'accessibility'

export interface DemoStep {
  id: string
  track: DemoTrack
  title: string
  description: string
  route?: string
  demoKey?: string
  highlight?: string
}

/** Teacher Journey — 5-minute hackathon presentation flow. */
export const TEACHER_STEPS: DemoStep[] = [
  {
    id: 'teacher-1',
    track: 'teacher',
    title: 'demo.teacher.step1_title',
    description: 'demo.teacher.step1_desc',
    route: '/dashboard',
    demoKey: 'teacher-ms-johnson',
  },
  {
    id: 'teacher-2',
    track: 'teacher',
    title: 'demo.teacher.step2_title',
    description: 'demo.teacher.step2_desc',
    route: '/plan/new',
    highlight: 'plan-form',
  },
  {
    id: 'teacher-3',
    track: 'teacher',
    title: 'demo.teacher.step3_title',
    description: 'demo.teacher.step3_desc',
    highlight: 'pipeline-viz',
  },
  {
    id: 'teacher-4',
    track: 'teacher',
    title: 'demo.teacher.step4_title',
    description: 'demo.teacher.step4_desc',
    route: '/classroom',
    highlight: 'classroom-grid',
  },
  {
    id: 'teacher-5',
    track: 'teacher',
    title: 'demo.teacher.step5_title',
    description: 'demo.teacher.step5_desc',
    highlight: 'exports',
  },
]

/** Accessibility Showcase — demonstrates the 9 persona themes. */
export const A11Y_STEPS: DemoStep[] = [
  {
    id: 'a11y-1',
    track: 'accessibility',
    title: 'demo.a11y.step1_title',
    description: 'demo.a11y.step1_desc',
    demoKey: 'student-alex-tea',
    highlight: 'theme-preview',
  },
  {
    id: 'a11y-2',
    track: 'accessibility',
    title: 'demo.a11y.step2_title',
    description: 'demo.a11y.step2_desc',
    demoKey: 'student-maya-adhd',
  },
  {
    id: 'a11y-3',
    track: 'accessibility',
    title: 'demo.a11y.step3_title',
    description: 'demo.a11y.step3_desc',
    demoKey: 'student-lucas-dyslexia',
    highlight: 'bionic-reading',
  },
  {
    id: 'a11y-4',
    track: 'accessibility',
    title: 'demo.a11y.step4_title',
    description: 'demo.a11y.step4_desc',
    demoKey: 'student-sofia-hearing',
    highlight: 'sign-language',
  },
  {
    id: 'a11y-5',
    track: 'accessibility',
    title: 'demo.a11y.step5_title',
    description: 'demo.a11y.step5_desc',
    highlight: 'theme-compare',
  },
]

interface DemoState {
  isDemoMode: boolean
  activeTrack: DemoTrack | null
  currentStep: number
  dismissed: boolean
  isApiOffline: boolean
  _hydrated: boolean
  startDemo: (track: DemoTrack) => void
  nextStep: () => void
  prevStep: () => void
  goToStep: (step: number) => void
  exitDemo: () => void
  dismiss: () => void
  setApiOffline: (offline: boolean) => void
  hydrate: () => void
  /** Get the steps for the current track. */
  getSteps: () => DemoStep[]
  /** Get the current step info, or null. */
  getCurrentStep: () => DemoStep | null
}

function stepsForTrack(track: DemoTrack | null): DemoStep[] {
  if (track === 'teacher') return TEACHER_STEPS
  if (track === 'accessibility') return A11Y_STEPS
  return []
}

export const useDemoStore = create<DemoState>((set, get) => ({
  isDemoMode: false,
  activeTrack: null,
  currentStep: 0,
  dismissed: false,
  isApiOffline: false,
  _hydrated: false,
  startDemo: (track) => set({ isDemoMode: true, activeTrack: track, currentStep: 0 }),
  nextStep: () =>
    set((s) => {
      const steps = stepsForTrack(s.activeTrack)
      const next = Math.min(s.currentStep + 1, steps.length - 1)
      if (s.currentStep >= steps.length - 1) {
        return { isDemoMode: false, activeTrack: null, currentStep: 0 }
      }
      return { currentStep: next }
    }),
  prevStep: () =>
    set((s) => ({ currentStep: Math.max(s.currentStep - 1, 0) })),
  goToStep: (step) => set({ currentStep: step }),
  exitDemo: () => set({ isDemoMode: false, activeTrack: null, currentStep: 0 }),
  dismiss: () => {
    if (typeof window !== 'undefined')
      localStorage.setItem('ailine-demo-dismissed', 'true')
    set({ dismissed: true, isDemoMode: false, activeTrack: null, currentStep: 0 })
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
  getSteps: () => stepsForTrack(get().activeTrack),
  getCurrentStep: () => {
    const steps = stepsForTrack(get().activeTrack)
    return steps[get().currentStep] ?? null
  },
}))

// Hydrate from localStorage after module loads (deferred to avoid SSR issues)
if (typeof window !== 'undefined') {
  // Use queueMicrotask to defer past module evaluation
  queueMicrotask(() => useDemoStore.getState().hydrate())
}
