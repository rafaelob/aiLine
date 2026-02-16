'use client'

import { LandingNav } from './landing-nav'
import { LandingHero } from './landing-hero'
import { LandingFeatures } from './landing-features'
import { LandingStats } from './landing-stats'
import { LandingHowItWorks } from './landing-how-it-works'
import { LandingDemoLogin } from './landing-demo-login'
import { LandingFooter } from './landing-footer'

interface LandingPageProps {
  locale: string
  heroTitle: string
  heroSubtitle: string
  heroFullName: string
  startDemo: string
  badgeOpenSource: string
  badgeBuiltWith: string
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
  howItWorksTitle: string
  howItWorksSteps: { title: string; description: string }[]
  demoTitle: string
  demoSubtitle: string
  demoEnterAs: string
  demoTeacherLabel: string
  demoStudentLabel: string
  demoParentLabel: string
  demoProfiles: {
    teacher: { name: string; detail: string; description: string }
    students: {
      alex: { name: string; condition: string; description: string }
      maya: { name: string; condition: string; description: string }
      lucas: { name: string; condition: string; description: string }
      sofia: { name: string; condition: string; description: string }
    }
    parent: { name: string; description: string }
  }
  footerOpenSource: string
  footerCreatedWith: string
  footerHackathon: string
}

/**
 * Landing page orchestrator — full-screen, no sidebar/topbar.
 * Renders hero, stats, how-it-works, features, demo login, and footer sections.
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
          fullName={props.heroFullName}
          badgeOpenSource={props.badgeOpenSource}
          badgeBuiltWith={props.badgeBuiltWith}
        />
        <LandingStats
          personas={props.statsPersonas}
          languages={props.statsLanguages}
          models={props.statsModels}
          standards={props.statsStandards}
          sectionLabel={props.statsLabel}
        />
        <LandingHowItWorks
          title={props.howItWorksTitle}
          steps={props.howItWorksSteps}
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
        <LandingDemoLogin
          locale={props.locale}
          title={props.demoTitle}
          subtitle={props.demoSubtitle}
          enterAs={props.demoEnterAs}
          teacherLabel={props.demoTeacherLabel}
          studentLabel={props.demoStudentLabel}
          parentLabel={props.demoParentLabel}
          profiles={props.demoProfiles}
        />
      </main>
      <LandingFooter
        builtWith={props.builtWith}
        openSource={props.footerOpenSource}
        createdWith={props.footerCreatedWith}
        hackathon={props.footerHackathon}
      />
    </div>
  )
}
