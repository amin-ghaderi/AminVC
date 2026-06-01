import { useMemo } from 'react'

import type { EventEnvelope } from '@/types/api'

interface HistoryTabProps {
  projectId: string
  partId: string
  chunkId: number
  events: EventEnvelope[] | undefined
}

export function HistoryTab({
  projectId,
  partId,
  chunkId,
  events,
}: HistoryTabProps) {
  const filtered = useMemo(() => {
    if (!events) return []
    return events.filter(
      (e) =>
        e.project_id === projectId &&
        e.part_id === partId &&
        e.chunk_id === chunkId,
    )
  }, [events, projectId, partId, chunkId])

  if (!filtered.length) {
    return (
      <p
        className="text-sm text-[var(--color-muted-foreground)]"
        data-testid="history-empty"
      >
        No events available
      </p>
    )
  }

  return (
    <ul className="space-y-2" data-testid="history-list">
      {filtered.map((event) => (
        <li
          key={event.event_id}
          className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
        >
          <div className="flex flex-wrap justify-between gap-2 text-xs text-[var(--color-muted-foreground)]">
            <span>{event.timestamp}</span>
            <span className="font-mono">{event.event_type}</span>
          </div>
          <p className="mt-1">{eventSummary(event)}</p>
        </li>
      ))}
    </ul>
  )
}

function eventSummary(event: EventEnvelope): string {
  const payload = event.payload
  if (typeof payload.message === 'string') return payload.message
  if (typeof payload.status === 'string') return payload.status
  if (typeof payload.job_type === 'string') {
    return `${payload.job_type} job`
  }
  return event.event_type
}
