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

export function findLatestVcProgress(
  events: EventEnvelope[],
): VcProgressPayload | null {
  const vcEvents = events
    .filter((e) => e.event_type === 'vc.progress')
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  if (!vcEvents.length) return null
  return parseVcProgressPayload(vcEvents[0].payload)
}

export function vcProgressPercent(progress: VcProgressPayload): number {
  if (progress.total_steps <= 0) return 0
  return Math.min(
    100,
    Math.round((progress.current_step / progress.total_steps) * 100),
  )
}
