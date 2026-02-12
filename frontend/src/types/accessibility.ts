/**
 * Accessibility types for persona switching, disability simulation,
 * and the Accessibility Twin tabbed view (ADR-044).
 */

/** The 9 accessibility personas available in AiLine. */
export type PersonaId =
  | 'standard'
  | 'high_contrast'
  | 'tea'
  | 'tdah'
  | 'dyslexia'
  | 'low_vision'
  | 'hearing'
  | 'motor'
  | 'screen_reader'

export interface Persona {
  id: PersonaId
  label: string
  icon: string
  /** CSS data-theme value applied to document.body */
  theme: string
  description: string
}

/** Export variant identifiers matching backend export variants. */
export type ExportVariant =
  | 'standard'
  | 'low_distraction'
  | 'large_print'
  | 'high_contrast'
  | 'dyslexia_friendly'
  | 'screen_reader'
  | 'visual_schedule'

export interface ExportVariantInfo {
  id: ExportVariant
  label: string
  description: string
}

/** Disability simulation modes for the Empathy Bridge. */
export type SimulationMode =
  | 'protanopia'
  | 'deuteranopia'
  | 'tritanopia'
  | 'low_vision'
  | 'dyslexia'
  | 'tunnel_vision'
  | 'motor_difficulty'

export interface SimulationInfo {
  id: SimulationMode
  label: string
  description: string
  category: 'color_blindness' | 'vision' | 'cognitive' | 'motor'
}

/** Diff change for Accessibility Twin view. */
export interface DiffChange {
  type: 'addition' | 'removal' | 'unchanged'
  text: string
}

/** Tab value for the Accessibility Twin. */
export type TwinTab = 'original' | 'adapted'
