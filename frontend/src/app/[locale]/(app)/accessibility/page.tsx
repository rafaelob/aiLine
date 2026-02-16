'use client'

import { useTranslations } from 'next-intl'
import { PersonaToggle } from '@/components/accessibility/persona-toggle'
import { AccessibilityTwin } from '@/components/accessibility/accessibility-twin'
import { SimulateDisability } from '@/components/accessibility/simulate-disability'
import { ColorBlindFilters } from '@/components/accessibility/color-blind-filters'
import { CognitiveLoadMeter } from '@/components/cognitive/cognitive-load-meter'
import { PersonaHUD } from '@/components/accessibility/persona-hud'

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
  const t = useTranslations('accessibility')

  return (
    <main className="flex min-h-screen flex-col gap-10 p-6">
      {/* SVG filters for color blindness simulation (hidden, referenced by CSS) */}
      <ColorBlindFilters />

      {/* Page header */}
      <header>
        <h1 className="text-3xl font-bold text-[var(--color-text)]">
          {t('page_title')}
        </h1>
        <p className="mt-2 max-w-2xl text-[var(--color-muted)]">
          {t('page_description')}
        </p>
      </header>

      {/* Section 1: Persona Toggle */}
      <section aria-labelledby="persona-heading" className="flex flex-col gap-4">
        <h2
          id="persona-heading"
          className="text-xl font-semibold text-[var(--color-text)]"
        >
          {t('persona_heading')}
        </h2>
        <p className="text-sm text-[var(--color-muted)]">
          {t('persona_description')}
        </p>
        <PersonaToggle />
      </section>

      {/* Divider */}
      <hr className="border-[var(--color-border)]" />

      {/* Section 2: Accessibility Twin */}
      <section aria-labelledby="twin-heading" className="flex flex-col gap-4">
        <h2
          id="twin-heading"
          className="text-xl font-semibold text-[var(--color-text)]"
        >
          {t('twin_heading')}
        </h2>
        <p className="text-sm text-[var(--color-muted)]">
          {t('twin_description')}
        </p>
        <AccessibilityTwin
          originalContent={DEMO_ORIGINAL}
          adaptedContent={DEMO_ADAPTED}
          adaptationLabel="TEA"
        />
      </section>

      {/* Divider */}
      <hr className="border-[var(--color-border)]" />

      {/* Section 3: Simulate Disability */}
      <SimulateDisability />

      {/* Divider */}
      <hr className="border-[var(--color-border)]" />

      {/* Section 4: Cognitive Load Meter */}
      <section aria-labelledby="cognitive-heading" className="flex flex-col gap-4">
        <h2
          id="cognitive-heading"
          className="text-xl font-semibold text-[var(--color-text)]"
        >
          {t('cognitive_heading')}
        </h2>
        <p className="text-sm text-[var(--color-muted)]">
          {t('cognitive_description')}
        </p>
        <CognitiveLoadMeter
          factors={{ uiDensity: 35, readingLevel: 45, interactionCount: 6 }}
        />
      </section>

      {/* Persona HUD */}
      <PersonaHUD className="mt-4" />
    </main>
  )
}

/* --- Demo content for Accessibility Twin --- */

const DEMO_ORIGINAL = `Title: Fractions and Decimal Numbers
Grade: 5th Grade
Duration: 50 minutes

Objectives:
- Understand the relationship between fractions and decimals
- Convert fractions to decimals and vice versa
- Solve everyday problems involving fractions

Introduction (15 min):
Begin with a discussion about where we find fractions in daily life.
Examples: cake recipes, pizza slicing, time on a clock.

Development (25 min):
Hands-on activity with concrete materials.
Students divide paper circles into equal parts.
Conversion exercises in their notebooks.

Closing (10 min):
Group discussion about what they learned.
Homework: find 3 examples of fractions at home.`

const DEMO_ADAPTED = `Title: Fractions and Decimal Numbers
Grade: 5th Grade
Duration: 60 minutes (extended time)

Objectives:
- Understand the relationship between fractions and decimals
- Convert fractions to decimals and vice versa
- Solve everyday problems involving fractions
- Use visual representations as support

Introduction (20 min):
Begin with a discussion about where we find fractions in daily life.
Use a VISUAL SCHEDULE with pictograms for each lesson phase.
Limit to 3 concrete examples with images: pizza, clock, ruler.
Announce transitions with a 2-minute warning.

Development (25 min):
Hands-on activity with concrete materials.
Provide pre-organized materials in individual kits.
Students divide paper circles into equal parts.
Include step-by-step instructions with visual support.
Conversion exercises in notebooks with partial answer key.
Allow calculator use as support.

Closing (15 min):
Group discussion about what they learned.
Accept responses via drawing, gesture, or speech.
Visual summary of the lesson with 3 key points.
Homework: find 3 examples of fractions at home (with template).`
