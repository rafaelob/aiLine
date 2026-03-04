import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignLanguageSelector, SIGN_LANGUAGES } from './sign-language-selector'

// jsdom does not implement scrollIntoView
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe('SignLanguageSelector', () => {
  const user = userEvent.setup()

  it('renders with default ASL selection', () => {
    render(<SignLanguageSelector />)
    expect(screen.getByText('American Sign Language')).toBeInTheDocument()
  })

  it('renders custom label', () => {
    render(<SignLanguageSelector label="Choose Language" />)
    expect(screen.getByText('Choose Language')).toBeInTheDocument()
  })

  it('shows selected language by value prop', () => {
    render(<SignLanguageSelector value="libras" />)
    expect(screen.getByText('Brazilian Sign Language')).toBeInTheDocument()
  })

  it('has combobox role with correct ARIA attributes', () => {
    render(<SignLanguageSelector />)
    const combobox = screen.getByRole('combobox')
    expect(combobox).toHaveAttribute('aria-expanded', 'false')
    expect(combobox).toHaveAttribute('aria-haspopup', 'listbox')
  })

  it('opens dropdown on click', async () => {
    render(<SignLanguageSelector />)
    const combobox = screen.getByRole('combobox')
    await user.click(combobox)

    expect(combobox).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('listbox')).toBeInTheDocument()
  })

  it('shows all 8 sign languages when open', async () => {
    render(<SignLanguageSelector />)
    await user.click(screen.getByRole('combobox'))

    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(8)
  })

  it('calls onChange when an option is clicked', async () => {
    const onChange = vi.fn()
    render(<SignLanguageSelector onChange={onChange} />)
    await user.click(screen.getByRole('combobox'))

    // Use fireEvent.click to bypass mousedown-based outside-click timing
    const options = screen.getAllByRole('option')
    const librasOption = options.find((o) => o.id.includes('libras'))!
    fireEvent.click(librasOption)

    expect(onChange).toHaveBeenCalledWith('libras')
  })

  it('closes dropdown after selection', async () => {
    const onChange = vi.fn()
    render(<SignLanguageSelector onChange={onChange} />)
    await user.click(screen.getByRole('combobox'))

    const options = screen.getAllByRole('option')
    const librasOption = options.find((o) => o.id.includes('libras'))!
    fireEvent.click(librasOption)

    expect(screen.getByRole('combobox')).toHaveAttribute('aria-expanded', 'false')
  })

  it('marks the current value as selected', async () => {
    render(<SignLanguageSelector value="bsl" />)
    await user.click(screen.getByRole('combobox'))

    // Use option IDs to avoid duplicate text matches (BSL name === nameNative)
    const options = screen.getAllByRole('option')
    const bslOption = options.find((o) => o.id.includes('bsl'))!
    const aslOption = options.find((o) => o.id.includes('asl'))!
    expect(bslOption).toHaveAttribute('aria-selected', 'true')
    expect(aslOption).toHaveAttribute('aria-selected', 'false')
  })

  it('closes on Escape key', async () => {
    render(<SignLanguageSelector />)
    await user.click(screen.getByRole('combobox'))
    expect(screen.getByRole('listbox')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-expanded', 'false')
  })

  it('navigates with ArrowDown and ArrowUp', async () => {
    const onChange = vi.fn()
    render(<SignLanguageSelector value="asl" onChange={onChange} />)
    const combobox = screen.getByRole('combobox')

    // Open with ArrowDown
    await user.click(combobox)

    // Move down
    await user.keyboard('{ArrowDown}')
    // Select with Enter
    await user.keyboard('{Enter}')

    // Should have selected BSL (index 1, since ASL is index 0 which is focused on open)
    expect(onChange).toHaveBeenCalledWith('bsl')
  })

  it('wraps around from last to first with ArrowDown', async () => {
    const onChange = vi.fn()
    render(<SignLanguageSelector value="isl" onChange={onChange} />)
    await user.click(screen.getByRole('combobox'))

    // ISL is last (index 7). ArrowDown should wrap to index 0 (ASL)
    await user.keyboard('{ArrowDown}')
    await user.keyboard('{Enter}')

    expect(onChange).toHaveBeenCalledWith('asl')
  })

  it('exports SIGN_LANGUAGES array with 8 entries', () => {
    expect(SIGN_LANGUAGES).toHaveLength(8)
    for (const sl of SIGN_LANGUAGES) {
      expect(sl.code).toBeTruthy()
      expect(sl.name).toBeTruthy()
      expect(sl.nameNative).toBeTruthy()
      expect(sl.country).toBeTruthy()
      expect(sl.flag).toBeTruthy()
      expect(sl.estimatedUsers).toBeTruthy()
    }
  })

  it('shows native name and country in dropdown options', async () => {
    render(<SignLanguageSelector />)
    await user.click(screen.getByRole('combobox'))

    expect(screen.getByText('Lingua Brasileira de Sinais')).toBeInTheDocument()
    expect(screen.getByText('Brazil')).toBeInTheDocument()
  })

  it('defaults to ASL when invalid value is provided', () => {
    render(<SignLanguageSelector value="invalid-code" />)
    // Falls back to first language (ASL)
    expect(screen.getByText('American Sign Language')).toBeInTheDocument()
  })
})
