import { apiClient } from '@/api/client'
import type { WorkerStatus } from '@/types/api'

export function getWorkerStatus(): Promise<WorkerStatus> {
  return apiClient<WorkerStatus>('/worker')
}
