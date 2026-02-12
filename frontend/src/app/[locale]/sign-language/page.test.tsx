import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import SignLanguagePage from './page'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
  },
}))

vi.mock('@/components/sign-language/webcam-capture', () => ({
  WebcamCapture: () => <div data-testid="webcam-capture">Webcam</div>,
}))

vi.mock('@/components/sign-language/vlibras-widget', () => ({
  VLibrasWidget: () => <div data-testid="vlibras-widget">VLibras</div>,
}))

vi.mock('@/components/sign-language/gesture-list', () => ({
  GestureList: () => <div data-testid="gesture-list">Gestures</div>,
}))

vi.mock('@/components/sign-language/libras-captioning', () => ({
  LibrasCaptioning: () => <div data-testid="libras-captioning">Captioning</div>,
}))

describe('SignLanguagePage', () => {
  it('renders the page title', () => {
    render(<SignLanguagePage />)
    expect(screen.getByText('sign_language.title')).toBeInTheDocument()
  })

  it('renders the subtitle', () => {
    render(<SignLanguagePage />)
    expect(screen.getByText('sign_language.subtitle')).toBeInTheDocument()
  })

  it('renders the WebcamCapture component', () => {
    render(<SignLanguagePage />)
    expect(screen.getByTestId('webcam-capture')).toBeInTheDocument()
  })

  it('renders the GestureList component', () => {
    render(<SignLanguagePage />)
    expect(screen.getByTestId('gesture-list')).toBeInTheDocument()
  })

  it('renders the VLibrasWidget component', () => {
    render(<SignLanguagePage />)
    expect(screen.getByTestId('vlibras-widget')).toBeInTheDocument()
  })

  it('renders the VLibras section title', () => {
    render(<SignLanguagePage />)
    expect(screen.getByText('sign_language.vlibras_title')).toBeInTheDocument()
  })

  it('renders the VLibras description', () => {
    render(<SignLanguagePage />)
    expect(screen.getByText('sign_language.vlibras_description')).toBeInTheDocument()
  })

  it('renders as a main landmark', () => {
    render(<SignLanguagePage />)
    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
  })
})
