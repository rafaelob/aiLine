'use client'

import { LandingNav } from './landing-nav'
import { LandingHero } from './landing-hero'
import { LandingFeatures } from './landing-features'
import { LandingStats } from './landing-stats'
import { LandingFooter } from './landing-footer'

interface LandingPageProps {
  locale: string
  heroTitle: string
  heroSubtitle: string
  startDemo: string
  statsPersonas: string
  statsLanguages: string
  statsModels: string
  statsStandards: string
  statsLabel: string
  featuresTitle: string
  featurePipeline: string
  featurePipelineDesc: string
  featureAccessibility: string
  featureAccessibilityDesc: string
  featureTutor: string
  featureTutorDesc: string
  featureModels: string
  featureModelsDesc: string
  featureSign: string
  featureSignDesc: string
  featureCurriculum: string
  featureCurriculumDesc: string
  builtWith: string
}

/**
 * Landing page orchestrator — full-screen, no sidebar/topbar.
 * Renders hero, features, stats, and footer sections.
 */
export function LandingPage(props: LandingPageProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingNav locale={props.locale} startDemo={props.startDemo} />
      <main id="main-content">
        <LandingHero
          locale={props.locale}
          title={props.heroTitle}
          subtitle={props.heroSubtitle}
          cta={props.startDemo}
        />
        <LandingStats
          personas={props.statsPersonas}
          languages={props.statsLanguages}
          models={props.statsModels}
          standards={props.statsStandards}
          sectionLabel={props.statsLabel}
        />
        <LandingFeatures
          title={props.featuresTitle}
          features={[
            { title: props.featurePipeline, desc: props.featurePipelineDesc, icon: 'pipeline' },
            { title: props.featureAccessibility, desc: props.featureAccessibilityDesc, icon: 'a11y' },
            { title: props.featureTutor, desc: props.featureTutorDesc, icon: 'tutor' },
            { title: props.featureModels, desc: props.featureModelsDesc, icon: 'models' },
            { title: props.featureSign, desc: props.featureSignDesc, icon: 'sign' },
            { title: props.featureCurriculum, desc: props.featureCurriculumDesc, icon: 'curriculum' },
          ]}
        />
      </main>
      <LandingFooter builtWith={props.builtWith} />
    </div>
  )
}
