import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createPart, listParts } from '@/api/parts'
import { queryKeys } from '@/hooks/queryKeys'
import type { CreatePartRequest } from '@/types/api'

export function usePartsList(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.parts.list(projectId ?? ''),
    queryFn: () => listParts(projectId!),
    enabled: Boolean(projectId),
  })
}

export function useCreatePart(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreatePartRequest) => createPart(projectId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.parts.list(projectId),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(projectId),
      })
    },
  })
}
