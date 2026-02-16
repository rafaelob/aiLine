import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Layout from './layout'

describe('AccessibilityLayout', () => {
  it('renders children', () => {
    render(
      <Layout params={Promise.resolve({ locale: 'en' })}>
        <p>test content</p>
      </Layout>,
    )
    expect(screen.getByText('test content')).toBeInTheDocument()
  })
})
