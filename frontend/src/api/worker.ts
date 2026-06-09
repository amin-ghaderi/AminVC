import { apiClient } from '@/api/client'
import type { WorkerStatus } from '@/types/api'

export function getWorkerStatus(): Promise<WorkerStatus> {
  return apiClient<WorkerStatus>('/worker')
}

export function startWorker(): Promise<{ status: string }> {
  return apiClient<{ status: string }>('/worker/start', { method: 'POST' })
}

export function stopWorker(): Promise<{ status: string }> {
  return apiClient<{ status: string }>('/worker/stop', { method: 'POST' })
}
