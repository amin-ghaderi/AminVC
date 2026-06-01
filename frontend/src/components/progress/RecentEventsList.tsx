import { summarizeEvent } from '@/lib/eventSummary'
import type { EventEnvelope } from '@/types/api'

interface RecentEventsListProps {
  events: EventEnvelope[] | undefined
  error?: boolean
}

export function RecentEventsList({ events, error }: RecentEventsListProps) {
  if (error) {
    return (
      <p className="text-sm text-red-400" data-testid="events-error">
        Unable to load events
      </p>
    )
  }

  if (!events?.length) {
    return (
      <p className="text-sm text-[var(--color-muted-foreground)]">No events available</p>
    )
  }

  return (
    <ul className="space-y-2" data-testid="recent-events-list">
      {events.map((event) => (
        <li
          key={event.event_id}
          className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
        >
          <div className="flex flex-wrap justify-between gap-2 text-xs text-[var(--color-muted-foreground)]">
            <span>{event.timestamp}</span>
            <span className="font-mono">{event.event_type}</span>
          </div>
          <p className="mt-1">{summarizeEvent(event)}</p>
        </li>
      ))}
    </ul>
  )
}
