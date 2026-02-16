import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import TutorsPage from './page'

// Mock TutorChat to isolate page-level tests
vi.mock('@/components/tutor/tutor-chat', () => ({
  TutorChat: () => <div data-testid="tutor-chat">Tutor Chat Mock</div>,
}))

const defaultParams = Promise.resolve({ locale: 'pt-BR' })

describe('TutorsPage', () => {
  it('renders the page title', async () => {
    const page = await TutorsPage({ params: defaultParams })
    render(page)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading.textContent).toBe('tutor.title')
  })

  it('renders the page subtitle', async () => {
    const page = await TutorsPage({ params: defaultParams })
    render(page)
    expect(screen.getByText('tutor.subtitle')).toBeInTheDocument()
  })

  it('renders the TutorChat component', async () => {
    const page = await TutorsPage({ params: defaultParams })
    render(page)
    expect(screen.getByTestId('tutor-chat')).toBeInTheDocument()
  })

  it('wraps content in a max-width container', async () => {
    const page = await TutorsPage({ params: defaultParams })
    const { container } = render(page)
    // PageTransition is the outermost wrapper, max-w-4xl is inside
    const maxWContainer = container.querySelector('.max-w-4xl')
    expect(maxWContainer).toBeInTheDocument()
  })

  it('renders a header element', async () => {
    const page = await TutorsPage({ params: defaultParams })
    render(page)
    const header = document.querySelector('header')
    expect(header).toBeInTheDocument()
  })

  it('has proper heading hierarchy', async () => {
    const page = await TutorsPage({ params: defaultParams })
    render(page)
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1.textContent).toBe('tutor.title')
  })
})
