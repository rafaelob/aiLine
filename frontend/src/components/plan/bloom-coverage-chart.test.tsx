import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BloomCoverageChart } from './bloom-coverage-chart'

// Mock recharts to avoid canvas/SVG rendering issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children, data }: { children: React.ReactNode; data: unknown[] }) => (
    <div data-testid="bar-chart" data-count={data.length}>{children}</div>
  ),
  Bar: ({ children, dataKey }: { children: React.ReactNode; dataKey: string }) => (
    <div data-testid="bar" data-key={dataKey}>{children}</div>
  ),
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Cell: ({ fill }: { fill: string }) => <div data-testid="cell" data-fill={fill} />,
}))

const sampleData = [
  { standard: 'EF01MA01', name: 'Numbers', bloomLevel: 'remember' },
  { standard: 'EF01MA02', name: 'Addition', bloomLevel: 'understand' },
  { standard: 'EF01MA03', name: 'Subtraction', bloomLevel: 'apply' },
  { standard: 'EF01MA04', name: 'Patterns', bloomLevel: 'analyze' },
  { standard: 'EF01MA05', name: 'Problem Solving', bloomLevel: 'evaluate' },
  { standard: 'EF01MA06', name: 'Projects', bloomLevel: 'create' },
  { standard: 'EF01MA07', name: 'Counting', bloomLevel: 'remember' },
]

describe('BloomCoverageChart', () => {
  it('renders the chart container with img role', () => {
    render(<BloomCoverageChart data={sampleData} />)
    expect(
      screen.getByRole('img', { name: "Bloom's taxonomy coverage chart" })
    ).toBeInTheDocument()
  })

  it('renders ResponsiveContainer', () => {
    render(<BloomCoverageChart data={sampleData} />)
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
  })

  it('renders BarChart with 6 bloom levels', () => {
    render(<BloomCoverageChart data={sampleData} />)
    const chart = screen.getByTestId('bar-chart')
    expect(chart).toBeInTheDocument()
    expect(chart.getAttribute('data-count')).toBe('6')
  })

  it('renders a Bar with dataKey "count"', () => {
    render(<BloomCoverageChart data={sampleData} />)
    const bar = screen.getByTestId('bar')
    expect(bar.getAttribute('data-key')).toBe('count')
  })

  it('renders 6 Cell elements for each bloom level', () => {
    render(<BloomCoverageChart data={sampleData} />)
    const cells = screen.getAllByTestId('cell')
    expect(cells).toHaveLength(6)
  })

  it('renders cells with correct bloom colors', () => {
    render(<BloomCoverageChart data={sampleData} />)
    const cells = screen.getAllByTestId('cell')
    const fills = cells.map((c) => c.getAttribute('data-fill'))
    expect(fills).toContain('#DC2626') // remember
    expect(fills).toContain('#E07E34') // understand
    expect(fills).toContain('#D9A006') // apply
    expect(fills).toContain('#2D8B6E') // analyze
    expect(fills).toContain('#3B82F6') // evaluate
    expect(fills).toContain('#4338CA') // create
  })

  it('renders nothing when data is empty', () => {
    const { container } = render(<BloomCoverageChart data={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when no standards match any bloom level', () => {
    const data = [{ standard: 'X', name: 'Unknown', bloomLevel: 'unknown' }]
    const { container } = render(<BloomCoverageChart data={data} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders chart when only one bloom level has data', () => {
    const data = [{ standard: 'A', name: 'Recall', bloomLevel: 'remember' }]
    render(<BloomCoverageChart data={data} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('renders XAxis and YAxis', () => {
    render(<BloomCoverageChart data={sampleData} />)
    expect(screen.getByTestId('x-axis')).toBeInTheDocument()
    expect(screen.getByTestId('y-axis')).toBeInTheDocument()
  })

  it('renders Tooltip', () => {
    render(<BloomCoverageChart data={sampleData} />)
    expect(screen.getByTestId('tooltip')).toBeInTheDocument()
  })
})
