import { apiClient } from '@/api/client'
import type {
  ChunkingRequest,
  ChunkingResponse,
  CreatePartRequest,
  ExtractTextResponse,
  Part,
  PartSummary,
  SourceUploadResponse,
} from '@/types/api'

export function getPart(projectId: string, partId: string): Promise<Part> {
  return apiClient<Part>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}`,
  )
}

export function listParts(projectId: string): Promise<Part[]> {
  return apiClient<Part[]>(
    `/projects/${encodeURIComponent(projectId)}/parts`,
  )
}

export function createPart(
  projectId: string,
  body: CreatePartRequest,
): Promise<Part> {
  return apiClient<Part>(`/projects/${encodeURIComponent(projectId)}/parts`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function uploadSourcePdf(
  projectId: string,
  partId: string,
  file: File,
): Promise<SourceUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return apiClient<SourceUploadResponse>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/source`,
    { method: 'POST', body: form },
  )
}

export function extractPartText(
  projectId: string,
  partId: string,
): Promise<ExtractTextResponse> {
  return apiClient<ExtractTextResponse>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/extract-text`,
    { method: 'POST' },
  )
}

export function createPartChunks(
  projectId: string,
  partId: string,
  body: ChunkingRequest,
): Promise<ChunkingResponse> {
  return apiClient<ChunkingResponse>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/chunking`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
  )
}

export function getPartSummary(
  projectId: string,
  partId: string,
): Promise<PartSummary> {
  return apiClient<PartSummary>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/summary`,
  )
}
