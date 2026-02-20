import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import MaterialsPage from './page'

vi.mock('./materials-content', () => ({
  MaterialsContent: () => <div data-testid="materials-content">Materials</div>,
}))

describe('MaterialsPage', () => {
  it('renders heading and description', async () => {
    const Component = await MaterialsPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByText('materials.title')).toBeInTheDocument()
    expect(screen.getByText('materials.upload_desc')).toBeInTheDocument()
  })

  it('renders MaterialsContent component', async () => {
    const Component = await MaterialsPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByTestId('materials-content')).toBeInTheDocument()
  })
})
