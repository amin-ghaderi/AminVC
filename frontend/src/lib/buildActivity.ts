import type { EventEnvelope } from '@/types/api'

const MONITORED_BUILD_EVENTS = new Set([
  'queue.job_queued',
  'queue.job_started',
  'queue.job_completed',
  'queue.job_failed',
  'worker.job_started',
  'worker.job_completed',
])

function eventMatchesBuild(event: EventEnvelope, buildId: string): boolean {
  const payload = event.payload
  const jobId = payload.job_id
  if (typeof jobId === 'string' && jobId === buildId) {
    return true
  }
  const jobType = payload.job_type
  return jobType === 'build' && jobId === buildId
}

export function getBuildLastActivity(
  buildId: string,
  events: EventEnvelope[] | undefined,
): string | null {
  if (!events?.length) {
    return null
  }
  const match = events
    .filter(
      (e) =>
        MONITORED_BUILD_EVENTS.has(e.event_type) &&
        eventMatchesBuild(e, buildId),
    )
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0]
  if (!match) {
    return null
  }
  return `${match.event_type} · ${match.timestamp}`
}
