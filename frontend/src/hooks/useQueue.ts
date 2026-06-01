import { useQuery } from '@tanstack/react-query'

import { getQueueSnapshot } from '@/api/queue'
import { queryKeys } from '@/hooks/queryKeys'

const QUEUE_POLL_MS = 3000

export function useQueueSnapshot() {
  return useQuery({
    queryKey: queryKeys.queue.snapshot,
    queryFn: getQueueSnapshot,
    refetchInterval: QUEUE_POLL_MS,
  })
}
