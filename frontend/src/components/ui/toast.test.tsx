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

  it('has role="status" for non-error variants', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Info', variant: 'info', duration: 5000 }} />
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has role="alert" for error variant', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Fail', variant: 'error', duration: 0 }} />
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders close button with aria-label', () => {
    render(
      <Toast toast={{ id: 'test-1', message: 'Hello', variant: 'info', duration: 5000 }} />
    )
    expect(screen.getByLabelText('toast.close')).toBeInTheDocument()
  })

  it('calls removeToast when close button is clicked', async () => {
    const id = useToastStore.getState().addToast('Removable', 'error')
    render(
      <Toast toast={useToastStore.getState().toasts[0]} />
    )

    await user.click(screen.getByLabelText('toast.close'))
    expect(useToastStore.getState().toasts.find((t) => t.id === id)).toBeUndefined()
  })

  it('renders undo button when onUndo is provided', () => {
    const onUndo = vi.fn()
    render(
      <Toast toast={{ id: 'test-undo', message: 'Action done', variant: 'success', duration: 5000, onUndo }} />
    )
    expect(screen.getByText('toast.undo')).toBeInTheDocument()
  })

  it('does not render undo button when onUndo is not provided', () => {
    render(
      <Toast toast={{ id: 'test-no-undo', message: 'Normal toast', variant: 'info', duration: 5000 }} />
    )
    expect(screen.queryByText('toast.undo')).not.toBeInTheDocument()
  })

  it('calls onUndo and removes toast when undo is clicked', async () => {
    const onUndo = vi.fn()
    const id = useToastStore.getState().addToast('Undoable', 'success', 5000, onUndo)
    const toast = useToastStore.getState().toasts.find((t) => t.id === id)!
    render(<Toast toast={toast} />)

    await user.click(screen.getByText('toast.undo'))
    expect(onUndo).toHaveBeenCalledTimes(1)
    expect(useToastStore.getState().toasts.find((t) => t.id === id)).toBeUndefined()
  })
})
