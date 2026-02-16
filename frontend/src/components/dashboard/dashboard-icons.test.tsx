import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import {
  StatPlansIcon,
  StatStudentsIcon,
  StatScoreIcon,
  PlanIcon,
  UploadIcon,
  TutorIcon,
  ArrowRightIcon,
  PlayIcon,
} from './dashboard-icons'

describe('Dashboard Icons', () => {
  describe('StatPlansIcon', () => {
    it('renders an SVG', () => {
      const { container } = render(<StatPlansIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('is hidden from assistive tech', () => {
      const { container } = render(<StatPlansIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('has 24x24 dimensions', () => {
      const { container } = render(<StatPlansIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '24')
      expect(svg).toHaveAttribute('height', '24')
    })
  })

  describe('StatStudentsIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<StatStudentsIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('StatScoreIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<StatScoreIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('PlanIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<PlanIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('UploadIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<UploadIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('TutorIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<TutorIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('ArrowRightIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<ArrowRightIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('applies custom className', () => {
      const { container } = render(<ArrowRightIcon className="text-red-500" />)
      const svg = container.querySelector('svg')
      expect(svg?.getAttribute('class')).toContain('text-red-500')
    })

    it('has 16x16 dimensions', () => {
      const { container } = render(<ArrowRightIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '16')
      expect(svg).toHaveAttribute('height', '16')
    })
  })

  describe('PlayIcon', () => {
    it('renders an SVG with aria-hidden', () => {
      const { container } = render(<PlayIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('has 24x24 dimensions', () => {
      const { container } = render(<PlayIcon />)
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '24')
      expect(svg).toHaveAttribute('height', '24')
    })
  })
})
