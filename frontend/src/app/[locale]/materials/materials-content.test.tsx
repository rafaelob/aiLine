import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MaterialsContent } from './materials-content'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    article: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <article {...safe}>{children as React.ReactNode}</article>
    },
    form: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, onSubmit, ...safe } = rest
      return <form onSubmit={onSubmit as React.FormEventHandler} {...safe}>{children as React.ReactNode}</form>
    },
  },
}))

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => `materials.${key}`,
}))

function mockFetchEmpty() {
  return vi.fn((url: string) => {
    if (typeof url === 'string' && url.includes('/materials')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) })
  })
}

function mockFetchWithMaterials() {
  const materials = [
    {
      id: '1',
      teacher_id: 'dev-teacher',
      subject: 'Science',
      title: 'Photosynthesis Guide',
      content: 'A comprehensive guide about photosynthesis.',
      tags: ['biology', 'plants'],
      created_at: '2026-02-10T10:00:00Z',
    },
  ]
  return vi.fn((url: string, opts?: RequestInit) => {
    if (typeof url === 'string' && url.includes('/materials') && opts?.method === 'POST') {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ id: '2' }) })
    }
    if (typeof url === 'string' && url.includes('/materials')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(materials) })
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) })
  })
}

describe('MaterialsContent', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetchEmpty())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders upload button', async () => {
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('materials.upload')).toBeInTheDocument()
    })
  })

  it('shows empty state when no materials', async () => {
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('materials.empty')).toBeInTheDocument()
      expect(screen.getByText('materials.empty_hint')).toBeInTheDocument()
      expect(screen.getByText('materials.empty_cta')).toBeInTheDocument()
    })
  })

  it('renders materials when API returns data', async () => {
    vi.stubGlobal('fetch', mockFetchWithMaterials())
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('Photosynthesis Guide')).toBeInTheDocument()
      expect(screen.getByText('Science')).toBeInTheDocument()
    })
  })

  it('shows upload form when button clicked', async () => {
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('materials.upload')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('materials.upload'))
    expect(screen.getByLabelText('materials.field_title')).toBeInTheDocument()
    expect(screen.getByLabelText('materials.field_subject')).toBeInTheDocument()
    expect(screen.getByLabelText('materials.field_content')).toBeInTheDocument()
    expect(screen.getByLabelText('materials.field_tags')).toBeInTheDocument()
  })

  it('submits form and calls API', async () => {
    const fetchMock = mockFetchWithMaterials()
    vi.stubGlobal('fetch', fetchMock)
    render(<MaterialsContent />)

    await waitFor(() => {
      expect(screen.getByText('materials.upload')).toBeInTheDocument()
    })
    // Open form via empty CTA button since the upload button might be hidden
    // after materials load; use the first available button
    const uploadBtn = screen.getByText('materials.upload')
    fireEvent.click(uploadBtn)

    // Fill the form — use queryByLabelText since labels use translation keys
    const titleInput = screen.getByLabelText('materials.field_title')
    const subjectInput = screen.getByLabelText('materials.field_subject')
    const contentInput = screen.getByLabelText('materials.field_content')

    fireEvent.change(titleInput, { target: { value: 'New Material' } })
    fireEvent.change(subjectInput, { target: { value: 'Math' } })
    fireEvent.change(contentInput, { target: { value: 'Math content here' } })

    const submitBtn = screen.getByText('materials.submit')
    fireEvent.click(submitBtn)

    await waitFor(() => {
      const postCalls = fetchMock.mock.calls.filter(
        (call: unknown[]) => (call[1] as RequestInit)?.method === 'POST'
      )
      expect(postCalls.length).toBe(1)
    })
  })

  it('shows cancel button in form', async () => {
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('materials.upload')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('materials.upload'))
    expect(screen.getByText('materials.cancel')).toBeInTheDocument()
  })

  it('hides form when cancel clicked', async () => {
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('materials.upload')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('materials.upload'))
    expect(screen.getByLabelText('materials.field_title')).toBeInTheDocument()

    fireEvent.click(screen.getByText('materials.cancel'))
    expect(screen.queryByLabelText('materials.field_title')).not.toBeInTheDocument()
  })

  it('renders material tags', async () => {
    vi.stubGlobal('fetch', mockFetchWithMaterials())
    render(<MaterialsContent />)
    await waitFor(() => {
      expect(screen.getByText('biology')).toBeInTheDocument()
      expect(screen.getByText('plants')).toBeInTheDocument()
    })
  })

  it('handles fetch error gracefully', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))))
    render(<MaterialsContent />)
    await waitFor(() => {
      // Should show empty state — no crash
      expect(screen.getByText('materials.empty')).toBeInTheDocument()
    })
  })
})
