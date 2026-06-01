import type { EventEnvelope } from '@/types/api'

let recentEvents: EventEnvelope[] = []

export function getRecentEventsForMock(): EventEnvelope[] {
  return recentEvents
}

export function setRecentEventsForMock(events: EventEnvelope[]) {
  recentEvents = events
}

export function syncRecentEvents(
  workspaceEvents: EventEnvelope[],
  monitorEvents: EventEnvelope[],
) {
  const byId = new Map<string, EventEnvelope>()
  for (const event of [...workspaceEvents, ...monitorEvents]) {
    byId.set(event.event_id, event)
  }
  recentEvents = [...byId.values()].sort((a, b) =>
    b.timestamp.localeCompare(a.timestamp),
  )
}
