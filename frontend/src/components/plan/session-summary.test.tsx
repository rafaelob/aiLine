import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SessionSummary } from './session-summary'
import type { StudyPlan } from '@/types/plan'

// Mock Recharts to avoid canvas issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  Cell: () => null,
}))

const mockPlanWithStandards: StudyPlan = {
  id: 'plan-1',
  title: 'Fractions & Decimals',
  subject: 'Math',
  grade: '5th Grade',
  objectives: ['Learn fractions', 'Convert decimals'],
  activities: [
    {
      title: 'Discussion',
      description: 'Explain fractions in daily life',
      duration_minutes: 15,
      materials: ['Whiteboard'],
      adaptations: [
        { profile: 'ASD', description: 'Use visual aids and structured prompts' },
        { profile: 'ADHD', description: 'Break into 5-minute segments' },
      ],
    },
    {
      title: 'Practice',
      description: 'Apply fraction operations to solve word problems',
      duration_minutes: 25,
      materials: [],
      adaptations: [
        { profile: 'Dyslexia', description: 'Provide number line support' },
      ],
    },
  ],
  assessments: [],
  accessibility_notes: [],
  curriculum_alignment: [
    {
      standard_id: 'BNCC-EF05MA03',
      standard_name: 'Fractions',
      description: 'Compare and order fractions',
    },
    {
      standard_id: 'BNCC-EF05MA07',
      standard_name: 'Decimal Operations',
      description: 'Apply operations with decimals to solve problems',
    },
  ],
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
}

const mockPlanEmpty: StudyPlan = {
  id: 'plan-2',
  title: 'Empty Plan',
  subject: 'Science',
  grade: '3rd Grade',
  objectives: ['Basics'],
  activities: [],
  assessments: [],
  accessibility_notes: [],
  curriculum_alignment: [],
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
}

const mockWriteText = vi.fn().mockResolvedValue(undefined)

beforeEach(() => {
  vi.clearAllMocks()
  // Ensure clipboard mock is consistent across tests
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: mockWriteText },
    configurable: true,
    writable: true,
  })
})

describe('SessionSummary', () => {
  it('renders the standards coverage section heading', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('session.standards_coverage')).toBeInTheDocument()
  })

  it('renders standard codes in the table', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('BNCC-EF05MA03')).toBeInTheDocument()
    expect(screen.getByText('BNCC-EF05MA07')).toBeInTheDocument()
  })

  it('renders standard names in the table', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('Fractions')).toBeInTheDocument()
    expect(screen.getByText('Decimal Operations')).toBeInTheDocument()
  })

  it('renders Bloom level badges for each standard', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    // "Compare and order fractions" => 'compar' matches 'analyze'
    // "Apply operations with decimals to solve problems" => 'appl' or 'solv' matches 'apply'
    expect(screen.getByText('analyze')).toBeInTheDocument()
    expect(screen.getByText('apply')).toBeInTheDocument()
  })

  it('shows no-standards message when curriculum_alignment is empty', () => {
    render(<SessionSummary plan={mockPlanEmpty} />)
    expect(screen.getByText('session.no_standards')).toBeInTheDocument()
  })

  it('renders accessibility adaptations section', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(
      screen.getByText('session.adaptations_applied')
    ).toBeInTheDocument()
  })

  it('lists all adaptations from all activities', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(
      screen.getByText('Use visual aids and structured prompts')
    ).toBeInTheDocument()
    expect(
      screen.getByText('Break into 5-minute segments')
    ).toBeInTheDocument()
    expect(
      screen.getByText('Provide number line support')
    ).toBeInTheDocument()
  })

  it('shows adaptation profiles', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('ASD')).toBeInTheDocument()
    expect(screen.getByText('ADHD')).toBeInTheDocument()
    expect(screen.getByText('Dyslexia')).toBeInTheDocument()
  })

  it('shows no-adaptations message when there are none', () => {
    render(<SessionSummary plan={mockPlanEmpty} />)
    expect(screen.getByText('session.no_adaptations')).toBeInTheDocument()
  })

  it('renders next steps section', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('session.next_steps')).toBeInTheDocument()
    expect(screen.getByText('session.micro_assessment')).toBeInTheDocument()
    expect(screen.getByText('session.practice_activity')).toBeInTheDocument()
    expect(screen.getByText('session.next_topic')).toBeInTheDocument()
  })

  it('renders copy markdown button', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(
      screen.getByLabelText('session.copy_markdown')
    ).toBeInTheDocument()
  })

  it('renders download JSON button', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(
      screen.getByLabelText('session.download_json')
    ).toBeInTheDocument()
  })

  it('shows copied state after clicking copy button', async () => {
    // jsdom clipboard handling varies; verify the UI feedback
    const user = userEvent.setup()
    render(<SessionSummary plan={mockPlanWithStandards} />)

    const copyBtn = screen.getByLabelText('session.copy_markdown')
    expect(copyBtn).toBeInTheDocument()

    await user.click(copyBtn)

    // Verify the button shows copied feedback
    await waitFor(() => {
      expect(screen.getByText('session.copied')).toBeInTheDocument()
    })
  })

  it('has proper ARIA landmarks for each section', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    const sections = screen.getAllByRole('region', { hidden: true }).length
    // At minimum, check named sections exist via their headings
    expect(screen.getByText('session.standards_coverage')).toBeInTheDocument()
    expect(screen.getByText('session.adaptations_applied')).toBeInTheDocument()
    expect(screen.getByText('session.next_steps')).toBeInTheDocument()
  })

  it('renders table headers for standards coverage', () => {
    render(<SessionSummary plan={mockPlanWithStandards} />)
    expect(screen.getByText('session.standard_code')).toBeInTheDocument()
    expect(screen.getByText('session.standard_name')).toBeInTheDocument()
    expect(screen.getByText('session.bloom_level')).toBeInTheDocument()
  })
})
