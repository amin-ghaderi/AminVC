import { apiClient } from '@/api/client'
import type { QueueSnapshot } from '@/types/api'

export function getQueueSnapshot(): Promise<QueueSnapshot> {
  return apiClient<QueueSnapshot>('/queue')
}
