import { getTranslations } from 'next-intl/server'
import { LandingPage } from '@/components/landing/landing-page'

interface PageProps {
  params: Promise<{ locale: string }>
}

/**
 * Public landing page — no sidebar, no topbar.
 * Renders at /{locale}/ outside the (app) route group.
 */
export default async function HomePage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'landing' })

  return (
    <LandingPage
      locale={locale}
      heroTitle={t('hero_title')}
      heroSubtitle={t('hero_subtitle')}
      startDemo={t('start_demo')}
      statsPersonas={t('stats_personas')}
      statsLanguages={t('stats_languages')}
      statsModels={t('stats_models')}
      statsStandards={t('stats_standards')}
      statsLabel={t('stats_label')}
      featuresTitle={t('features_title')}
      featurePipeline={t('feature_pipeline')}
      featurePipelineDesc={t('feature_pipeline_desc')}
      featureAccessibility={t('feature_accessibility')}
      featureAccessibilityDesc={t('feature_accessibility_desc')}
      featureTutor={t('feature_tutor')}
      featureTutorDesc={t('feature_tutor_desc')}
      featureModels={t('feature_models')}
      featureModelsDesc={t('feature_models_desc')}
      featureSign={t('feature_sign')}
      featureSignDesc={t('feature_sign_desc')}
      featureCurriculum={t('feature_curriculum')}
      featureCurriculumDesc={t('feature_curriculum_desc')}
      builtWith={t('built_with')}
    />
  )
}
