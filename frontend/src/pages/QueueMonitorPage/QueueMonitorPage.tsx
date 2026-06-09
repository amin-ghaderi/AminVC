import { useMemo, useState } from 'react'

import {
  CompletedJobsSection,
  FailedJobsSection,
  QueuedJobsSection,
  RunningJobsSection,
} from '@/components/queue-monitor/JobSections'
import { QueueFilters } from '@/components/queue-monitor/QueueFilters'
import { QueueSearch } from '@/components/queue-monitor/QueueSearch'
import { QueueSummaryCards } from '@/components/queue-monitor/QueueSummaryCards'
import { useToast } from '@/components/shared/ToastProvider'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError } from '@/api/client'
import { filterQueueJobs } from '@/lib/queueFilters'
import {
  useCancelQueueJob,
  useQueueJobsMonitor,
  useQueueSnapshotMonitor,
  useWorkerStatusMonitor,
} from '@/hooks/useQueueMonitor'
import { WorkerStoppedBanner } from '@/components/worker/WorkerStoppedBanner'
import { useQueueMonitorStore } from '@/store/queueMonitorStore'

export function QueueMonitorPage() {
  const filter = useQueueMonitorStore((s) => s.filter)
  const search = useQueueMonitorStore((s) => s.search)
  const setFilter = useQueueMonitorStore((s) => s.setFilter)
  const setSearch = useQueueMonitorStore((s) => s.setSearch)

  const snapshotQuery = useQueueSnapshotMonitor()
  const jobsQuery = useQueueJobsMonitor()
  useWorkerStatusMonitor()

  const cancelMutation = useCancelQueueJob()
  const { toast } = useToast()
  const [cancellingId, setCancellingId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const data = jobsQuery.data
    if (!data) {
      return { running: [], queued: [], failed: [], completed: [] }
    }
    return {
      running: filterQueueJobs(data.running, filter, search),
      queued: filterQueueJobs(data.queued, filter, search),
      failed: filterQueueJobs(data.failed, filter, search),
      completed: filterQueueJobs(data.completed, filter, search),
    }
  }, [jobsQuery.data, filter, search])

  function handleCancel(jobId: string) {
    setCancellingId(jobId)
    cancelMutation.mutate(jobId, {
      onSuccess: () => toast({ title: 'Job cancelled' }),
      onError: (error) =>
        toast({
          title: 'Cancel failed',
          description: error instanceof ApiError ? error.message : undefined,
          variant: 'error',
        }),
      onSettled: () => setCancellingId(null),
    })
  }

  const loading = snapshotQuery.isLoading || jobsQuery.isLoading

  return (
    <div className="space-y-6" data-testid="queue-monitor-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Queue Monitor</h1>
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Operational queue visibility
        </p>
      </div>

      <WorkerStoppedBanner />

      {snapshotQuery.isError ? (
        <p className="text-sm text-red-400" data-testid="queue-load-error">
          Unable to load queue
        </p>
      ) : loading ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <QueueSummaryCards snapshot={snapshotQuery.data} />
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <QueueFilters value={filter} onChange={setFilter} />
        <div className="w-full sm:max-w-xs">
          <QueueSearch value={search} onChange={setSearch} />
        </div>
      </div>

      {jobsQuery.isError ? (
        <p className="text-sm text-red-400" data-testid="queue-jobs-error">
          Unable to load queue
        </p>
      ) : jobsQuery.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-8">
          <RunningJobsSection jobs={filtered.running} />
          <QueuedJobsSection
            jobs={filtered.queued}
            onCancel={handleCancel}
            cancellingId={cancellingId}
          />
          <FailedJobsSection jobs={filtered.failed} />
          <CompletedJobsSection jobs={filtered.completed} />
        </div>
      )}
    </div>
  )
}
