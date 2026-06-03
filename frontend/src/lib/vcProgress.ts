import type { EventEnvelope, VcProgressPayload } from '@/types/api'

export function parseVcProgressPayload(
  payload: Record<string, unknown>,
): VcProgressPayload | null {
  const current = payload.current_step
  const total = payload.total_steps
  if (typeof current !== 'number' || typeof total !== 'number' || total <= 0) {
    return null
  }
  return {
    current_step: current,
    total_steps: total,
    elapsed_seconds:
      typeof payload.elapsed_seconds === 'number' ? payload.elapsed_seconds : 0,
    estimated_remaining_seconds:
      typeof payload.estimated_remaining_seconds === 'number'
        ? payload.estimated_remaining_seconds
        : 0,
  }
}

export function findLatestVcProgressEvent(
  events: EventEnvelope[],
): EventEnvelope | null {
  const vcEvents = events
    .filter((e) => e.event_type === 'vc.progress')
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  return vcEvents[0] ?? null
}

export function findLatestVcProgress(
  events: EventEnvelope[],
): VcProgressPayload | null {
  const latest = findLatestVcProgressEvent(events)
  if (!latest) return null
  return parseVcProgressPayload(latest.payload)
}

export function findLatestVcProgressForPart(
  events: EventEnvelope[],
  projectId: string,
  partId: string,
  chunkId?: number,
): VcProgressPayload | null {
  const event = findLatestVcProgressEventForPart(
    events,
    projectId,
    partId,
    chunkId,
  )
  if (!event) return null
  return parseVcProgressPayload(event.payload)
}

export function findLatestVcProgressEventForPart(
  events: EventEnvelope[],
  projectId: string,
  partId: string,
  chunkId?: number,
): EventEnvelope | null {
  const vcEvents = events
    .filter(
      (e) =>
        e.event_type === 'vc.progress' &&
        e.project_id === projectId &&
        e.part_id === partId &&
        (chunkId === undefined || e.chunk_id === chunkId),
    )
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  return vcEvents[0] ?? null
}

export function vcProgressPercent(progress: VcProgressPayload): number {
  if (progress.total_steps <= 0) return 0
  return Math.min(
    100,
    Math.round((progress.current_step / progress.total_steps) * 100),
  )
}
