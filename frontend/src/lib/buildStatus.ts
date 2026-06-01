import type { BuildStatus, QueueJob, QueueJobsResponse } from '@/types/api'

function findBuildJob(jobs: QueueJob[], buildId: string): QueueJob | undefined {
  return jobs.find((j) => j.job_type === 'build' && j.job_id === buildId)
}

export function deriveBuildStatus(
  buildId: string,
  jobs: QueueJobsResponse | undefined,
  options?: { downloadAvailable?: boolean },
): BuildStatus {
  if (!jobs) {
    return 'Created'
  }
  if (findBuildJob(jobs.running, buildId)) {
    return 'Running'
  }
  if (findBuildJob(jobs.queued, buildId)) {
    return 'Queued'
  }
  if (findBuildJob(jobs.failed, buildId)) {
    return 'Failed'
  }
  if (findBuildJob(jobs.cancelled, buildId)) {
    return 'Cancelled'
  }
  if (findBuildJob(jobs.completed, buildId) || options?.downloadAvailable) {
    return 'Completed'
  }
  return 'Created'
}

export function canQueueBuild(status: BuildStatus): boolean {
  return status === 'Created' || status === 'Failed' || status === 'Cancelled'
}

export function canCancelBuild(status: BuildStatus): boolean {
  return status === 'Queued'
}

export function canDownloadBuild(status: BuildStatus): boolean {
  return status === 'Completed'
}
