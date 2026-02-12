/**
 * Thin wrapper around the dynamic mermaid import.
 * Extracted for testability (vi.mock can intercept this module).
 */
export async function loadMermaid() {
  const { default: mermaid } = await import('mermaid')
  return mermaid
}
