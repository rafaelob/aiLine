import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WizardSteps } from './wizard-steps'
import type { PlanGenerationRequest } from '@/types/plan'

// Mock the PlanGenerationRequest type
vi.mock('@/types/plan', () => ({
  // Type-only export, no runtime needed
}))

const baseFormData: PlanGenerationRequest = {
  subject: '',
  grade: '',
  prompt: '',
  accessibility_profile: 'standard',
  locale: 'en',
}

describe('WizardSteps', () => {
  const user = userEvent.setup()
  const defaultProps = {
    step: 0,
    formData: baseFormData,
    errors: {},
    onUpdateField: vi.fn(),
    onValidateStep: vi.fn(() => true),
  }

  describe('Step 0: Subject & Grade', () => {
    it('renders subject and grade inputs', () => {
      render(<WizardSteps {...defaultProps} step={0} />)
      expect(screen.getByLabelText('plans.form.subject')).toBeInTheDocument()
      expect(screen.getByLabelText('plans.form.grade')).toBeInTheDocument()
    })

    it('calls onUpdateField when subject changes', async () => {
      const onUpdateField = vi.fn()
      render(<WizardSteps {...defaultProps} step={0} onUpdateField={onUpdateField} />)
      await user.type(screen.getByLabelText('plans.form.subject'), 'Math')
      expect(onUpdateField).toHaveBeenCalledWith('subject', 'M')
    })

    it('calls onUpdateField when grade changes', async () => {
      const onUpdateField = vi.fn()
      render(<WizardSteps {...defaultProps} step={0} onUpdateField={onUpdateField} />)
      await user.type(screen.getByLabelText('plans.form.grade'), '6')
      expect(onUpdateField).toHaveBeenCalledWith('grade', '6')
    })

    it('shows error messages for subject', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={0}
          errors={{ subject: 'Subject is required' }}
        />,
      )
      expect(screen.getByText('Subject is required')).toBeInTheDocument()
    })

    it('shows error messages for grade', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={0}
          errors={{ grade: 'Grade is required' }}
        />,
      )
      expect(screen.getByText('Grade is required')).toBeInTheDocument()
    })

    it('marks subject as aria-invalid when error exists', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={0}
          errors={{ subject: 'Required' }}
        />,
      )
      expect(screen.getByLabelText('plans.form.subject')).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Step 1: Accessibility Profile', () => {
    it('renders radiogroup with profiles', () => {
      render(<WizardSteps {...defaultProps} step={1} />)
      expect(screen.getByRole('radiogroup')).toBeInTheDocument()
      // Should have 7 accessibility profiles
      const radios = screen.getAllByRole('radio')
      expect(radios).toHaveLength(7)
    })

    it('marks selected profile as checked', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={1}
          formData={{ ...baseFormData, accessibility_profile: 'tea' }}
        />,
      )
      const teaRadio = screen.getByRole('radio', { name: /plans\.form\.accessibility_profiles\.tea/i })
      expect(teaRadio).toHaveAttribute('aria-checked', 'true')
    })

    it('calls onUpdateField when profile is clicked', async () => {
      const onUpdateField = vi.fn()
      render(
        <WizardSteps
          {...defaultProps}
          step={1}
          onUpdateField={onUpdateField}
        />,
      )
      const radios = screen.getAllByRole('radio')
      // Click the second profile (tea)
      await user.click(radios[1])
      expect(onUpdateField).toHaveBeenCalledWith('accessibility_profile', 'tea')
    })
  })

  describe('Step 2: Content/Prompt', () => {
    it('renders textarea for prompt', () => {
      render(<WizardSteps {...defaultProps} step={2} />)
      expect(screen.getByLabelText('plans.form.prompt')).toBeInTheDocument()
    })

    it('shows character counter', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={2}
          formData={{ ...baseFormData, prompt: 'Hello' }}
        />,
      )
      expect(screen.getByText('5 / 2000')).toBeInTheDocument()
    })

    it('shows prompt error', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={2}
          errors={{ prompt: 'Prompt is required' }}
        />,
      )
      expect(screen.getByText('Prompt is required')).toBeInTheDocument()
    })
  })

  describe('Step 3: Review', () => {
    it('renders review summary with form data', () => {
      render(
        <WizardSteps
          {...defaultProps}
          step={3}
          formData={{
            subject: 'Science',
            grade: '6th',
            prompt: 'Create an inclusive lesson',
            accessibility_profile: 'tea',
            locale: 'en',
          }}
        />,
      )
      expect(screen.getByText('plans.wizard.review_title')).toBeInTheDocument()
      expect(screen.getByText('Science')).toBeInTheDocument()
      expect(screen.getByText('6th')).toBeInTheDocument()
      expect(screen.getByText('Create an inclusive lesson')).toBeInTheDocument()
    })
  })
})
