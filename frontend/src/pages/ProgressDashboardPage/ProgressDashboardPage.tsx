import {
  WorkerStatusCard,
  workerFromStatus,
} from '@/components/progress/WorkerStatusCard'
import { CurrentJobCard } from '@/components/progress/CurrentJobCard'
import { VcProgressWidget } from '@/components/progress/VcProgressWidget'
import { RecentEventsList } from '@/components/progress/RecentEventsList'
import { Skeleton } from '@/components/ui/skeleton'
import { useQueueJobsMonitor } from '@/hooks/useQueueMonitor'
import { useWorkerStatusMonitor } from '@/hooks/useQueueMonitor'
import { useVcProgress } from '@/hooks/useVcProgress'
import { useRecentEventsMonitor } from '@/hooks/useVcProgressEvents'

export function ProgressDashboardPage() {
  const workerQuery = useWorkerStatusMonitor()
  const jobsQuery = useQueueJobsMonitor()
  const vcProgressQuery = useVcProgress()
  const eventsQuery = useRecentEventsMonitor(20)

  const workers = workerQuery.data
    ? [workerFromStatus(workerQuery.data)]
    : []

  const currentJob = jobsQuery.data?.running[0]

  return (
    <div className="space-y-6" data-testid="progress-dashboard-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Progress Dashboard</h1>
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Long-running VC visibility
        </p>
      </div>

      {workerQuery.isError ? (
        <p className="text-sm text-red-400" data-testid="worker-load-error">
          Unable to load worker status
        </p>
      ) : workerQuery.isLoading ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <WorkerStatusCard workers={workers} />
      )}

      {jobsQuery.isLoading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <CurrentJobCard job={currentJob} />
      )}

      <VcProgressWidget
        progress={vcProgressQuery.data ?? null}
        isLoading={vcProgressQuery.isLoading}
        isError={vcProgressQuery.isError}
      />

      <div>
        <h2 className="mb-3 text-lg font-semibold">Recent Events</h2>
        {eventsQuery.isError ? (
          <RecentEventsList events={undefined} error />
        ) : eventsQuery.isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <RecentEventsList events={eventsQuery.data} />
        )}
      </div>
    </div>
  )
}
