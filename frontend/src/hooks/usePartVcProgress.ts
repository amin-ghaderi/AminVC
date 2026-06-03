import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getRecentEvents } from '@/api/events'
import { getPartSummary } from '@/api/parts'
import { computePartVcProgress } from '@/lib/partVcProgress'
import { queryKeys } from '@/hooks/queryKeys'
import { VC_PROGRESS_POLL_MS } from '@/hooks/pollingConstants'

export interface UsePartVcProgressOptions {
  /** When set, only use vc.progress for this chunk. */
  chunkId?: number
  /** When true, hide current-chunk block unless chunkIsProcessing. */
  requireChunkProcessing?: boolean
  chunkIsProcessing?: boolean
  enabled?: boolean
}

export function usePartVcProgress(
  projectId: string,
  partId: string,
  options: UsePartVcProgressOptions = {},
) {
  const enabled =
    options.enabled !== false && Boolean(projectId && partId)

  const summaryQuery = useQuery({
    queryKey: queryKeys.partSummary(projectId, partId),
    queryFn: () => getPartSummary(projectId, partId),
    enabled,
    refetchInterval: VC_PROGRESS_POLL_MS,
  })

  const eventsQuery = useQuery({
    queryKey: queryKeys.events.recent,
    queryFn: () => getRecentEvents(200),
    enabled,
    refetchInterval: VC_PROGRESS_POLL_MS,
  })

  const view = useMemo(
    () =>
      computePartVcProgress({
        events: eventsQuery.data,
        summary: summaryQuery.data,
        projectId,
        partId,
        chunkId: options.chunkId,
        requireChunkProcessing: options.requireChunkProcessing,
        chunkIsProcessing: options.chunkIsProcessing,
      }),
    [
      eventsQuery.data,
      summaryQuery.data,
      projectId,
      partId,
      options.chunkId,
      options.requireChunkProcessing,
      options.chunkIsProcessing,
    ],
  )

  return {
    ...view,
    isLoading: summaryQuery.isLoading || eventsQuery.isLoading,
    isError: summaryQuery.isError || eventsQuery.isError,
  }
}

/** Dashboard: resolve project/part from latest global vc.progress when not provided. */
export function useDashboardPartVcProgress() {
  const eventsQuery = useQuery({
    queryKey: queryKeys.events.recent,
    queryFn: () => getRecentEvents(200),
    refetchInterval: VC_PROGRESS_POLL_MS,
  })

  const scope = useMemo(() => {
    const events = eventsQuery.data ?? []
    const latest = events
      .filter((e) => e.event_type === 'vc.progress')
      .sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0]
    if (latest?.project_id && latest?.part_id) {
      return { projectId: latest.project_id, partId: latest.part_id }
    }
    return null
  }, [eventsQuery.data])

  const progress = usePartVcProgress(scope?.projectId ?? '', scope?.partId ?? '', {
    enabled: Boolean(scope),
  })

  return {
    ...progress,
    scope,
    isLoading: eventsQuery.isLoading || progress.isLoading,
    isError: eventsQuery.isError || progress.isError,
  }
}
