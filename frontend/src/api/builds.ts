import { apiClient } from '@/api/client'
import type { Build, CreateBuildRequest } from '@/types/api'

const API_BASE = '/api/v1'

export function listBuilds(projectId: string, partId: string): Promise<Build[]> {
  return apiClient<Build[]>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/builds`,
  )
}

export function getBuild(
  projectId: string,
  partId: string,
  buildId: string,
): Promise<Build> {
  return apiClient<Build>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/builds/${encodeURIComponent(buildId)}`,
  )
}

export function createBuild(
  projectId: string,
  partId: string,
  body: CreateBuildRequest,
): Promise<Build> {
  return apiClient<Build>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/builds`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
  )
}

export function queueBuild(
  projectId: string,
  partId: string,
  buildId: string,
): Promise<Record<string, unknown>> {
  return apiClient<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/builds/${encodeURIComponent(buildId)}/queue`,
    { method: 'POST' },
  )
}

export function getBuildDownloadUrl(
  projectId: string,
  partId: string,
  buildId: string,
): string {
  return `${API_BASE}/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/builds/${encodeURIComponent(buildId)}/download`
}

export async function checkBuildDownloadAvailable(
  projectId: string,
  partId: string,
  buildId: string,
): Promise<boolean> {
  const url = getBuildDownloadUrl(projectId, partId, buildId)
  try {
    const response = await fetch(url, { method: 'GET', headers: { Range: 'bytes=0-0' } })
    return response.ok
  } catch {
    return false
  }
}
