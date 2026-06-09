import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getWorkerStatus, startWorker, stopWorker } from '@/api/worker'
import { queryKeys } from '@/hooks/queryKeys'

const WORKER_POLL_MS = 3000

function invalidateWorkerQueries(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.worker.status })
  void queryClient.invalidateQueries({ queryKey: queryKeys.worker.statusMonitor })
}

export function useWorkerStatus() {
  return useQuery({
    queryKey: queryKeys.worker.status,
    queryFn: getWorkerStatus,
    refetchInterval: WORKER_POLL_MS,
  })
}

export function useStartWorker() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: startWorker,
    onSuccess: () => invalidateWorkerQueries(queryClient),
  })
}

export function useStopWorker() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: stopWorker,
    onSuccess: () => invalidateWorkerQueries(queryClient),
  })
}
