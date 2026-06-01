import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { cancelQueueJob, getQueueJobs, getQueueSnapshot } from '@/api/queue'
import { getWorkerStatus } from '@/api/worker'
import { queryKeys } from '@/hooks/queryKeys'

import { QUEUE_MONITOR_POLL_MS } from '@/hooks/pollingConstants'

export { QUEUE_MONITOR_POLL_MS } from '@/hooks/pollingConstants'

export function useQueueSnapshotMonitor() {
  return useQuery({
    queryKey: queryKeys.queue.snapshot,
    queryFn: getQueueSnapshot,
    refetchInterval: QUEUE_MONITOR_POLL_MS,
  })
}

export function useQueueJobsMonitor() {
  return useQuery({
    queryKey: queryKeys.queue.jobs,
    queryFn: getQueueJobs,
    refetchInterval: QUEUE_MONITOR_POLL_MS,
  })
}

export function useWorkerStatusMonitor() {
  return useQuery({
    queryKey: queryKeys.worker.statusMonitor,
    queryFn: getWorkerStatus,
    refetchInterval: QUEUE_MONITOR_POLL_MS,
  })
}

export function useCancelQueueJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) => cancelQueueJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.queue.jobs })
      void queryClient.invalidateQueries({ queryKey: queryKeys.queue.snapshot })
    },
  })
}
