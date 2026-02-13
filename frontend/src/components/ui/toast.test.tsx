import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Toast } from './toast'
import { useToastStore } from '@/stores/toast-store'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, layout: _l, initial: _i, animate: _a, exit: _e, transition: _t, ...rest }: Record<string, unknown>) => {
      return <div {...rest}>{children as React.ReactNode}</div>
    },
  },
}))

describe('Toast', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    useToastStore.getState().clearAll()
  })

  it('renders the toast message', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Saved!', variant: 'success', duration: 5000 }} />
    )
    expect(screen.getByText('Saved!')).toBeInTheDocument()
  })

  it('has role="status" for accessibility', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Info', variant: 'info', duration: 5000 }} />
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders close button with aria-label', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Hello', variant: 'info', duration: 5000 }} />
    )
    expect(screen.getByLabelText('Fechar notificação')).toBeInTheDocument()
  })

  it('calls removeToast when close button is clicked', async () => {
    const id = useToastStore.getState().addToast('Removable', 'error')
    render(
      <Toast toast={useToastStore.getState().toasts[0]} />
    )

    await user.click(screen.getByLabelText('Fechar notificação'))
    expect(useToastStore.getState().toasts.find((t) => t.id === id)).toBeUndefined()
  })
})
