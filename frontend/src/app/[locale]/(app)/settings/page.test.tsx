import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import SettingsPage from './page'

vi.mock('./settings-content', () => ({
  SettingsContent: () => <div data-testid="settings-content">Settings Content</div>,
}))

describe('SettingsPage', () => {
  it('renders heading and description', async () => {
    const Component = await SettingsPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByText('settings.title')).toBeInTheDocument()
    expect(screen.getByText('settings.description')).toBeInTheDocument()
  })

  it('renders SettingsContent component', async () => {
    const Component = await SettingsPage({
      params: Promise.resolve({ locale: 'en' }),
    })
    render(Component)
    expect(screen.getByTestId('settings-content')).toBeInTheDocument()
  })
})
