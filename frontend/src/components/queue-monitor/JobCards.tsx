import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { QueueJob } from '@/types/api'

function JobMeta({ job }: { job: QueueJob }) {
  return (
    <div className="mt-2 grid gap-1 text-xs text-[var(--color-muted-foreground)]">
      <p>Project: {job.project_id}</p>
      <p>Part: {job.part_id}</p>
      <p>Chunk: {job.chunk_id ?? '—'}</p>
      <p className="font-mono text-[10px]">{job.job_id}</p>
    </div>
  )
}

export function RunningJobCard({ job }: { job: QueueJob }) {
  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid={`running-job-${job.job_id}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-medium capitalize">{job.job_type}</p>
        <Badge>RUNNING</Badge>
      </div>
      <JobMeta job={job} />
      <p className="mt-2 text-xs">Started At: {job.started_at || '—'}</p>
      <p className="text-xs">Attempts: {job.attempts}</p>
    </div>
  )
}

export function QueuedJobCard({
  job,
  position,
  onCancel,
  cancelling,
}: {
  job: QueueJob
  position: number
  onCancel: () => void
  cancelling: boolean
}) {
  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid={`queued-job-${job.job_id}`}
    >
      <p className="text-xs text-[var(--color-muted-foreground)]">Position: {position}</p>
      <p className="mt-1 font-medium capitalize">{job.job_type}</p>
      <JobMeta job={job} />
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="mt-3"
        onClick={onCancel}
        disabled={cancelling}
      >
        Cancel
      </Button>
    </div>
  )
}

export function FailedJobCard({ job }: { job: QueueJob }) {
  return (
    <div
      className="rounded-lg border border-red-500/30 p-4"
      data-testid={`failed-job-${job.job_id}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-medium capitalize">{job.job_type}</p>
        <Badge variant="outline" className="border-red-500/50 text-red-400">
          FAILED
        </Badge>
      </div>
      <JobMeta job={job} />
      <p className="mt-2 text-xs text-red-300">Last Error: {job.last_error || '—'}</p>
    </div>
  )
}

export function CompletedJobCard({ job }: { job: QueueJob }) {
  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid={`completed-job-${job.job_id}`}
    >
      <p className="font-medium capitalize">{job.job_type}</p>
      <JobMeta job={job} />
      <p className="mt-2 text-xs">Completed At: {job.completed_at || '—'}</p>
    </div>
  )
}
