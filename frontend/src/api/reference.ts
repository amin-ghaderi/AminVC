import { apiClient } from '@/api/client'
import type {
  ReferenceAudioDeleteResponse,
  ReferenceAudioUploadResponse,
} from '@/types/api'

const API_BASE = '/api/v1'

export function referenceAudioUrl(projectId: string, partId: string): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/reference`
}

export function uploadReferenceAudio(
  projectId: string,
  partId: string,
  file: File,
): Promise<ReferenceAudioUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return apiClient<ReferenceAudioUploadResponse>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/reference`,
    { method: 'POST', body: form },
  )
}

export function deleteReferenceAudio(
  projectId: string,
  partId: string,
): Promise<ReferenceAudioDeleteResponse> {
  return apiClient<ReferenceAudioDeleteResponse>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/reference`,
    { method: 'DELETE' },
  )
}
