import { describe, it, expect } from 'vitest'
import {
  PERSONAS,
  PERSONA_LIST,
  SIMULATIONS,
  SIMULATION_CATEGORIES,
  EXPORT_VARIANTS,
  getSimulationCSS,
} from './accessibility-data'

describe('PERSONAS', () => {
  it('contains all 9 persona IDs', () => {
    const ids = Object.keys(PERSONAS)
    expect(ids).toHaveLength(9)
    expect(ids).toContain('standard')
    expect(ids).toContain('high_contrast')
    expect(ids).toContain('tea')
    expect(ids).toContain('tdah')
    expect(ids).toContain('dyslexia')
    expect(ids).toContain('low_vision')
    expect(ids).toContain('hearing')
    expect(ids).toContain('motor')
    expect(ids).toContain('screen_reader')
  })

  it('each persona has required fields', () => {
    for (const persona of Object.values(PERSONAS)) {
      expect(persona.id).toBeTruthy()
      expect(persona.label).toBeTruthy()
      expect(persona.icon).toBeTruthy()
      expect(persona.theme).toBeTruthy()
      expect(persona.description).toBeTruthy()
    }
  })
})

describe('PERSONA_LIST', () => {
  it('is an array derived from PERSONAS', () => {
    expect(Array.isArray(PERSONA_LIST)).toBe(true)
    expect(PERSONA_LIST).toHaveLength(9)
  })

  it('contains the same items as PERSONAS values', () => {
    const ids = PERSONA_LIST.map((p) => p.id)
    for (const key of Object.keys(PERSONAS)) {
      expect(ids).toContain(key)
    }
  })
})

describe('SIMULATIONS', () => {
  it('has 7 simulation modes', () => {
    expect(SIMULATIONS).toHaveLength(7)
  })

  it('each simulation has required fields', () => {
    for (const sim of SIMULATIONS) {
      expect(sim.id).toBeTruthy()
      expect(sim.label).toBeTruthy()
      expect(sim.description).toBeTruthy()
      expect(sim.category).toBeTruthy()
    }
  })

  it('covers all categories', () => {
    const categories = new Set(SIMULATIONS.map((s) => s.category))
    expect(categories).toContain('color_blindness')
    expect(categories).toContain('vision')
    expect(categories).toContain('cognitive')
    expect(categories).toContain('motor')
  })
})

describe('SIMULATION_CATEGORIES', () => {
  it('has 4 categories', () => {
    expect(SIMULATION_CATEGORIES).toHaveLength(4)
  })

  it('each has id and label', () => {
    for (const cat of SIMULATION_CATEGORIES) {
      expect(cat.id).toBeTruthy()
      expect(cat.label).toBeTruthy()
    }
  })
})

describe('EXPORT_VARIANTS', () => {
  it('has 7 export variants', () => {
    expect(EXPORT_VARIANTS).toHaveLength(7)
  })

  it('each variant has required fields', () => {
    for (const variant of EXPORT_VARIANTS) {
      expect(variant.id).toBeTruthy()
      expect(variant.label).toBeTruthy()
      expect(variant.description).toBeTruthy()
    }
  })

  it('includes standard variant', () => {
    const ids = EXPORT_VARIANTS.map((v) => v.id)
    expect(ids).toContain('standard')
  })
})

describe('getSimulationCSS', () => {
  it('returns SVG filter URL for protanopia', () => {
    expect(getSimulationCSS('protanopia')).toBe('url(#cb-protanopia)')
  })

  it('returns SVG filter URL for deuteranopia', () => {
    expect(getSimulationCSS('deuteranopia')).toBe('url(#cb-deuteranopia)')
  })

  it('returns SVG filter URL for tritanopia', () => {
    expect(getSimulationCSS('tritanopia')).toBe('url(#cb-tritanopia)')
  })

  it('returns blur+contrast+brightness for low_vision', () => {
    expect(getSimulationCSS('low_vision')).toBe(
      'blur(2px) contrast(0.6) brightness(0.8)'
    )
  })

  it('returns empty string for dyslexia (handled separately)', () => {
    expect(getSimulationCSS('dyslexia')).toBe('')
  })

  it('returns empty string for tunnel_vision (handled via overlay)', () => {
    expect(getSimulationCSS('tunnel_vision')).toBe('')
  })

  it('returns empty string for motor_difficulty', () => {
    expect(getSimulationCSS('motor_difficulty')).toBe('')
  })
})
