import { BuildCard } from '@/components/build-manager/BuildCard'
import { Skeleton } from '@/components/ui/skeleton'
import type { Build, EventEnvelope, QueueJobsResponse } from '@/types/api'

interface BuildListProps {
  builds: Build[] | undefined
  loading: boolean
  error: boolean
  projectId: string
  partId: string
  jobs: QueueJobsResponse | undefined
  events: EventEnvelope[] | undefined
  downloadReadyByBuildId: Record<string, boolean>
  expandedBuildId: string | null
  onToggleExpand: (buildId: string) => void
  onQueue: (buildId: string) => void
  onCancel: (buildId: string) => void
  queuingId: string | null
  cancellingId: string | null
}

export function BuildList({
  builds,
  loading,
  error,
  projectId,
  partId,
  jobs,
  events,
  downloadReadyByBuildId,
  expandedBuildId,
  onToggleExpand,
  onQueue,
  onCancel,
  queuingId,
  cancellingId,
}: BuildListProps) {
  if (error) {
    return (
      <p className="text-sm text-red-400" data-testid="builds-load-error">
        Unable to load builds
      </p>
    )
  }

  if (loading) {
    return <Skeleton className="h-40 w-full" data-testid="builds-loading" />
  }

  if (!builds?.length) {
    return (
      <p
        className="text-sm text-[var(--color-muted-foreground)]"
        data-testid="no-builds-empty"
      >
        No builds created yet.
      </p>
    )
  }

  return (
    <div className="space-y-3" data-testid="build-list">
      {builds.map((build) => (
        <BuildCard
          key={build.build_id}
          build={build}
          projectId={projectId}
          partId={partId}
          jobs={jobs}
          events={events}
          downloadAvailable={downloadReadyByBuildId[build.build_id]}
          expanded={expandedBuildId === build.build_id}
          onToggleExpand={() => onToggleExpand(build.build_id)}
          onQueue={() => onQueue(build.build_id)}
          onCancel={() => onCancel(build.build_id)}
          queuing={queuingId === build.build_id}
          cancelling={cancellingId === build.build_id}
        />
      ))}
    </div>
  )
}
