/**
 * Static data for accessibility personas, simulation modes, and export variants.
 * Centralized here to avoid duplication across components.
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
    label: 'Padrão',
    icon: '👤',
    theme: 'standard',
    description: 'Visualização padrão sem adaptações específicas',
  },
  high_contrast: {
    id: 'high_contrast',
    label: 'Alto Contraste',
    icon: '🔲',
    theme: 'high_contrast',
    description: 'Cores de alto contraste para melhor legibilidade',
  },
  tea: {
    id: 'tea',
    label: 'TEA',
    icon: '🧩',
    theme: 'tea',
    description: 'Otimizado para Transtorno do Espectro Autista',
  },
  tdah: {
    id: 'tdah',
    label: 'TDAH',
    icon: '⚡',
    theme: 'tdah',
    description: 'Otimizado para Transtorno de Déficit de Atenção',
  },
  dyslexia: {
    id: 'dyslexia',
    label: 'Dislexia',
    icon: '📖',
    theme: 'dyslexia',
    description: 'Fontes e espaçamentos otimizados para dislexia',
  },
  low_vision: {
    id: 'low_vision',
    label: 'Baixa Visão',
    icon: '🔍',
    theme: 'low_vision',
    description: 'Texto ampliado e contraste reforçado',
  },
  hearing: {
    id: 'hearing',
    label: 'Auditivo',
    icon: '👂',
    theme: 'hearing',
    description: 'Ênfase em conteúdo visual e legendas',
  },
  motor: {
    id: 'motor',
    label: 'Motor',
    icon: '🖐️',
    theme: 'motor',
    description: 'Áreas de toque ampliadas e navegação simplificada',
  },
  screen_reader: {
    id: 'screen_reader',
    label: 'Leitor de Tela',
    icon: '🔊',
    theme: 'screen_reader',
    description: 'Otimizado para tecnologias assistivas',
  },
}

export const PERSONA_LIST: Persona[] = Object.values(PERSONAS)

export const SIMULATIONS: SimulationInfo[] = [
  {
    id: 'protanopia',
    label: 'Protanopia',
    description:
      'Dificuldade em distinguir vermelho do verde. Afeta ~1% dos homens. Vermelho aparece como verde-amarelado.',
    category: 'color_blindness',
  },
  {
    id: 'deuteranopia',
    label: 'Deuteranopia',
    description:
      'Forma mais comum de daltonismo. Afeta ~6% dos homens. Verde é confundido com vermelho.',
    category: 'color_blindness',
  },
  {
    id: 'tritanopia',
    label: 'Tritanopia',
    description:
      'Dificuldade em distinguir azul do amarelo. Rara (~0.01%). Azul aparece como verde.',
    category: 'color_blindness',
  },
  {
    id: 'low_vision',
    label: 'Baixa Visão',
    description:
      'Simula visão embaçada e contraste reduzido, como experimentado por pessoas com degeneração macular.',
    category: 'vision',
  },
  {
    id: 'tunnel_vision',
    label: 'Visão Tubular',
    description:
      'Campo visual restrito ao centro, como experimentado por pessoas com glaucoma ou retinite pigmentosa.',
    category: 'vision',
  },
  {
    id: 'dyslexia',
    label: 'Dislexia',
    description:
      'Letras embaralhadas simulam a dificuldade de leitura. Afeta ~5-10% da população.',
    category: 'cognitive',
  },
  {
    id: 'motor_difficulty',
    label: 'Dificuldade Motora',
    description:
      'Atraso no cursor simula tremor e dificuldade de controle motor fino.',
    category: 'motor',
  },
]

export const SIMULATION_CATEGORIES = [
  { id: 'color_blindness' as const, label: 'Daltonismo' },
  { id: 'vision' as const, label: 'Visão' },
  { id: 'cognitive' as const, label: 'Cognitivo' },
  { id: 'motor' as const, label: 'Motor' },
]

export const EXPORT_VARIANTS: ExportVariantInfo[] = [
  {
    id: 'standard',
    label: 'Padrão',
    description: 'Formato padrão do plano de aula',
  },
  {
    id: 'low_distraction',
    label: 'Baixa Distração',
    description: 'Layout simplificado com menos elementos visuais',
  },
  {
    id: 'large_print',
    label: 'Impressão Grande',
    description: 'Texto ampliado para baixa visão',
  },
  {
    id: 'high_contrast',
    label: 'Alto Contraste',
    description: 'Cores de alto contraste para melhor legibilidade',
  },
  {
    id: 'dyslexia_friendly',
    label: 'Amigável à Dislexia',
    description: 'Fontes e espaçamentos otimizados para dislexia',
  },
  {
    id: 'screen_reader',
    label: 'Leitor de Tela',
    description: 'Estrutura semântica otimizada para leitores de tela',
  },
  {
    id: 'visual_schedule',
    label: 'Agenda Visual',
    description: 'Cartões visuais para TEA/TDAH',
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
