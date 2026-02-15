import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useDemoStore } from './demo-store'

describe('useDemoStore', () => {
  beforeEach(() => {
    useDemoStore.setState({
      isDemoMode: false,
      currentStep: 0,
      dismissed: false,
    })
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
    })
  })

  it('startDemo sets isDemoMode=true and currentStep=1', () => {
    useDemoStore.getState().startDemo()
    const state = useDemoStore.getState()
    expect(state.isDemoMode).toBe(true)
    expect(state.currentStep).toBe(1)
  })

  it('nextStep increments currentStep', () => {
    useDemoStore.getState().startDemo()
    useDemoStore.getState().nextStep()
    expect(useDemoStore.getState().currentStep).toBe(2)
  })

  it('nextStep clamps at 3', () => {
    useDemoStore.setState({ isDemoMode: true, currentStep: 3 })
    useDemoStore.getState().nextStep()
    expect(useDemoStore.getState().currentStep).toBe(3)
  })

  it('exitDemo resets state', () => {
    useDemoStore.getState().startDemo()
    useDemoStore.getState().exitDemo()
    const state = useDemoStore.getState()
    expect(state.isDemoMode).toBe(false)
    expect(state.currentStep).toBe(0)
  })

  it('dismiss sets localStorage and dismissed flag', () => {
    useDemoStore.getState().dismiss()
    const state = useDemoStore.getState()
    expect(state.dismissed).toBe(true)
    expect(state.isDemoMode).toBe(false)
    expect(state.currentStep).toBe(0)
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'ailine-demo-dismissed',
      'true',
    )
  })
})
