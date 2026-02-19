import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BraillePreview } from './braille-preview'

describe('BraillePreview', () => {
  const user = userEvent.setup()

  const shortBrf = 'hello world\ntest line'
  const longBrf = Array.from({ length: 30 }, (_, i) => `line ${i + 1}`).join('\n')

  it('renders with proper ARIA region', () => {
    render(<BraillePreview brf={shortBrf} />)
    const region = screen.getByRole('region')
    expect(region).toHaveAttribute('aria-label', 'braille.preview_label')
  })

  it('displays character, line, and page stats', () => {
    render(<BraillePreview brf={shortBrf} />)
    expect(screen.getByText('braille.stat_chars')).toBeInTheDocument()
    expect(screen.getByText('braille.stat_lines')).toBeInTheDocument()
    expect(screen.getByText('braille.stat_pages')).toBeInTheDocument()
  })

  it('renders BRF content in a document role element', () => {
    render(<BraillePreview brf={shortBrf} />)
    const doc = screen.getByRole('document')
    expect(doc).toBeInTheDocument()
    expect(doc).toHaveAttribute('tabindex', '0')
  })

  it('shows the BRF text in pre element', () => {
    render(<BraillePreview brf={shortBrf} />)
    const pre = document.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre?.textContent).toContain('hello world')
    expect(pre?.textContent).toContain('test line')
  })

  it('does not show page navigation for single-page content', () => {
    render(<BraillePreview brf={shortBrf} />)
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })

  it('shows page navigation for multi-page content', () => {
    render(<BraillePreview brf={longBrf} />)
    const nav = screen.getByRole('navigation')
    expect(nav).toHaveAttribute('aria-label', 'braille.page_nav_label')
  })

  it('navigates between pages', async () => {
    render(<BraillePreview brf={longBrf} />)

    const nextBtn = screen.getByLabelText('braille.next_page')
    const prevBtn = screen.getByLabelText('braille.prev_page')

    // Initially on page 1, prev should be disabled
    expect(prevBtn).toBeDisabled()
    expect(nextBtn).not.toBeDisabled()

    // Go to next page
    await user.click(nextBtn)

    // Now prev should be enabled
    expect(prevBtn).not.toBeDisabled()
  })

  it('has live region for page indicator', () => {
    render(<BraillePreview brf={longBrf} />)
    const indicator = screen.getByText(/braille\.page_indicator/)
    expect(indicator).toHaveAttribute('aria-live', 'polite')
    expect(indicator).toHaveAttribute('aria-atomic', 'true')
  })

  it('applies custom className', () => {
    const { container } = render(<BraillePreview brf={shortBrf} className="test-class" />)
    expect(container.firstElementChild).toHaveClass('test-class')
  })

  it('shows cells per line stat', () => {
    render(<BraillePreview brf={shortBrf} />)
    expect(screen.getByText(/braille\.stat_cells_per_line/)).toBeInTheDocument()
  })

  it('focus-visible styling on content area', () => {
    render(<BraillePreview brf={shortBrf} />)
    const doc = screen.getByRole('document')
    expect(doc.className).toContain('focus-visible:outline-2')
  })

  describe('download and copy', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('renders download button with aria-label', () => {
      render(<BraillePreview brf={shortBrf} />)
      const downloadBtn = screen.getByLabelText('braille.download_label')
      expect(downloadBtn).toBeInTheDocument()
      expect(downloadBtn).toHaveTextContent('braille.download')
    })

    it('renders copy button with aria-label', () => {
      render(<BraillePreview brf={shortBrf} />)
      const copyBtn = screen.getByLabelText('braille.copy_label')
      expect(copyBtn).toBeInTheDocument()
      expect(copyBtn).toHaveTextContent('braille.copy')
    })

    it('triggers download on button click', async () => {
      render(<BraillePreview brf={shortBrf} filename="my-plan" />)
      const downloadBtn = screen.getByLabelText('braille.download_label')
      expect(downloadBtn).toBeInTheDocument()
      // Just verify the button is clickable without error
      await user.click(downloadBtn)
    })

    it('copies BRF content to clipboard', async () => {
      const writeText = vi.fn(() => Promise.resolve())
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText },
        writable: true,
        configurable: true,
      })

      render(<BraillePreview brf={shortBrf} />)
      const copyBtn = screen.getByLabelText('braille.copy_label')

      await user.click(copyBtn)

      expect(writeText).toHaveBeenCalledWith(shortBrf)
      await waitFor(() => {
        expect(copyBtn).toHaveTextContent('braille.copied')
      })
    })

    it('shows error state on clipboard failure', async () => {
      const writeText = vi.fn(() => Promise.reject(new Error('denied')))
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText },
        writable: true,
        configurable: true,
      })

      render(<BraillePreview brf={shortBrf} />)
      const copyBtn = screen.getByLabelText('braille.copy_label')

      await user.click(copyBtn)

      await waitFor(() => {
        expect(copyBtn).toHaveTextContent('braille.copy_error')
      })
    })
  })
})
