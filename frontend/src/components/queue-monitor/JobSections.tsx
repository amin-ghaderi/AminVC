import type { ReactNode } from 'react'

import {
  CompletedJobCard,
  FailedJobCard,
  QueuedJobCard,
  RunningJobCard,
} from '@/components/queue-monitor/JobCards'
import type { QueueJob } from '@/types/api'

function Section({
  title,
  testId,
  children,
}: {
  title: string
  testId: string
  children: ReactNode
}) {
  return (
    <section data-testid={testId}>
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  )
}

export function RunningJobsSection({ jobs }: { jobs: QueueJob[] }) {
  return (
    <Section title="Currently Executing" testId="running-jobs-section">
      {jobs.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">No running jobs</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {jobs.map((job) => (
            <RunningJobCard key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </Section>
  )
}

export function QueuedJobsSection({
  jobs,
  onCancel,
  cancellingId,
}: {
  jobs: QueueJob[]
  onCancel: (jobId: string) => void
  cancellingId: string | null
}) {
  return (
    <Section title="Queued Jobs" testId="queued-jobs-section">
      {jobs.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">No queued jobs</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {jobs.map((job, index) => (
            <QueuedJobCard
              key={job.job_id}
              job={job}
              position={index + 1}
              onCancel={() => onCancel(job.job_id)}
              cancelling={cancellingId === job.job_id}
            />
          ))}
        </div>
      )}
    </Section>
  )
}

export function FailedJobsSection({ jobs }: { jobs: QueueJob[] }) {
  return (
    <Section title="Failed Jobs" testId="failed-jobs-section">
      {jobs.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">No failed jobs</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {jobs.map((job) => (
            <FailedJobCard key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </Section>
  )
}

export function CompletedJobsSection({ jobs }: { jobs: QueueJob[] }) {
  return (
    <Section title="Completed Jobs" testId="completed-jobs-section">
      {jobs.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">No completed jobs</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {jobs.map((job) => (
            <CompletedJobCard key={job.job_id} job={job} />
          ))}
        </div>
      )}
    </Section>
  )
}
