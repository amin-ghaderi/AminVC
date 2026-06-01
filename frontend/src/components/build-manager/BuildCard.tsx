import { BuildDetails } from '@/components/build-manager/BuildDetails'
import { StatusBadge } from '@/components/build-manager/StatusBadge'
import { Button } from '@/components/ui/button'
import { getBuildDownloadUrl } from '@/api/builds'
import {
  canCancelBuild,
  canDownloadBuild,
  canQueueBuild,
  deriveBuildStatus,
} from '@/lib/buildStatus'
import type { Build, BuildStatus, EventEnvelope, QueueJobsResponse } from '@/types/api'

interface BuildCardProps {
  build: Build
  projectId: string
  partId: string
  jobs: QueueJobsResponse | undefined
  events: EventEnvelope[] | undefined
  downloadAvailable?: boolean
  expanded: boolean
  onToggleExpand: () => void
  onQueue: () => void
  onCancel: () => void
  queuing: boolean
  cancelling: boolean
}

export function BuildCard({
  build,
  projectId,
  partId,
  jobs,
  events,
  downloadAvailable,
  expanded,
  onToggleExpand,
  onQueue,
  onCancel,
  queuing,
  cancelling,
}: BuildCardProps) {
  const status: BuildStatus = deriveBuildStatus(build.build_id, jobs, {
    downloadAvailable,
  })
  const downloadUrl = getBuildDownloadUrl(projectId, partId, build.build_id)

  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid={`build-card-${build.build_id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{build.name}</h3>
          <p className="mt-1 font-mono text-xs text-[var(--color-muted-foreground)]">
            {build.build_id}
          </p>
          <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
            {build.chunks.length} chunk{build.chunks.length === 1 ? '' : 's'} · Created{' '}
            {build.created_at}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {canQueueBuild(status) ? (
          <Button
            type="button"
            size="sm"
            onClick={onQueue}
            disabled={queuing}
            data-testid={`queue-build-${build.build_id}`}
          >
            Queue Build
          </Button>
        ) : null}
        {canCancelBuild(status) ? (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={onCancel}
            disabled={cancelling}
            data-testid={`cancel-build-${build.build_id}`}
          >
            Cancel
          </Button>
        ) : null}
        {canDownloadBuild(status) ? (
          <a
            href={downloadUrl}
            download={`${build.build_id}.wav`}
            className="inline-flex h-8 items-center rounded-md bg-[var(--color-primary)] px-3 text-xs font-medium text-[var(--color-primary-foreground)] hover:opacity-90"
            data-testid={`download-build-${build.build_id}`}
          >
            Download WAV
          </a>
        ) : null}
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={onToggleExpand}
          data-testid={`expand-build-${build.build_id}`}
        >
          {expanded ? 'Hide Details' : 'Show Details'}
        </Button>
      </div>

      {expanded ? <BuildDetails build={build} events={events} /> : null}
    </div>
  )
}
