import { apiClient } from '@/api/client'
import type { EventEnvelope } from '@/types/api'

export function getRecentEvents(limit = 100): Promise<EventEnvelope[]> {
  return apiClient<EventEnvelope[]>(`/events/recent?limit=${limit}`)
}
