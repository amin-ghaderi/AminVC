import { useQuery } from '@tanstack/react-query'

import { getRecentEvents } from '@/api/events'
import { findLatestVcProgress } from '@/lib/vcProgress'
import { queryKeys } from '@/hooks/queryKeys'
import { VC_PROGRESS_POLL_MS } from '@/hooks/pollingConstants'

export { VC_PROGRESS_POLL_MS } from '@/hooks/pollingConstants'

export function useVcProgress() {
  return useQuery({
    queryKey: queryKeys.vcProgress,
    queryFn: () => getRecentEvents(200),
    select: (events) => findLatestVcProgress(events),
    refetchInterval: VC_PROGRESS_POLL_MS,
  })
}
