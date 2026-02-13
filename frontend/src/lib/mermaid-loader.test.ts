import { describe, it, expect, vi } from 'vitest'

// Mock mermaid as a dynamic import
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn().mockResolvedValue({ svg: '<svg></svg>' }),
    parse: vi.fn(),
  },
}))

describe('loadMermaid', () => {
  it('returns the mermaid default export', async () => {
    const { loadMermaid } = await import('./mermaid-loader')
    const mermaid = await loadMermaid()

    expect(mermaid).toBeDefined()
    expect(mermaid.initialize).toBeDefined()
    expect(mermaid.render).toBeDefined()
  })

  it('returns same instance on repeated calls', async () => {
    const { loadMermaid } = await import('./mermaid-loader')
    const first = await loadMermaid()
    const second = await loadMermaid()

    expect(first).toBe(second)
  })
})
