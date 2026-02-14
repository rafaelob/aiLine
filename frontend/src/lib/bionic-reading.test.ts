import { describe, it, expect } from 'vitest'
import { toBionicHtml } from './bionic-reading'

describe('toBionicHtml', () => {
  it('bolds the first half of a single word', () => {
    expect(toBionicHtml('hello')).toBe('<b>hel</b>lo')
  })

  it('handles a two-letter word', () => {
    expect(toBionicHtml('is')).toBe('<b>i</b>s')
  })

  it('handles a single-letter word', () => {
    expect(toBionicHtml('a')).toBe('<b>a</b>')
  })

  it('transforms multiple words', () => {
    const result = toBionicHtml('The quick fox')
    expect(result).toBe('<b>Th</b>e <b>qui</b>ck <b>fo</b>x')
  })

  it('returns empty string for empty input', () => {
    expect(toBionicHtml('')).toBe('')
  })

  it('preserves non-word characters', () => {
    const result = toBionicHtml('hello, world!')
    expect(result).toContain('<b>hel</b>lo')
    expect(result).toContain('<b>wor</b>ld')
    expect(result).toContain(',')
    expect(result).toContain('!')
  })

  it('handles numbers as words', () => {
    expect(toBionicHtml('42')).toBe('<b>4</b>2')
  })
})
