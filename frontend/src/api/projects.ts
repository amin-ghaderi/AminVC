import { apiClient } from '@/api/client'
import type { CreateProjectRequest, Project } from '@/types/api'

export function listProjects(): Promise<Project[]> {
  return apiClient<Project[]>('/projects')
}

export function getProject(projectId: string): Promise<Project> {
  return apiClient<Project>(`/projects/${encodeURIComponent(projectId)}`)
}

export function createProject(body: CreateProjectRequest): Promise<Project> {
  return apiClient<Project>('/projects', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
