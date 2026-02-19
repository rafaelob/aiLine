import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExportViewer } from './export-viewer'

vi.mock('motion/react', () => ({
  motion: {
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const {
        initial: _i,
        animate: _a,
        transition: _t,
        layoutId: _li,
        variants: _v,
        style: _s,
        ...safe
      } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
  },
  useReducedMotion: () => false,
}))

vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

const mockExports: Record<string, string> = {
  standard: '<p>Standard content</p>',
  low_distraction: '<p>Low distraction content</p>',
  large_print: '<p>Large print content</p>',
}

describe('ExportViewer', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the variant selector', () => {
    render(<ExportViewer exports={mockExports} />)
    const select = screen.getByLabelText(/export_viewer\.variant_aria/i)
    expect(select).toBeInTheDocument()
  })

  it('renders two export panels side by side', () => {
    render(<ExportViewer exports={mockExports} />)
    const region = screen.getByRole('region', { name: /export_viewer\.comparison_label/i })
    expect(region).toBeInTheDocument()

    expect(screen.getByText('export_viewer.standard_panel')).toBeInTheDocument()
  })

  it('renders standard content in the standard panel', () => {
    render(<ExportViewer exports={mockExports} />)
    const standardPanel = document.querySelector('#standard-panel')
    expect(standardPanel).toBeInTheDocument()
    expect(standardPanel?.textContent).toContain('Standard content')
  })

  it('changes variant when selector changes', async () => {
    render(<ExportViewer exports={mockExports} />)
    const select = screen.getByLabelText(/export_viewer\.variant_aria/i)
    await user.selectOptions(select, 'large_print')

    const variantPanel = document.querySelector('#variant-panel')
    expect(variantPanel?.textContent).toContain('Large print content')
  })

  it('renders full screen toggle button when callback provided', () => {
    const onToggle = vi.fn()
    render(
      <ExportViewer
        exports={mockExports}
        onFullScreenToggle={onToggle}
      />
    )
    const button = screen.getByLabelText(/export_viewer\.fullscreen_enter_label/i)
    expect(button).toBeInTheDocument()
  })

  it('calls onFullScreenToggle when button is clicked', async () => {
    const onToggle = vi.fn()
    render(
      <ExportViewer
        exports={mockExports}
        onFullScreenToggle={onToggle}
      />
    )
    const button = screen.getByLabelText(/export_viewer\.fullscreen_enter_label/i)
    await user.click(button)
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('does not render full screen button without callback', () => {
    render(<ExportViewer exports={mockExports} />)
    expect(screen.queryByLabelText(/export_viewer\.fullscreen_enter_label/i)).not.toBeInTheDocument()
  })

  it('shows empty content message when variant has no content', () => {
    render(<ExportViewer exports={{ standard: '<p>Test</p>' }} />)
    expect(screen.getByText(/export_viewer\.no_content/i)).toBeInTheDocument()
  })
})
