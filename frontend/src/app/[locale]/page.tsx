import { DashboardContent } from '@/components/dashboard/dashboard-content'

/**
 * Dashboard page (root for each locale).
 * Server component that renders the dashboard layout.
 */
export default function DashboardPage() {
  return (
    <div className="max-w-5xl mx-auto">
      <DashboardContent />
    </div>
  )
}
