import { describe, it, expect } from 'vitest'
import { containerVariants, itemVariants } from './motion-variants'

describe('motion-variants', () => {
  it('containerVariants has hidden and visible states', () => {
    expect(containerVariants).toHaveProperty('hidden')
    expect(containerVariants).toHaveProperty('visible')
  })

  it('containerVariants.visible has staggerChildren transition', () => {
    const visible = containerVariants.visible as { transition?: { staggerChildren?: number } }
    expect(visible.transition?.staggerChildren).toBeGreaterThan(0)
  })

  it('itemVariants has hidden and visible states', () => {
    expect(itemVariants).toHaveProperty('hidden')
    expect(itemVariants).toHaveProperty('visible')
  })

  it('itemVariants.hidden sets opacity to 0', () => {
    const hidden = itemVariants.hidden as { opacity?: number }
    expect(hidden.opacity).toBe(0)
  })

  it('itemVariants.visible sets opacity to 1', () => {
    const visible = itemVariants.visible as { opacity?: number }
    expect(visible.opacity).toBe(1)
  })
})
