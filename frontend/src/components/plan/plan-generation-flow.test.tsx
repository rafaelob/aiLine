import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PlanGenerationFlow } from './plan-generation-flow'

vi.mock('motion/react', () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, variants: _v, ...safe } = rest
      return <div {...safe}>{children as React.ReactNode}</div>
    },
    span: (props: Record<string, unknown>) => {
      const { animate: _a, transition: _t, ...safe } = props
      return <span {...safe}>{props.children as React.ReactNode}</span>
    },
    p: (props: Record<string, unknown>) => {
      const { initial: _i, animate: _a, exit: _e, transition: _t, ...safe } = props
      return <p {...safe}>{props.children as React.ReactNode}</p>
    },
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockStartGeneration = vi.fn()
const mockCancel = vi.fn()
let mockHookState = {
  isRunning: false,
  plan: null as unknown,
  error: null as string | null,
  stages: [],
  qualityReport: null,
  score: null as number | null,
}

vi.mock('@/hooks/use-pipeline-sse', () => ({
  usePipelineSSE: () => ({
    startGeneration: mockStartGeneration,
    cancel: mockCancel,
    ...mockHookState,
  }),
}))

vi.mock('@/components/pipeline/pipeline-viewer', () => ({
  PipelineViewer: () => <div data-testid="pipeline-viewer">Pipeline</div>,
}))

vi.mock('./plan-tabs', () => ({
  PlanTabs: () => <div data-testid="plan-tabs">Plan Tabs</div>,
}))

describe('PlanGenerationFlow', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    mockHookState = {
      isRunning: false,
      plan: null,
      error: null,
      stages: [],
      qualityReport: null,
      score: null,
    }
  })

  it('renders the first wizard step with Subject and Grade fields', () => {
    render(<PlanGenerationFlow />)
    expect(screen.getByLabelText('plans.form.subject')).toBeInTheDocument()
    expect(screen.getByLabelText('plans.form.grade')).toBeInTheDocument()
  })

  it('shows validation error when trying to advance with empty fields', async () => {
    render(<PlanGenerationFlow />)
    const nextBtn = screen.getByText('plans.wizard.next')
    await user.click(nextBtn)
    // Should show required errors
    const errors = screen.getAllByRole('alert')
    expect(errors.length).toBeGreaterThanOrEqual(1)
  })

  it('advances to step 2 when fields are valid', async () => {
    render(<PlanGenerationFlow />)

    const subjectInput = screen.getByLabelText('plans.form.subject')
    await user.type(subjectInput, 'Science')

    const gradeInput = screen.getByLabelText('plans.form.grade')
    await user.type(gradeInput, '6th Grade')

    const nextBtn = screen.getByText('plans.wizard.next')
    await user.click(nextBtn)

    // Step 2: accessibility profile cards should be visible
    expect(screen.getByText('plans.wizard.profile_description')).toBeInTheDocument()
  })

  it('navigates back from step 2 to step 1', async () => {
    render(<PlanGenerationFlow />)

    // Fill step 1 and advance
    await user.type(screen.getByLabelText('plans.form.subject'), 'Math')
    await user.type(screen.getByLabelText('plans.form.grade'), '5th')
    await user.click(screen.getByText('plans.wizard.next'))

    // Go back
    const backBtn = screen.getByText('plans.wizard.back')
    await user.click(backBtn)

    // Should be on step 1 again
    expect(screen.getByLabelText('plans.form.subject')).toBeInTheDocument()
  })

  it('renders step indicator with 4 steps', () => {
    render(<PlanGenerationFlow />)
    // 4 step labels
    expect(screen.getByText('plans.wizard.step_subject')).toBeInTheDocument()
    expect(screen.getByText('plans.wizard.step_profile')).toBeInTheDocument()
    expect(screen.getByText('plans.wizard.step_prompt')).toBeInTheDocument()
    expect(screen.getByText('plans.wizard.step_review')).toBeInTheDocument()
  })

  it('shows pipeline viewer when running', () => {
    mockHookState = { ...mockHookState, isRunning: true }
    render(<PlanGenerationFlow />)

    expect(screen.getByTestId('pipeline-viewer')).toBeInTheDocument()
    expect(screen.getByText('plans.cancel')).toBeInTheDocument()
  })

  it('calls cancel when cancel button is clicked', async () => {
    mockHookState = { ...mockHookState, isRunning: true }
    render(<PlanGenerationFlow />)

    await user.click(screen.getByText('plans.cancel'))
    expect(mockCancel).toHaveBeenCalledTimes(1)
  })

  it('shows plan tabs when generation completes', () => {
    mockHookState = {
      ...mockHookState,
      isRunning: false,
      plan: { id: 'plan-1', title: 'Test' },
    }
    render(<PlanGenerationFlow />)

    expect(screen.getByTestId('plan-tabs')).toBeInTheDocument()
  })

  it('shows success message with score when plan is ready', () => {
    mockHookState = {
      ...mockHookState,
      isRunning: false,
      plan: { id: 'plan-1', title: 'Test' },
      score: 85,
    }
    render(<PlanGenerationFlow />)

    expect(screen.getByText('plans.generation_complete')).toBeInTheDocument()
  })

  it('shows error alert when error occurs without running', () => {
    mockHookState = {
      ...mockHookState,
      isRunning: false,
      plan: null,
      error: 'Something failed',
    }
    render(<PlanGenerationFlow />)

    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Something failed')
  })

  it('renders back button as disabled on first step', () => {
    render(<PlanGenerationFlow />)
    const backBtn = screen.getByText('plans.wizard.back')
    expect(backBtn).toBeDisabled()
  })
})
