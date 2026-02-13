/**
 * Static data for accessibility personas, simulation modes, and export variants.
 * Centralized here to avoid duplication across components.
 *
 * Labels and descriptions use i18n translation keys (resolved by consuming
 * components via useTranslations). The `labelKey` and `descKey` fields
 * reference keys in the messages JSON files under the corresponding namespace.
 */

import type {
  Persona,
  PersonaId,
  SimulationInfo,
  SimulationMode,
  ExportVariantInfo,
} from '@/types/accessibility'

export const PERSONAS: Record<PersonaId, Persona> = {
  standard: {
    id: 'standard',
    label: 'standard',
    icon: '\u{1F464}',
    theme: 'standard',
    description: 'standard_desc',
  },
  high_contrast: {
    id: 'high_contrast',
    label: 'high_contrast',
    icon: '\u{1F532}',
    theme: 'high_contrast',
    description: 'high_contrast_desc',
  },
  tea: {
    id: 'tea',
    label: 'tea',
    icon: '\u{1F9E9}',
    theme: 'tea',
    description: 'tea_desc',
  },
  tdah: {
    id: 'tdah',
    label: 'tdah',
    icon: '\u26A1',
    theme: 'tdah',
    description: 'tdah_desc',
  },
  dyslexia: {
    id: 'dyslexia',
    label: 'dyslexia',
    icon: '\u{1F4D6}',
    theme: 'dyslexia',
    description: 'dyslexia_desc',
  },
  low_vision: {
    id: 'low_vision',
    label: 'low_vision',
    icon: '\u{1F50D}',
    theme: 'low_vision',
    description: 'low_vision_desc',
  },
  hearing: {
    id: 'hearing',
    label: 'hearing',
    icon: '\u{1F442}',
    theme: 'hearing',
    description: 'hearing_desc',
  },
  motor: {
    id: 'motor',
    label: 'motor',
    icon: '\u{1F590}\uFE0F',
    theme: 'motor',
    description: 'motor_desc',
  },
  screen_reader: {
    id: 'screen_reader',
    label: 'screen_reader',
    icon: '\u{1F50A}',
    theme: 'screen_reader',
    description: 'screen_reader_desc',
  },
}

export const PERSONA_LIST: Persona[] = Object.values(PERSONAS)

export const SIMULATIONS: SimulationInfo[] = [
  {
    id: 'protanopia',
    label: 'protanopia',
    description: 'protanopia_desc',
    category: 'color_blindness',
  },
  {
    id: 'deuteranopia',
    label: 'deuteranopia',
    description: 'deuteranopia_desc',
    category: 'color_blindness',
  },
  {
    id: 'tritanopia',
    label: 'tritanopia',
    description: 'tritanopia_desc',
    category: 'color_blindness',
  },
  {
    id: 'low_vision',
    label: 'low_vision',
    description: 'low_vision_desc',
    category: 'vision',
  },
  {
    id: 'tunnel_vision',
    label: 'tunnel_vision',
    description: 'tunnel_vision_desc',
    category: 'vision',
  },
  {
    id: 'dyslexia',
    label: 'dyslexia',
    description: 'dyslexia_desc',
    category: 'cognitive',
  },
  {
    id: 'motor_difficulty',
    label: 'motor_difficulty',
    description: 'motor_difficulty_desc',
    category: 'motor',
  },
]

export const SIMULATION_CATEGORIES = [
  { id: 'color_blindness' as const, label: 'color_blindness' },
  { id: 'vision' as const, label: 'vision' },
  { id: 'cognitive' as const, label: 'cognitive' },
  { id: 'motor' as const, label: 'motor' },
]

export const EXPORT_VARIANTS: ExportVariantInfo[] = [
  {
    id: 'standard',
    label: 'standard',
    description: 'standard_desc',
  },
  {
    id: 'low_distraction',
    label: 'low_distraction',
    description: 'low_distraction_desc',
  },
  {
    id: 'large_print',
    label: 'large_print',
    description: 'large_print_desc',
  },
  {
    id: 'high_contrast',
    label: 'high_contrast',
    description: 'high_contrast_desc',
  },
  {
    id: 'dyslexia_friendly',
    label: 'dyslexia_friendly',
    description: 'dyslexia_friendly_desc',
  },
  {
    id: 'screen_reader',
    label: 'screen_reader',
    description: 'screen_reader_desc',
  },
  {
    id: 'visual_schedule',
    label: 'visual_schedule',
    description: 'visual_schedule_desc',
  },
]

/** Map simulation mode to its CSS filter or class application. */
export function getSimulationCSS(mode: SimulationMode): string {
  switch (mode) {
    case 'protanopia':
      return 'url(#cb-protanopia)'
    case 'deuteranopia':
      return 'url(#cb-deuteranopia)'
    case 'tritanopia':
      return 'url(#cb-tritanopia)'
    case 'low_vision':
      return 'blur(2px) contrast(0.6) brightness(0.8)'
    default:
      return ''
  }
}
