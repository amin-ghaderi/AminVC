import type { EventEnvelope } from '@/types/api'

export function summarizeEvent(event: EventEnvelope): string {
  const payload = event.payload
  if (typeof payload.message === 'string') return payload.message
  if (event.event_type === 'vc.progress') {
    const step = payload.current_step
    const total = payload.total_steps
    if (typeof step === 'number' && typeof total === 'number') {
      return `VC step ${step} / ${total}`
    }
  }
  if (event.event_type === 'queue.job_queued' && typeof payload.job_type === 'string') {
    return `${payload.job_type} job queued`
  }
  if (event.event_type === 'worker.job_started') {
    return 'Worker job started'
  }
  if (event.event_type === 'vc.chunk_completed') {
    return 'VC chunk completed'
  }
  if (event.event_type === 'narration.approved') {
    return 'Narration approved'
  }
  if (typeof payload.status === 'string') return payload.status
  if (typeof payload.job_type === 'string') {
    return `${payload.job_type} — ${event.event_type}`
  }
  return event.event_type
}
