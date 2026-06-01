import { useQuery } from '@tanstack/react-query'

import { getRecentEvents } from '@/api/events'
import { queryKeys } from '@/hooks/queryKeys'
import { EVENTS_POLL_MS } from '@/hooks/pollingConstants'

export { EVENTS_POLL_MS } from '@/hooks/pollingConstants'

export function useRecentEventsMonitor(limit = 20) {
  return useQuery({
    queryKey: queryKeys.eventsRecent,
    queryFn: () => getRecentEvents(200),
    refetchInterval: EVENTS_POLL_MS,
    select: (events) => events.slice(0, limit),
  })
}
