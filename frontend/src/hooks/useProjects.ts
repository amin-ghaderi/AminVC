import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createProject, getProject, listProjects } from '@/api/projects'
import { queryKeys } from '@/hooks/queryKeys'
import type { CreateProjectRequest } from '@/types/api'

export function useProjectsList() {
  return useQuery({
    queryKey: queryKeys.projects.all,
    queryFn: listProjects,
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectId ?? ''),
    queryFn: () => getProject(projectId!),
    enabled: Boolean(projectId),
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateProjectRequest) => createProject(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
    },
  })
}
