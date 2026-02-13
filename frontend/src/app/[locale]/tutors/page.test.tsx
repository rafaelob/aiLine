import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import TutorsPage from './page'

// Mock TutorChat to isolate page-level tests
vi.mock('@/components/tutor/tutor-chat', () => ({
  TutorChat: () => <div data-testid="tutor-chat">Tutor Chat Mock</div>,
}))

describe('TutorsPage', () => {
  it('renders the page title', () => {
    render(<TutorsPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading.textContent).toBe('tutor.title')
  })

  it('renders the page subtitle', () => {
    render(<TutorsPage />)
    expect(screen.getByText('tutor.subtitle')).toBeInTheDocument()
  })

  it('renders the TutorChat component', () => {
    render(<TutorsPage />)
    expect(screen.getByTestId('tutor-chat')).toBeInTheDocument()
  })

  it('wraps content in a max-width container', () => {
    const { container } = render(<TutorsPage />)
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('max-w-4xl')
  })

  it('renders a header element', () => {
    render(<TutorsPage />)
    const header = document.querySelector('header')
    expect(header).toBeInTheDocument()
  })

  it('has proper heading hierarchy', () => {
    render(<TutorsPage />)
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1.textContent).toBe('tutor.title')
  })
})
