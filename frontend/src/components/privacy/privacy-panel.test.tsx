import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PrivacyPanel } from './privacy-panel'

const mockSummary = {
  plans: 12,
  sessions: 34,
  materials: 5,
  last_updated: '2026-02-13T10:00:00Z',
}

describe('PrivacyPanel', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockSummary),
      })
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders title and description', () => {
    render(<PrivacyPanel />)
    expect(screen.getByText('privacy.title')).toBeInTheDocument()
    expect(screen.getByText('privacy.description')).toBeInTheDocument()
  })

  it('shows loading skeletons initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    const { container } = render(<PrivacyPanel />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(1)
  })

  it('renders data summary after fetch', async () => {
    render(<PrivacyPanel />)
    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('34')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  it('renders retention policies', () => {
    render(<PrivacyPanel />)
    expect(screen.getByText('privacy.retention_plans')).toBeInTheDocument()
    expect(screen.getByText('privacy.retention_sessions')).toBeInTheDocument()
    expect(screen.getByText('privacy.retention_materials')).toBeInTheDocument()
    expect(screen.getByText('privacy.retention_logs')).toBeInTheDocument()
  })

  it('renders export button', () => {
    render(<PrivacyPanel />)
    const exportBtns = screen.getAllByText('privacy.export_data')
    expect(exportBtns.length).toBeGreaterThanOrEqual(1)
  })

  it('renders delete button', () => {
    render(<PrivacyPanel />)
    const deleteBtns = screen.getAllByText('privacy.delete_data')
    expect(deleteBtns.length).toBeGreaterThanOrEqual(1)
  })

  it('shows confirmation on first delete click', async () => {
    render(<PrivacyPanel />)
    const deleteBtn = screen.getAllByText('privacy.delete_data').find(
      (el) => el.tagName === 'BUTTON'
    )!
    await user.click(deleteBtn)

    expect(screen.getByText('privacy.delete_confirm')).toBeInTheDocument()
  })

  it('calls export API on export click', async () => {
    render(<PrivacyPanel />)
    const exportBtn = screen.getAllByText('privacy.export_data').find(
      (el) => el.tagName === 'BUTTON'
    )!
    await user.click(exportBtn)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/privacy/export'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('has proper section headings', () => {
    render(<PrivacyPanel />)
    expect(screen.getByText('privacy.data_summary')).toBeInTheDocument()
    expect(screen.getByText('privacy.retention')).toBeInTheDocument()
    expect(screen.getByText('privacy.actions')).toBeInTheDocument()
  })
})
