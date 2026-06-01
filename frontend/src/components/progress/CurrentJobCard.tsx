import type { QueueJob } from '@/types/api'

interface CurrentJobCardProps {
  job: QueueJob | undefined
}

export function CurrentJobCard({ job }: CurrentJobCardProps) {
  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid="current-job-panel"
    >
      <h2 className="text-lg font-semibold">Current Job</h2>
      {!job ? (
        <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
          No job currently running
        </p>
      ) : (
        <div className="mt-3 grid gap-1 text-sm">
          <p>
            <span className="text-[var(--color-muted-foreground)]">Job Type: </span>
            <span className="capitalize">{job.job_type}</span>
          </p>
          <p>
            <span className="text-[var(--color-muted-foreground)]">Project: </span>
            {job.project_id}
          </p>
          <p>
            <span className="text-[var(--color-muted-foreground)]">Part: </span>
            {job.part_id}
          </p>
          <p>
            <span className="text-[var(--color-muted-foreground)]">Chunk: </span>
            {job.chunk_id ?? '—'}
          </p>
        </div>
      )}
    </div>
  )
}
