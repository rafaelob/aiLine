import { describe, it, expect } from 'vitest'
import {
  DEMO_PROMPT,
  DEMO_GRADE,
  DEMO_SUBJECT,
  DEMO_PROFILE,
  DEMO_STEPS,
  DEMO_TRACES,
  DEMO_STUDENT_COUNT,
} from './demo-data'

describe('demo-data', () => {
  it('DEMO_PROMPT is a non-empty string', () => {
    expect(DEMO_PROMPT).toBeTruthy()
    expect(typeof DEMO_PROMPT).toBe('string')
  })

  it('DEMO_GRADE and DEMO_SUBJECT are set', () => {
    expect(DEMO_GRADE).toBe('6th Grade')
    expect(DEMO_SUBJECT).toBe('Science')
  })

  it('DEMO_PROFILE is tea', () => {
    expect(DEMO_PROFILE).toBe('tea')
  })

  it('DEMO_STEPS has 3 steps with target and key', () => {
    expect(DEMO_STEPS).toHaveLength(3)
    for (const step of DEMO_STEPS) {
      expect(step.target).toBeTruthy()
      expect(step.key).toBeTruthy()
    }
  })

  it('DEMO_TRACES has entries with required fields', () => {
    expect(DEMO_TRACES.length).toBeGreaterThan(0)
    for (const trace of DEMO_TRACES) {
      expect(trace.run_id).toBeTruthy()
      expect(trace.status).toMatch(/^(completed|failed)$/)
      expect(trace.total_time_ms).toBeGreaterThan(0)
      expect(trace.node_count).toBeGreaterThan(0)
    }
  })

  it('DEMO_TRACES includes at least one failed trace', () => {
    const failed = DEMO_TRACES.filter((t) => t.status === 'failed')
    expect(failed.length).toBeGreaterThan(0)
    expect(failed[0].final_score).toBeNull()
  })

  it('DEMO_STUDENT_COUNT is 4', () => {
    expect(DEMO_STUDENT_COUNT).toBe(4)
  })
})
