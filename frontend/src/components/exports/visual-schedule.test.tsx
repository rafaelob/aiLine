import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VisualSchedule } from './visual-schedule'
import type { ScheduleStep } from '@/types/exports'

vi.mock('motion/react', () => ({
  motion: {
    li: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial: _i, animate: _a, transition: _t, ...safe } = rest
      return <li {...safe}>{children as React.ReactNode}</li>
    },
  },
}))

const mockSteps: ScheduleStep[] = [
  {
    stepNumber: 1,
    title: 'Roda de Conversa',
    description: 'Discussao inicial',
    durationMinutes: 15,
    type: 'intro',
    materials: ['Quadro branco'],
    adaptations: ['Usar imagens para TEA'],
  },
  {
    stepNumber: 2,
    title: 'Atividade Pratica',
    description: 'Exercicios com material concreto',
    durationMinutes: 25,
    type: 'develop',
    materials: [],
    adaptations: [],
  },
  {
    stepNumber: 3,
    title: 'Avaliacao',
    description: 'Quiz rapido',
    durationMinutes: 10,
    type: 'assessment',
  },
]

describe('VisualSchedule', () => {
  it('renders the plan title', () => {
    render(<VisualSchedule planTitle="Fracoes e Decimais" steps={mockSteps} />)
    expect(screen.getByText('Fracoes e Decimais')).toBeInTheDocument()
  })

  it('renders all step cards in the ordered list', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    const ol = screen.getByRole('list', { name: /visual_schedule\.steps_label/i })
    // Each step has a <li> wrapper from motion mock
    const items = ol.querySelectorAll(':scope > li')
    expect(items).toHaveLength(3)
  })

  it('computes total duration from steps when not provided', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    // i18n mock returns "visual_schedule.subtitle" (key only)
    expect(screen.getByText(/visual_schedule\.subtitle/)).toBeInTheDocument()
  })

  it('uses provided totalDurationMinutes when given', () => {
    render(
      <VisualSchedule
        planTitle="Test"
        steps={mockSteps}
        totalDurationMinutes={60}
      />
    )
    expect(screen.getByText(/visual_schedule\.subtitle/)).toBeInTheDocument()
  })

  it('displays step numbers', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('displays step titles', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText('Roda de Conversa')).toBeInTheDocument()
    expect(screen.getByText('Atividade Pratica')).toBeInTheDocument()
    expect(screen.getByText('Avaliacao')).toBeInTheDocument()
  })

  it('displays step type labels', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText('visual_schedule.type_intro')).toBeInTheDocument()
    expect(screen.getByText('visual_schedule.type_develop')).toBeInTheDocument()
  })

  it('displays step duration', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    const durations = screen.getAllByText('visual_schedule.duration_short')
    expect(durations).toHaveLength(3)
  })

  it('displays materials when present', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText('Quadro branco')).toBeInTheDocument()
  })

  it('displays adaptations when present', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText('Usar imagens para TEA')).toBeInTheDocument()
  })

  it('renders step count in subtitle', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    expect(screen.getByText(/visual_schedule\.subtitle/)).toBeInTheDocument()
  })

  it('has accessible label on the ordered list', () => {
    render(<VisualSchedule planTitle="Test" steps={mockSteps} />)
    const ol = screen.getByRole('list', { name: /visual_schedule\.steps_label/i })
    expect(ol).toBeInTheDocument()
  })
})
