'use client'

import { PersonaToggle } from '@/components/accessibility/persona-toggle'
import { AccessibilityTwin } from '@/components/accessibility/accessibility-twin'
import { SimulateDisability } from '@/components/accessibility/simulate-disability'
import { ColorBlindFilters } from '@/components/accessibility/color-blind-filters'

/**
 * Accessibility page combining:
 * 1. Persona toggle at top for switching accessibility themes.
 * 2. Accessibility Twin viewer comparing original vs adapted content.
 * 3. Simulate Disability (Empathy Bridge) section for educators.
 *
 * All sections follow WCAG AAA guidelines with proper keyboard navigation,
 * ARIA attributes, and semantic HTML structure.
 */
export default function AccessibilityPage() {
  return (
    <main className="flex min-h-screen flex-col gap-10 p-6">
      {/* SVG filters for color blindness simulation (hidden, referenced by CSS) */}
      <ColorBlindFilters />

      {/* Page header */}
      <header>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Acessibilidade
        </h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">
          Personalize a experiência para diferentes necessidades de aprendizagem.
          Alterne entre personas, compare versões adaptadas e simule
          condições para entender a perspectiva dos seus alunos.
        </p>
      </header>

      {/* Section 1: Persona Toggle */}
      <section aria-labelledby="persona-heading" className="flex flex-col gap-4">
        <h2
          id="persona-heading"
          className="text-xl font-semibold text-gray-900 dark:text-white"
        >
          Persona de Acessibilidade
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Selecione uma persona para ajustar o tema visual da plataforma.
        </p>
        <PersonaToggle />
      </section>

      {/* Divider */}
      <hr className="border-gray-200 dark:border-gray-700" />

      {/* Section 2: Accessibility Twin */}
      <section aria-labelledby="twin-heading" className="flex flex-col gap-4">
        <h2
          id="twin-heading"
          className="text-xl font-semibold text-gray-900 dark:text-white"
        >
          Comparação de Versões
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Compare a versão original do plano com a versão adaptada.
          Diferenças são destacadas com cores e indicadores visuais.
        </p>
        <AccessibilityTwin
          originalContent={DEMO_ORIGINAL}
          adaptedContent={DEMO_ADAPTED}
          adaptationLabel="TEA"
        />
      </section>

      {/* Divider */}
      <hr className="border-gray-200 dark:border-gray-700" />

      {/* Section 3: Simulate Disability */}
      <SimulateDisability />
    </main>
  )
}

/* --- Demo content for Accessibility Twin --- */

const DEMO_ORIGINAL = `Título: Frações e Números Decimais
Série: 5º ano do Ensino Fundamental
Duração: 50 minutos

Objetivos:
- Compreender a relação entre frações e decimais
- Converter frações em decimais e vice-versa
- Resolver problemas do cotidiano envolvendo frações

Introdução (15 min):
Começar com uma discussão sobre onde encontramos frações no dia a dia.
Exemplos: receitas de bolo, divisão de pizza, horários.

Desenvolvimento (25 min):
Atividade prática com material concreto.
Alunos dividem círculos de papel em partes iguais.
Exercícios de conversão no caderno.

Fechamento (10 min):
Roda de conversa sobre o que aprenderam.
Tarefa de casa: encontrar 3 exemplos de frações em casa.`

const DEMO_ADAPTED = `Título: Frações e Números Decimais
Série: 5º ano do Ensino Fundamental
Duração: 60 minutos (tempo estendido)

Objetivos:
- Compreender a relação entre frações e decimais
- Converter frações em decimais e vice-versa
- Resolver problemas do cotidiano envolvendo frações
- Usar representações visuais como suporte

Introdução (20 min):
Começar com uma discussão sobre onde encontramos frações no dia a dia.
Usar AGENDA VISUAL com pictogramas para cada etapa da aula.
Limitar a 3 exemplos concretos com imagens: pizza, relógio, régua.
Antecipar transições com aviso de 2 minutos.

Desenvolvimento (25 min):
Atividade prática com material concreto.
Fornecer material pré-organizado em kits individuais.
Alunos dividem círculos de papel em partes iguais.
Incluir instruções passo-a-passo com suporte visual.
Exercícios de conversão no caderno com gabarito parcial.
Permitir uso de calculadora como apoio.

Fechamento (15 min):
Roda de conversa sobre o que aprenderam.
Aceitar resposta por desenho, gesto ou fala.
Resumo visual da aula com 3 pontos principais.
Tarefa de casa: encontrar 3 exemplos de frações em casa (com modelo).`
