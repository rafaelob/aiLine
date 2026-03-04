import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useDemoStore, TEACHER_STEPS, A11Y_STEPS } from './demo-store'

describe('useDemoStore', () => {
  beforeEach(() => {
    useDemoStore.setState({
      isDemoMode: false,
      activeTrack: null,
      currentStep: 0,
      dismissed: false,
    })
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
    })
  })

  it('startDemo sets isDemoMode=true with teacher track', () => {
    useDemoStore.getState().startDemo('teacher')
    const state = useDemoStore.getState()
    expect(state.isDemoMode).toBe(true)
    expect(state.activeTrack).toBe('teacher')
    expect(state.currentStep).toBe(0)
  })

  it('startDemo with accessibility track', () => {
    useDemoStore.getState().startDemo('accessibility')
    const state = useDemoStore.getState()
    expect(state.isDemoMode).toBe(true)
    expect(state.activeTrack).toBe('accessibility')
  })

  it('nextStep increments currentStep', () => {
    useDemoStore.getState().startDemo('teacher')
    useDemoStore.getState().nextStep()
    expect(useDemoStore.getState().currentStep).toBe(1)
  })

  it('nextStep exits demo at last step', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'teacher',
      currentStep: TEACHER_STEPS.length - 1,
    })
    useDemoStore.getState().nextStep()
    expect(useDemoStore.getState().isDemoMode).toBe(false)
  })

  it('prevStep decrements currentStep', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'teacher',
      currentStep: 2,
    })
    useDemoStore.getState().prevStep()
    expect(useDemoStore.getState().currentStep).toBe(1)
  })

  it('prevStep clamps at 0', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'teacher',
      currentStep: 0,
    })
    useDemoStore.getState().prevStep()
    expect(useDemoStore.getState().currentStep).toBe(0)
  })

  it('goToStep navigates directly', () => {
    useDemoStore.setState({
      isDemoMode: true,
      activeTrack: 'accessibility',
      currentStep: 0,
    })
    useDemoStore.getState().goToStep(3)
    expect(useDemoStore.getState().currentStep).toBe(3)
  })

  it('exitDemo resets state', () => {
    useDemoStore.getState().startDemo('teacher')
    useDemoStore.getState().exitDemo()
    const state = useDemoStore.getState()
    expect(state.isDemoMode).toBe(false)
    expect(state.activeTrack).toBeNull()
    expect(state.currentStep).toBe(0)
  })

  it('dismiss sets localStorage and dismissed flag', () => {
    useDemoStore.getState().dismiss()
    const state = useDemoStore.getState()
    expect(state.dismissed).toBe(true)
    expect(state.isDemoMode).toBe(false)
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'ailine-demo-dismissed',
      'true',
    )
  })

  it('getSteps returns teacher steps for teacher track', () => {
    useDemoStore.setState({ activeTrack: 'teacher' })
    expect(useDemoStore.getState().getSteps()).toBe(TEACHER_STEPS)
  })

  it('getSteps returns a11y steps for accessibility track', () => {
    useDemoStore.setState({ activeTrack: 'accessibility' })
    expect(useDemoStore.getState().getSteps()).toBe(A11Y_STEPS)
  })

  it('getCurrentStep returns current step object', () => {
    useDemoStore.setState({ activeTrack: 'teacher', currentStep: 1 })
    const step = useDemoStore.getState().getCurrentStep()
    expect(step).toBe(TEACHER_STEPS[1])
  })

  it('getCurrentStep returns null when no track', () => {
    expect(useDemoStore.getState().getCurrentStep()).toBeNull()
  })

  it('TEACHER_STEPS has 5 steps', () => {
    expect(TEACHER_STEPS).toHaveLength(5)
    expect(TEACHER_STEPS.every((s) => s.track === 'teacher')).toBe(true)
  })

  it('A11Y_STEPS has 5 steps', () => {
    expect(A11Y_STEPS).toHaveLength(5)
    expect(A11Y_STEPS.every((s) => s.track === 'accessibility')).toBe(true)
  })
})
