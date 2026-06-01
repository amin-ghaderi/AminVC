import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  approveNarration,
  approveVc,
  getChunk,
  getChunkAssets,
  listChunks,
  rebuildNarration,
  rebuildVc,
  unapproveNarration,
  unapproveVc,
  updateChunkText,
} from '@/api/chunks'
import { getRecentEvents } from '@/api/events'
import { getPartSummary } from '@/api/parts'
import { queueNarration, queueVc } from '@/api/queue'
import { queryKeys } from '@/hooks/queryKeys'
import type { QueueJobBody } from '@/types/api'

export const WORKSPACE_POLL_MS = 5000

export function usePartSummaryQuery(projectId: string, partId: string) {
  return useQuery({
    queryKey: queryKeys.partSummary(projectId, partId),
    queryFn: () => getPartSummary(projectId, partId),
    enabled: Boolean(projectId && partId),
    refetchInterval: WORKSPACE_POLL_MS,
  })
}

export function useChunksQuery(projectId: string, partId: string) {
  return useQuery({
    queryKey: queryKeys.chunks(projectId, partId),
    queryFn: () => listChunks(projectId, partId),
    enabled: Boolean(projectId && partId),
    refetchInterval: WORKSPACE_POLL_MS,
  })
}

export function useChunkQuery(
  projectId: string,
  partId: string,
  chunkId: number | null,
) {
  return useQuery({
    queryKey: queryKeys.chunk(projectId, partId, chunkId ?? 0),
    queryFn: () => getChunk(projectId, partId, chunkId!),
    enabled: Boolean(projectId && partId && chunkId !== null),
    refetchInterval: WORKSPACE_POLL_MS,
  })
}

export function useChunkAssetsQuery(
  projectId: string,
  partId: string,
  chunkId: number | null,
) {
  return useQuery({
    queryKey: queryKeys.chunkAssets(projectId, partId, chunkId ?? 0),
    queryFn: () => getChunkAssets(projectId, partId, chunkId!),
    enabled: Boolean(projectId && partId && chunkId !== null),
    refetchInterval: WORKSPACE_POLL_MS,
  })
}

export function useRecentEventsQuery() {
  return useQuery({
    queryKey: queryKeys.events.recent,
    queryFn: () => getRecentEvents(200),
    refetchInterval: WORKSPACE_POLL_MS,
  })
}

function useWorkspaceInvalidation(projectId: string, partId: string) {
  const queryClient = useQueryClient()
  return {
    invalidateChunkBundle: (chunkId: number) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.chunk(projectId, partId, chunkId),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.chunks(projectId, partId),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.partSummary(projectId, partId),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.chunkAssets(projectId, partId, chunkId),
      })
    },
    invalidateQueueAndEvents: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.queue.snapshot,
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.events.recent,
      })
    },
    refreshAll: (chunkId: number | null) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.chunks(projectId, partId),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.partSummary(projectId, partId),
      })
      if (chunkId !== null) {
        void queryClient.invalidateQueries({
          queryKey: queryKeys.chunk(projectId, partId, chunkId),
        })
        void queryClient.invalidateQueries({
          queryKey: queryKeys.chunkAssets(projectId, partId, chunkId),
        })
      }
      void queryClient.invalidateQueries({
        queryKey: queryKeys.events.recent,
      })
    },
  }
}

export function useSaveChunkTextMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: (text: string) =>
      updateChunkText(projectId, partId, chunkId, text),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useRebuildNarrationMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => rebuildNarration(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useRebuildVcMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => rebuildVc(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useApproveNarrationMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => approveNarration(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useUnapproveNarrationMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => unapproveNarration(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useApproveVcMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => approveVc(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useUnapproveVcMutation(
  projectId: string,
  partId: string,
  chunkId: number,
) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: () => unapproveVc(projectId, partId, chunkId),
    onSuccess: () => invalidation.invalidateChunkBundle(chunkId),
  })
}

export function useQueueNarrationMutation(projectId: string, partId: string) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: (body: QueueJobBody) => queueNarration(body),
    onSuccess: () => invalidation.invalidateQueueAndEvents(),
  })
}

export function useQueueVcMutation(projectId: string, partId: string) {
  const invalidation = useWorkspaceInvalidation(projectId, partId)
  return useMutation({
    mutationFn: (body: QueueJobBody) => queueVc(body),
    onSuccess: () => invalidation.invalidateQueueAndEvents(),
  })
}

export { useWorkspaceInvalidation }
