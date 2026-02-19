import { getTranslations } from 'next-intl/server'
import { LandingPage } from '@/components/landing/landing-page'

interface PageProps {
  params: Promise<{ locale: string }>
}

/**
 * Public landing page -- no sidebar, no topbar.
 * Renders at /{locale}/ outside the (app) route group.
 */
export default async function HomePage({ params }: PageProps) {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'landing' })

  return (
    <LandingPage
      locale={locale}
      startDemo={t('start_demo')}
      hero={{
        title: t('hero_title'),
        subtitle: t('hero_subtitle'),
        fullName: t('hero_full_name'),
        badgeOpenSource: t('badge_open_source'),
        badgeBuiltWith: t('badge_built_with'),
      }}
      stats={{
        personas: t('stats_personas'),
        languages: t('stats_languages'),
        models: t('stats_models'),
        standards: t('stats_standards'),
        label: t('stats_label'),
      }}
      features={{
        title: t('features_title'),
        items: [
          { title: t('feature_pipeline'), desc: t('feature_pipeline_desc'), icon: 'pipeline' },
          { title: t('feature_accessibility'), desc: t('feature_accessibility_desc'), icon: 'a11y' },
          { title: t('feature_tutor'), desc: t('feature_tutor_desc'), icon: 'tutor' },
          { title: t('feature_models'), desc: t('feature_models_desc'), icon: 'models' },
          { title: t('feature_sign'), desc: t('feature_sign_desc'), icon: 'sign' },
          { title: t('feature_curriculum'), desc: t('feature_curriculum_desc'), icon: 'curriculum' },
        ],
      }}
      howItWorks={{
        title: t('how_it_works_title'),
        steps: [
          { title: t('how_step_1_title'), description: t('how_step_1_desc') },
          { title: t('how_step_2_title'), description: t('how_step_2_desc') },
          { title: t('how_step_3_title'), description: t('how_step_3_desc') },
          { title: t('how_step_4_title'), description: t('how_step_4_desc') },
        ],
      }}
      demo={{
        title: t('demo_title'),
        subtitle: t('demo_subtitle'),
        enterAs: t('demo_enter_as'),
        teacherLabel: t('demo_role_teacher'),
        studentLabel: t('demo_role_student'),
        parentLabel: t('demo_role_parent'),
        profiles: {
          teacher: {
            name: t('demo_teacher_name'),
            detail: t('demo_teacher_detail'),
            description: t('demo_teacher_desc'),
          },
          students: {
            alex: { name: t('demo_alex_name'), condition: t('demo_alex_condition'), description: t('demo_alex_desc') },
            maya: { name: t('demo_maya_name'), condition: t('demo_maya_condition'), description: t('demo_maya_desc') },
            lucas: { name: t('demo_lucas_name'), condition: t('demo_lucas_condition'), description: t('demo_lucas_desc') },
            sofia: { name: t('demo_sofia_name'), condition: t('demo_sofia_condition'), description: t('demo_sofia_desc') },
          },
          parent: { name: t('demo_parent_name'), description: t('demo_parent_desc') },
        },
      }}
      footer={{
        builtWith: t('built_with'),
        openSource: t('footer_open_source'),
        createdWith: t('footer_created_with'),
        hackathon: t('footer_hackathon'),
      }}
    />
  )
}
