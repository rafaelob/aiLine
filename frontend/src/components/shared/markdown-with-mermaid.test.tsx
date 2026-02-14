import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MarkdownWithMermaid } from './markdown-with-mermaid'

// Mock the MermaidRenderer to avoid dynamic import
vi.mock('./mermaid-renderer', () => ({
  default: ({ code }: { code: string }) => (
    <div data-testid="mermaid-renderer">{code}</div>
  ),
  extractMermaidBlocks: vi.fn().mockImplementation((text: string) => {
    const pattern = /```mermaid\n([\s\S]*?)```/g
    const segments: Array<
      { type: 'text'; content: string } | { type: 'mermaid'; content: string }
    > = []
    let lastIndex = 0
    let match: RegExpExecArray | null
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
      }
      segments.push({ type: 'mermaid', content: match[1] })
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < text.length) {
      segments.push({ type: 'text', content: text.slice(lastIndex) })
    }
    return segments
  }),
}))

describe('MarkdownWithMermaid', () => {
  it('renders plain text without mermaid blocks', () => {
    render(<MarkdownWithMermaid content="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders with the provided textClassName', () => {
    const { container } = render(
      <MarkdownWithMermaid content="Styled text" textClassName="custom-class" />
    )
    const span = container.querySelector('span')
    expect(span).toHaveClass('custom-class')
  })

  it('renders nothing when content is empty', () => {
    const { container } = render(<MarkdownWithMermaid content="" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders mermaid blocks via MermaidRenderer', async () => {
    const content = 'Before\n```mermaid\ngraph TD\nA-->B\n```\nAfter'
    const { container } = render(<MarkdownWithMermaid content={content} />)
    expect(await screen.findByTestId('mermaid-renderer')).toBeInTheDocument()
    // Text segments are rendered as spans
    const spans = container.querySelectorAll('span')
    expect(spans.length).toBeGreaterThanOrEqual(2)
  })

  it('renders multiple mermaid blocks', async () => {
    const content = 'Text1\n```mermaid\ngraph A\n```\nMiddle\n```mermaid\ngraph B\n```\nEnd'
    render(<MarkdownWithMermaid content={content} />)
    const renderers = await screen.findAllByTestId('mermaid-renderer')
    expect(renderers).toHaveLength(2)
  })

  it('renders only mermaid block when no surrounding text', async () => {
    const content = '```mermaid\nflowchart LR\nA-->B\n```'
    render(<MarkdownWithMermaid content={content} />)
    expect(await screen.findByTestId('mermaid-renderer')).toBeInTheDocument()
  })
})
