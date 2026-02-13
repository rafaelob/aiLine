import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToastStore } from './toast-store'

describe('toast-store', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    useToastStore.getState().clearAll()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts with empty toasts', () => {
    expect(useToastStore.getState().toasts).toEqual([])
  })

  it('adds a toast with default variant (info)', () => {
    useToastStore.getState().addToast('Hello')
    const toasts = useToastStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].message).toBe('Hello')
    expect(toasts[0].variant).toBe('info')
  })

  it('adds a toast with specified variant', () => {
    useToastStore.getState().addToast('Error!', 'error')
    const toasts = useToastStore.getState().toasts
    expect(toasts[0].variant).toBe('error')
  })

  it('returns a unique id for each toast', () => {
    const id1 = useToastStore.getState().addToast('One')
    const id2 = useToastStore.getState().addToast('Two')
    expect(id1).not.toBe(id2)
  })

  it('removes a toast by id', () => {
    const id = useToastStore.getState().addToast('Remove me', 'error')
    expect(useToastStore.getState().toasts).toHaveLength(1)
    useToastStore.getState().removeToast(id)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('clears all toasts', () => {
    useToastStore.getState().addToast('One', 'error')
    useToastStore.getState().addToast('Two', 'error')
    expect(useToastStore.getState().toasts).toHaveLength(2)
    useToastStore.getState().clearAll()
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('auto-dismisses success toasts after 5000ms', () => {
    useToastStore.getState().addToast('Yay', 'success')
    expect(useToastStore.getState().toasts).toHaveLength(1)

    vi.advanceTimersByTime(4999)
    expect(useToastStore.getState().toasts).toHaveLength(1)

    vi.advanceTimersByTime(1)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })

  it('does not auto-dismiss error toasts', () => {
    useToastStore.getState().addToast('Fail', 'error')
    vi.advanceTimersByTime(60000)
    expect(useToastStore.getState().toasts).toHaveLength(1)
  })

  it('allows custom duration override', () => {
    useToastStore.getState().addToast('Custom', 'info', 2000)
    vi.advanceTimersByTime(2000)
    expect(useToastStore.getState().toasts).toHaveLength(0)
  })
})
