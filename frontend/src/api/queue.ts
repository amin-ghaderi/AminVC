import { apiClient } from '@/api/client'
import type { QueueJobBody, QueueJobsResponse, QueueSnapshot } from '@/types/api'

export function getQueueSnapshot(): Promise<QueueSnapshot> {
  return apiClient<QueueSnapshot>('/queue')
}

export function getQueueJobs(): Promise<QueueJobsResponse> {
  return apiClient<QueueJobsResponse>('/queue/jobs')
}

export function cancelQueueJob(jobId: string): Promise<Record<string, unknown>> {
  return apiClient<Record<string, unknown>>(
    `/queue/cancel/${encodeURIComponent(jobId)}`,
    { method: 'POST' },
  )
}

export function queueNarration(body: QueueJobBody): Promise<Record<string, unknown>> {
  return apiClient<Record<string, unknown>>('/queue/narration', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function queueVc(body: QueueJobBody): Promise<Record<string, unknown>> {
  return apiClient<Record<string, unknown>>('/queue/vc', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
