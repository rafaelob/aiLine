'use client'

import { useTranslations } from 'next-intl'
import { LandingNav } from './landing-nav'
import { LandingHero } from './landing-hero'
import { LandingFeatures } from './landing-features'
import { LandingStats } from './landing-stats'
import { LandingHowItWorks } from './landing-how-it-works'
import { LandingDemoLogin } from './landing-demo-login'
import { LandingFooter } from './landing-footer'

/* ------------------------------------------------------------------ */
/*  Grouped props (was 40+ flat props)                                 */
/* ------------------------------------------------------------------ */

interface HeroProps {
  title: string
  subtitle: string
  fullName: string
  badgeOpenSource: string
  badgeBuiltWith: string
}

interface StatsProps {
  personas: string
  languages: string
  models: string
  standards: string
  label: string
}

interface FeatureItem {
  title: string
  desc: string
  icon: 'pipeline' | 'a11y' | 'tutor' | 'models' | 'sign' | 'curriculum'
}

interface HowItWorksStep {
  title: string
  description: string
}

interface DemoProfileSet {
  teacher: { name: string; detail: string; description: string }
  students: {
    alex: { name: string; condition: string; description: string }
    maya: { name: string; condition: string; description: string }
    lucas: { name: string; condition: string; description: string }
    sofia: { name: string; condition: string; description: string }
  }
  parent: { name: string; description: string }
}

interface DemoProps {
  title: string
  subtitle: string
  enterAs: string
  teacherLabel: string
  studentLabel: string
  parentLabel: string
  profiles: DemoProfileSet
}

interface FooterProps {
  builtWith: string
  openSource: string
  createdWith: string
  hackathon: string
}

export interface LandingPageProps {
  locale: string
  startDemo: string
  hero: HeroProps
  stats: StatsProps
  features: { title: string; items: FeatureItem[] }
  howItWorks: { title: string; steps: HowItWorksStep[] }
  demo: DemoProps
  footer: FooterProps
}

/**
 * Landing page orchestrator -- full-screen, no sidebar/topbar.
 * Renders hero, stats, how-it-works, features, demo login, and footer sections.
 */
export function LandingPage(props: LandingPageProps) {
  const tCommon = useTranslations('common')

  return (
    <div className="min-h-screen flex flex-col">
      <a href="#main-content" className="skip-link">
        {tCommon('skipToContent')}
      </a>
      <header>
        <LandingNav locale={props.locale} startDemo={props.startDemo} />
      </header>
      <main id="main-content">
        <LandingHero
          title={props.hero.title}
          subtitle={props.hero.subtitle}
          cta={props.startDemo}
          fullName={props.hero.fullName}
          badgeOpenSource={props.hero.badgeOpenSource}
          badgeBuiltWith={props.hero.badgeBuiltWith}
        />
        <LandingStats
          personas={props.stats.personas}
          languages={props.stats.languages}
          models={props.stats.models}
          standards={props.stats.standards}
          sectionLabel={props.stats.label}
        />
        <LandingHowItWorks
          title={props.howItWorks.title}
          steps={props.howItWorks.steps}
        />
        <LandingFeatures
          title={props.features.title}
          features={props.features.items}
        />
        <LandingDemoLogin
          locale={props.locale}
          title={props.demo.title}
          subtitle={props.demo.subtitle}
          enterAs={props.demo.enterAs}
          teacherLabel={props.demo.teacherLabel}
          studentLabel={props.demo.studentLabel}
          parentLabel={props.demo.parentLabel}
          profiles={props.demo.profiles}
        />
      </main>
      <LandingFooter
        builtWith={props.footer.builtWith}
        openSource={props.footer.openSource}
        createdWith={props.footer.createdWith}
        hackathon={props.footer.hackathon}
      />
    </div>
  )
}
