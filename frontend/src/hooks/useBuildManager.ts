import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  checkBuildDownloadAvailable,
  createBuild,
  listBuilds,
  queueBuild,
} from '@/api/builds'
import { getRecentEvents } from '@/api/events'
import { cancelQueueJob, getQueueJobs } from '@/api/queue'
import { getPart } from '@/api/parts'
import { listChunks } from '@/api/chunks'
import {
  BUILDS_POLL_MS,
  BUILD_EVENTS_POLL_MS,
  BUILD_QUEUE_JOBS_POLL_MS,
} from '@/hooks/pollingConstants'
import { queryKeys } from '@/hooks/queryKeys'
import type { CreateBuildRequest } from '@/types/api'

export {
  BUILDS_POLL_MS,
  BUILD_EVENTS_POLL_MS,
  BUILD_QUEUE_JOBS_POLL_MS,
} from '@/hooks/pollingConstants'

export function useBuildManagerPart(projectId: string, partId: string) {
  return useQuery({
    queryKey: ['parts', projectId, partId] as const,
    queryFn: () => getPart(projectId, partId),
    enabled: Boolean(projectId && partId),
  })
}

export function useBuildManagerChunks(projectId: string, partId: string) {
  return useQuery({
    queryKey: queryKeys.chunks(projectId, partId),
    queryFn: () => listChunks(projectId, partId),
    enabled: Boolean(projectId && partId),
  })
}

export function useBuildsQuery(projectId: string, partId: string) {
  return useQuery({
    queryKey: queryKeys.builds.list(projectId, partId),
    queryFn: () => listBuilds(projectId, partId),
    enabled: Boolean(projectId && partId),
    refetchInterval: BUILDS_POLL_MS,
  })
}

export function useBuildQueueJobs() {
  return useQuery({
    queryKey: queryKeys.queue.jobs,
    queryFn: getQueueJobs,
    refetchInterval: BUILD_QUEUE_JOBS_POLL_MS,
  })
}

export function useBuildEvents() {
  return useQuery({
    queryKey: queryKeys.eventsRecent,
    queryFn: () => getRecentEvents(200),
    refetchInterval: BUILD_EVENTS_POLL_MS,
  })
}

export function useBuildDownloadCheck(
  projectId: string,
  partId: string,
  buildId: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.builds.status(buildId),
    queryFn: () => checkBuildDownloadAvailable(projectId, partId, buildId),
    enabled: enabled && Boolean(projectId && partId && buildId),
    staleTime: BUILDS_POLL_MS,
  })
}

export function useCreateBuild(projectId: string, partId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateBuildRequest) =>
      createBuild(projectId, partId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.builds.all })
    },
  })
}

export function useQueueBuildMutation(projectId: string, partId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (buildId: string) => queueBuild(projectId, partId, buildId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.queue.jobs })
      void queryClient.invalidateQueries({ queryKey: queryKeys.builds.all })
    },
  })
}

export function useCancelBuildJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (buildId: string) => cancelQueueJob(buildId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.queue.jobs })
      void queryClient.invalidateQueries({ queryKey: queryKeys.builds.all })
    },
  })
}
