import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SettingsContent } from './settings-content'

describe('SettingsContent', () => {
  it('renders AI model section', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.ai_model')).toBeInTheDocument()
    expect(screen.getByText('settings.ai_model_desc')).toBeInTheDocument()
  })

  it('renders auto-routed model by default', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.auto_routed')).toBeInTheDocument()
  })

  it('renders language section with current locale', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.language')).toBeInTheDocument()
  })

  it('renders accessibility section with link to preferences', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.accessibility_settings')).toBeInTheDocument()
    const link = screen.getByText('settings.open_preferences')
    expect(link.closest('a')).toHaveAttribute('href', '/pt-BR/accessibility')
  })

  it('renders privacy section with PrivacyPanel', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.privacy')).toBeInTheDocument()
    expect(screen.getByText('settings.privacy_desc')).toBeInTheDocument()
  })

  it('renders about section with version', () => {
    render(<SettingsContent />)
    expect(screen.getByText('settings.about')).toBeInTheDocument()
    expect(screen.getByText(/v0\.2\.0/)).toBeInTheDocument()
  })

  it('has proper section landmarks via aria-labelledby', () => {
    render(<SettingsContent />)
    expect(document.getElementById('settings-ai-model')).toBeInTheDocument()
    expect(document.getElementById('settings-language')).toBeInTheDocument()
    expect(document.getElementById('settings-accessibility')).toBeInTheDocument()
    expect(document.getElementById('settings-privacy')).toBeInTheDocument()
    expect(document.getElementById('settings-about')).toBeInTheDocument()
  })
})
