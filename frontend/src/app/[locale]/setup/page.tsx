import { SetupWizard } from '@/components/setup/setup-wizard'

interface PageProps {
  params: Promise<{ locale: string }>
}

/**
 * Setup wizard page -- first-run configuration for AiLine.
 * Renders at /{locale}/setup outside the (app) route group.
 */
export default async function SetupPage({ params }: PageProps) {
  const { locale } = await params
  return <SetupWizard locale={locale} />
}
