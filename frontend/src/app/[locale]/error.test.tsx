import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorPage from './error'

describe('ErrorPage', () => {
  const mockError = Object.assign(new Error('Test error'), { digest: 'abc123' })
  const mockReset = vi.fn()

  beforeEach(() => {
    mockReset.mockClear()
  })

  it('renders error title and description', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByText('common.error_title')).toBeInTheDocument()
    expect(screen.getByText('common.error_description')).toBeInTheDocument()
  })

  it('renders error digest when provided', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByText(/abc123/)).toBeInTheDocument()
  })

  it('hides digest when not provided', () => {
    const errorNoDig = new Error('No digest') as Error & { digest?: string }
    render(<ErrorPage error={errorNoDig} reset={mockReset} />)
    expect(screen.queryByText(/abc123/)).not.toBeInTheDocument()
  })

  it('calls reset when retry button is clicked', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    fireEvent.click(screen.getByText('common.retry'))
    expect(mockReset).toHaveBeenCalledTimes(1)
  })

  it('renders go home link pointing to root', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    const link = screen.getByText('common.go_home')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/')
  })

  it('renders the error icon', () => {
    const { container } = render(<ErrorPage error={mockError} reset={mockReset} />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('logs error to console', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(spy).toHaveBeenCalledWith('[ErrorBoundary]', mockError)
    spy.mockRestore()
  })

  it('renders the reload page button', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByText('common.reload')).toBeInTheDocument()
  })

  it('renders the copy diagnostics button', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByLabelText('common.copy_diagnostics')).toBeInTheDocument()
  })

  it('copies diagnostics to clipboard on click', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { writeText },
    })

    render(<ErrorPage error={mockError} reset={mockReset} />)
    const copyButton = screen.getByLabelText('common.copy_diagnostics')
    await user.click(copyButton)

    expect(writeText).toHaveBeenCalledTimes(1)
    const copiedText = writeText.mock.calls[0][0] as string
    expect(copiedText).toContain('abc123')
    expect(copiedText).toContain('Test error')

    vi.unstubAllGlobals()
  })

  it('shows confirmation after copying diagnostics', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    })

    render(<ErrorPage error={mockError} reset={mockReset} />)
    const copyButton = screen.getByLabelText('common.copy_diagnostics')
    await user.click(copyButton)

    expect(screen.getByText('common.diagnostics_copied')).toBeInTheDocument()

    vi.unstubAllGlobals()
  })

  it('shows SSE reconnect UI for streaming errors', () => {
    const sseError = Object.assign(new Error('SSE connection lost'), { digest: 'sse-001' })
    render(<ErrorPage error={sseError} reset={mockReset} />)

    expect(screen.getByText('common.sse_reconnect')).toBeInTheDocument()
  })

  it('does not show SSE reconnect UI for non-streaming errors', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.queryByText('common.sse_reconnect')).not.toBeInTheDocument()
  })

  it('has role="alert" on the container', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('focuses the retry button on mount for keyboard accessibility', () => {
    render(<ErrorPage error={mockError} reset={mockReset} />)
    const retryButton = screen.getByText('common.retry')
    expect(document.activeElement).toBe(retryButton)
  })
})
