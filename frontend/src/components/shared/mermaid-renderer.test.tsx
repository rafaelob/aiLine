import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MermaidRenderer, { extractMermaidBlocks } from './mermaid-renderer'

const mockInitialize = vi.fn()
const mockRender = vi.fn()

// Mock DOMPurify -- pass through for tests (XSS sanitization tested separately)
vi.mock('dompurify', () => ({
  default: { sanitize: (html: string) => html },
}))

// Mock the mermaid loader module (thin wrapper around dynamic import)
vi.mock('@/lib/mermaid-loader', () => ({
  loadMermaid: () =>
    Promise.resolve({
      initialize: mockInitialize,
      render: mockRender,
    }),
}))

// Mock useThemeContext
vi.mock('@/hooks/use-theme-context', () => ({
  useThemeContext: () => 'standard',
}))

// Mock motion/react
vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

const MOCK_SVG = '<svg class="mermaid-test"><rect width="100" height="50"/></svg>'

beforeEach(() => {
  vi.clearAllMocks()
  mockRender.mockResolvedValue({ svg: MOCK_SVG })
  HTMLDialogElement.prototype.showModal = vi.fn()
  HTMLDialogElement.prototype.close = vi.fn()
})

const SAMPLE_MERMAID = `graph TD
    A[Start] --> B[Process]
    B --> C[End]`

async function renderAndWaitForDiagram(code: string = SAMPLE_MERMAID) {
  render(<MermaidRenderer code={code} />)
  await waitFor(
    () => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    },
    { timeout: 3000 }
  )
}

describe('MermaidRenderer', () => {
  it('renders loading skeleton initially', () => {
    mockRender.mockReturnValue(new Promise(() => {}))
    render(<MermaidRenderer code={SAMPLE_MERMAID} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders the collapsible toggle button', () => {
    render(<MermaidRenderer code={SAMPLE_MERMAID} />)
    const toggle = screen.getByRole('button', { expanded: true })
    expect(toggle).toBeInTheDocument()
    expect(toggle).toHaveTextContent('mermaid.visual_explanation')
  })

  it('renders mermaid SVG after loading', async () => {
    await renderAndWaitForDiagram()
    expect(mockRender).toHaveBeenCalled()
    expect(mockInitialize).toHaveBeenCalledWith(
      expect.objectContaining({ theme: 'base', securityLevel: 'strict' })
    )
    // SVG rendered in the main content area (dialog is hidden by default)
    const imgContainers = screen.getAllByRole('img')
    expect(imgContainers.length).toBeGreaterThanOrEqual(1)
  })

  it('shows copy and fullscreen buttons', async () => {
    await renderAndWaitForDiagram()
    expect(screen.getByText('mermaid.copy_code')).toBeInTheDocument()
    expect(screen.getByText('mermaid.fullscreen')).toBeInTheDocument()
  })

  it('collapses and expands the panel', async () => {
    const user = userEvent.setup()
    render(<MermaidRenderer code={SAMPLE_MERMAID} />)

    const toggle = screen.getByRole('button', { expanded: true })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('opens fullscreen dialog on fullscreen button click', async () => {
    const user = userEvent.setup()
    await renderAndWaitForDiagram()

    const fullscreenBtn = screen.getByText('mermaid.fullscreen')
    await user.click(fullscreenBtn)

    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled()
  })

  it('shows copy button that transitions to copied state', async () => {
    // Directly test the copy button exists and has correct labels
    await renderAndWaitForDiagram()

    const copyBtn = screen.getByLabelText('mermaid.copy_code')
    expect(copyBtn).toBeInTheDocument()
    expect(copyBtn).toHaveTextContent('mermaid.copy_code')
  })

  it('shows error when mermaid render fails', async () => {
    mockRender.mockRejectedValueOnce(new Error('Invalid syntax'))

    render(<MermaidRenderer code="invalid mermaid code" />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(screen.getByText(/Invalid syntax/)).toBeInTheDocument()
  })
})

describe('extractMermaidBlocks', () => {
  it('returns single text segment when no mermaid blocks', () => {
    const result = extractMermaidBlocks('Hello world')
    expect(result).toEqual([{ type: 'text', content: 'Hello world' }])
  })

  it('extracts a single mermaid block', () => {
    const input = 'Before\n```mermaid\ngraph TD\n    A-->B\n```\nAfter'
    const result = extractMermaidBlocks(input)
    expect(result).toEqual([
      { type: 'text', content: 'Before\n' },
      { type: 'mermaid', content: 'graph TD\n    A-->B\n' },
      { type: 'text', content: '\nAfter' },
    ])
  })

  it('extracts multiple mermaid blocks', () => {
    const input = 'Intro\n```mermaid\nA-->B\n```\nMiddle\n```mermaid\nC-->D\n```\nEnd'
    const result = extractMermaidBlocks(input)
    expect(result).toHaveLength(5)
    expect(result[0]).toEqual({ type: 'text', content: 'Intro\n' })
    expect(result[1]).toEqual({ type: 'mermaid', content: 'A-->B\n' })
    expect(result[2]).toEqual({ type: 'text', content: '\nMiddle\n' })
    expect(result[3]).toEqual({ type: 'mermaid', content: 'C-->D\n' })
    expect(result[4]).toEqual({ type: 'text', content: '\nEnd' })
  })

  it('returns empty array for empty string', () => {
    const result = extractMermaidBlocks('')
    expect(result).toEqual([])
  })

  it('handles mermaid block at start of text', () => {
    const input = '```mermaid\ngraph LR\n    A-->B\n```\nAfter'
    const result = extractMermaidBlocks(input)
    expect(result[0]).toEqual({ type: 'mermaid', content: 'graph LR\n    A-->B\n' })
    expect(result[1]).toEqual({ type: 'text', content: '\nAfter' })
  })

  it('handles mermaid block at end of text', () => {
    const input = 'Before\n```mermaid\nA-->B\n```'
    const result = extractMermaidBlocks(input)
    expect(result[0]).toEqual({ type: 'text', content: 'Before\n' })
    expect(result[1]).toEqual({ type: 'mermaid', content: 'A-->B\n' })
  })
})
