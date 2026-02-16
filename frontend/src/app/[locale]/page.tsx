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
      heroFullName={t('hero_full_name')}
      startDemo={t('start_demo')}
      badgeOpenSource={t('badge_open_source')}
      badgeBuiltWith={t('badge_built_with')}
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
      howItWorksTitle={t('how_it_works_title')}
      howItWorksSteps={[
        { title: t('how_step_1_title'), description: t('how_step_1_desc') },
        { title: t('how_step_2_title'), description: t('how_step_2_desc') },
        { title: t('how_step_3_title'), description: t('how_step_3_desc') },
        { title: t('how_step_4_title'), description: t('how_step_4_desc') },
      ]}
      demoTitle={t('demo_title')}
      demoSubtitle={t('demo_subtitle')}
      demoEnterAs={t('demo_enter_as')}
      demoTeacherLabel={t('demo_role_teacher')}
      demoStudentLabel={t('demo_role_student')}
      demoParentLabel={t('demo_role_parent')}
      demoProfiles={{
        teacher: {
          name: t('demo_teacher_name'),
          detail: t('demo_teacher_detail'),
          description: t('demo_teacher_desc'),
        },
        students: {
          alex: {
            name: t('demo_alex_name'),
            condition: t('demo_alex_condition'),
            description: t('demo_alex_desc'),
          },
          maya: {
            name: t('demo_maya_name'),
            condition: t('demo_maya_condition'),
            description: t('demo_maya_desc'),
          },
          lucas: {
            name: t('demo_lucas_name'),
            condition: t('demo_lucas_condition'),
            description: t('demo_lucas_desc'),
          },
          sofia: {
            name: t('demo_sofia_name'),
            condition: t('demo_sofia_condition'),
            description: t('demo_sofia_desc'),
          },
        },
        parent: {
          name: t('demo_parent_name'),
          description: t('demo_parent_desc'),
        },
      }}
      footerOpenSource={t('footer_open_source')}
      footerCreatedWith={t('footer_created_with')}
      footerHackathon={t('footer_hackathon')}
    />
  )
}
