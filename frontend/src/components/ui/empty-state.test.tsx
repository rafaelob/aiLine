import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './empty-state'

describe('EmptyState', () => {
  const icon = <svg data-testid="empty-icon" />

  it('renders the title and description', () => {
    render(
      <EmptyState icon={icon} title="No items" description="Create your first item" />
    )
    expect(screen.getByText('No items')).toBeInTheDocument()
    expect(screen.getByText('Create your first item')).toBeInTheDocument()
  })

  it('renders the icon container', () => {
    render(
      <EmptyState icon={icon} title="Empty" description="Nothing here" />
    )
    expect(screen.getByTestId('empty-icon')).toBeInTheDocument()
  })

  it('renders CTA link when action is provided', () => {
    render(
      <EmptyState
        icon={icon}
        title="No plans"
        description="Get started"
        action={{ label: 'Create Plan', href: '/plans' }}
      />
    )
    const link = screen.getByText('Create Plan')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/plans')
  })

  it('does not render CTA when action is not provided', () => {
    render(
      <EmptyState icon={icon} title="Empty" description="No data" />
    )
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('uses text-balance on title and description', () => {
    render(
      <EmptyState icon={icon} title="Balanced" description="Also balanced" />
    )
    const title = screen.getByText('Balanced')
    expect(title.className).toContain('text-balance')
  })

  it('applies custom className', () => {
    const { container } = render(
      <EmptyState icon={icon} title="Test" description="Test" className="custom-class" />
    )
    expect((container.firstChild as HTMLElement).className).toContain('custom-class')
  })
})
