import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ToastProvider } from './toast-provider'
import { useToastStore } from '@/stores/toast-store'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, layout: _l, initial: _i, animate: _a, exit: _e, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('ToastProvider', () => {
  beforeEach(() => {
    useToastStore.getState().clearAll()
  })

  it('renders nothing when no toasts', () => {
    const { container } = render(<ToastProvider />)
    expect(container.innerHTML).toBe('')
  })

  it('renders toasts when present', () => {
    useToastStore.getState().addToast('Test message', 'error')
    render(<ToastProvider />)
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('renders the container with notifications aria-label and region role', () => {
    useToastStore.getState().addToast('Hello', 'error')
    render(<ToastProvider />)
    const region = screen.getByRole('region', { name: 'common.notifications' })
    expect(region).toBeInTheDocument()
  })

  it('renders multiple toasts', () => {
    useToastStore.getState().addToast('First', 'error')
    useToastStore.getState().addToast('Second', 'error')
    render(<ToastProvider />)
    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
  })
})
