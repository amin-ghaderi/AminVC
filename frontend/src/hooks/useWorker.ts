import { useQuery } from '@tanstack/react-query'

import { getWorkerStatus } from '@/api/worker'
import { queryKeys } from '@/hooks/queryKeys'

const WORKER_POLL_MS = 3000

export function useWorkerStatus() {
  return useQuery({
    queryKey: queryKeys.worker.status,
    queryFn: getWorkerStatus,
    refetchInterval: WORKER_POLL_MS,
  })
}
