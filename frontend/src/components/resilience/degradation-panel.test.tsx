import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DegradationPanel } from './degradation-panel'

describe('DegradationPanel', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders title and description', () => {
    render(<DegradationPanel />)
    expect(screen.getByText('degradation.title')).toBeInTheDocument()
    expect(screen.getByText('degradation.description')).toBeInTheDocument()
  })

  it('shows healthy status by default', () => {
    render(<DegradationPanel />)
    expect(screen.getByText('degradation.status_healthy')).toBeInTheDocument()
  })

  it('shows degraded status after toggling Redis failure', async () => {
    render(<DegradationPanel />)
    const redisBtn = screen.getByText('degradation.simulate_redis')
    await user.click(redisBtn)

    expect(screen.getByText('degradation.status_degraded')).toBeInTheDocument()
    expect(screen.getByText('degradation.redis_down')).toBeInTheDocument()
  })

  it('shows degraded status after toggling LLM failure', async () => {
    render(<DegradationPanel />)
    const llmBtn = screen.getByText('degradation.simulate_llm')
    await user.click(llmBtn)

    expect(screen.getByText('degradation.status_degraded')).toBeInTheDocument()
    expect(screen.getByText('degradation.llm_timeout')).toBeInTheDocument()
  })

  it('sets aria-pressed on active failure buttons', async () => {
    render(<DegradationPanel />)
    const redisBtn = screen.getByText('degradation.simulate_redis')
    expect(redisBtn).toHaveAttribute('aria-pressed', 'false')

    await user.click(redisBtn)
    expect(redisBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows reset button when degraded', async () => {
    render(<DegradationPanel />)
    expect(screen.queryByText('degradation.reset')).not.toBeInTheDocument()

    await user.click(screen.getByText('degradation.simulate_redis'))
    expect(screen.getByText('degradation.reset')).toBeInTheDocument()
  })

  it('resets all failures on reset click', async () => {
    render(<DegradationPanel />)
    await user.click(screen.getByText('degradation.simulate_redis'))
    await user.click(screen.getByText('degradation.simulate_llm'))
    expect(screen.getByText('degradation.status_degraded')).toBeInTheDocument()

    await user.click(screen.getByText('degradation.reset'))
    expect(screen.getByText('degradation.status_healthy')).toBeInTheDocument()
  })

  it('calls API when toggling failure', async () => {
    render(<DegradationPanel />)
    await user.click(screen.getByText('degradation.simulate_redis'))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/demo/chaos'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ failure: 'redis', active: true }),
        })
      )
    })
  })

  it('shows both failure descriptions when both active', async () => {
    render(<DegradationPanel />)
    await user.click(screen.getByText('degradation.simulate_redis'))
    await user.click(screen.getByText('degradation.simulate_llm'))

    expect(screen.getByText('degradation.redis_down')).toBeInTheDocument()
    expect(screen.getByText('degradation.llm_timeout')).toBeInTheDocument()
  })

  it('has proper status role with aria-live', () => {
    render(<DegradationPanel />)
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-live', 'polite')
  })
})
