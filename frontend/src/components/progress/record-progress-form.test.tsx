import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RecordProgressForm } from './record-progress-form'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('RecordProgressForm', () => {
  const user = userEvent.setup()
  const onSuccess = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form with heading', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)
    expect(screen.getByRole('heading', { name: 'progress.record_progress' })).toBeInTheDocument()
  })

  it('renders all input fields', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)

    expect(screen.getByPlaceholderText('Student ID')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Student Name')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Standard Code (e.g. EF06MA01)')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Standard Description')).toBeInTheDocument()
  })

  it('renders Student ID as required', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)

    const studentIdInput = screen.getByPlaceholderText('Student ID')
    expect(studentIdInput).toBeRequired()
  })

  it('renders Standard Code as required', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)

    const standardCodeInput = screen.getByPlaceholderText('Standard Code (e.g. EF06MA01)')
    expect(standardCodeInput).toBeRequired()
  })

  it('renders mastery level select with four options', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)

    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()

    // Check all four mastery options exist
    expect(screen.getByText('progress.mastery_levels.not_started')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.developing')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.proficient')).toBeInTheDocument()
    expect(screen.getByText('progress.mastery_levels.mastered')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<RecordProgressForm onSuccess={onSuccess} />)

    // The button text uses t('record_progress') which auto-mocks to "progress.record_progress"
    // The heading also uses the same key, so use getAllByText and check for the button role
    const submitButton = screen.getByRole('button', { name: 'progress.record_progress' })
    expect(submitButton).toBeInTheDocument()
    expect(submitButton).toHaveAttribute('type', 'submit')
  })

  it('calls onSuccess after successful submit', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'progress-1' }),
    })

    render(<RecordProgressForm onSuccess={onSuccess} />)

    // Fill required fields
    await user.type(screen.getByPlaceholderText('Student ID'), 'student-001')
    await user.type(screen.getByPlaceholderText('Standard Code (e.g. EF06MA01)'), 'EF06MA01')

    // Submit the form
    await user.click(screen.getByRole('button', { name: 'progress.record_progress' }))

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1)
    })

    // Verify fetch was called with correct endpoint and method
    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, options] = mockFetch.mock.calls[0]
    expect(url).toContain('/progress/record')
    expect(options.method).toBe('POST')

    // Verify the body
    const body = JSON.parse(options.body)
    expect(body.student_id).toBe('student-001')
    expect(body.standard_code).toBe('EF06MA01')
    expect(body.mastery_level).toBe('developing') // default value
  })

  it('does not call onSuccess when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })

    render(<RecordProgressForm onSuccess={onSuccess} />)

    await user.type(screen.getByPlaceholderText('Student ID'), 'student-001')
    await user.type(screen.getByPlaceholderText('Standard Code (e.g. EF06MA01)'), 'EF06MA01')

    await user.click(screen.getByRole('button', { name: 'progress.record_progress' }))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    expect(onSuccess).not.toHaveBeenCalled()
  })

  it('sends all filled fields in the POST body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'progress-1' }),
    })

    render(<RecordProgressForm onSuccess={onSuccess} />)

    await user.type(screen.getByPlaceholderText('Student ID'), 's1')
    await user.type(screen.getByPlaceholderText('Student Name'), 'Alice')
    await user.type(screen.getByPlaceholderText('Standard Code (e.g. EF06MA01)'), 'EF06MA01')
    await user.type(screen.getByPlaceholderText('Standard Description'), 'Fractions')
    await user.selectOptions(screen.getByRole('combobox'), 'proficient')

    await user.click(screen.getByRole('button', { name: 'progress.record_progress' }))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body).toEqual({
      student_id: 's1',
      student_name: 'Alice',
      standard_code: 'EF06MA01',
      standard_description: 'Fractions',
      mastery_level: 'proficient',
    })
  })

  it('applies custom className', () => {
    const { container } = render(
      <RecordProgressForm onSuccess={onSuccess} className="custom-class" />,
    )
    const form = container.querySelector('form')
    expect(form?.className).toContain('custom-class')
  })
})
