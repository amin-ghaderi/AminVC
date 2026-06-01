import type { QueueJob, QueueMonitorFilter } from '@/types/api'

export function matchesQueueJobType(job: QueueJob, filter: QueueMonitorFilter): boolean {
  if (filter === 'all') return true
  return job.job_type.toLowerCase() === filter
}

export function matchesQueueSearch(job: QueueJob, search: string): boolean {
  const q = search.trim().toLowerCase()
  if (!q) return true
  const fields = [
    job.project_id,
    job.part_id,
    job.job_id,
    job.chunk_id !== null ? String(job.chunk_id) : '',
  ]
  return fields.some((value) => value.toLowerCase().includes(q))
}

export function filterQueueJobs(jobs: QueueJob[], filter: QueueMonitorFilter, search: string) {
  return jobs
    .filter((job) => matchesQueueJobType(job, filter))
    .filter((job) => matchesQueueSearch(job, search))
}
