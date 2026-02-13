import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { ServiceWorkerRegistrar } from './sw-registrar'

describe('ServiceWorkerRegistrar', () => {
  const mockRegister = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: mockRegister },
      writable: true,
      configurable: true,
    })
  })

  it('renders nothing visible', () => {
    const { container } = render(<ServiceWorkerRegistrar />)
    expect(container.innerHTML).toBe('')
  })

  it('registers the service worker on mount', () => {
    render(<ServiceWorkerRegistrar />)
    expect(mockRegister).toHaveBeenCalledWith('/sw.js')
  })

  it('registers service worker only once', () => {
    render(<ServiceWorkerRegistrar />)
    expect(mockRegister).toHaveBeenCalledTimes(1)
  })

  it('handles registration failure silently', () => {
    mockRegister.mockRejectedValueOnce(new Error('SW registration failed'))
    // Should not throw
    expect(() => render(<ServiceWorkerRegistrar />)).not.toThrow()
  })
})
