import { useEffect, useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ChunkDetails } from '@/components/part-workspace/ChunkDetails'
import { ChunkFilters } from '@/components/part-workspace/ChunkFilters'
import { ChunkList } from '@/components/part-workspace/ChunkList'
import { ChunkSearch } from '@/components/part-workspace/ChunkSearch'
import { PartHeader } from '@/components/part-workspace/PartHeader'
import { ReferenceVoicePanel } from '@/components/part-workspace/ReferenceVoicePanel'
import { Skeleton } from '@/components/ui/skeleton'
import { filterChunks } from '@/lib/chunkFilters'
import {
  useChunksQuery,
  usePartSummaryQuery,
} from '@/hooks/usePartWorkspace'
import { getPart } from '@/api/parts'
import { useQuery } from '@tanstack/react-query'
import { usePartWorkspaceStore } from '@/store/partWorkspaceStore'
import { useUiStore } from '@/store/uiStore'
import { WorkerStoppedBanner } from '@/components/worker/WorkerStoppedBanner'

export function PartWorkspacePage() {
  const { projectId, partId } = useParams<{
    projectId: string
    partId: string
  }>()

  const filter = usePartWorkspaceStore((s) => s.filter)
  const search = usePartWorkspaceStore((s) => s.search)
  const selectedChunkId = usePartWorkspaceStore((s) => s.selectedChunkId)
  const setFilter = usePartWorkspaceStore((s) => s.setFilter)
  const setSearch = usePartWorkspaceStore((s) => s.setSearch)
  const setSelectedChunk = usePartWorkspaceStore((s) => s.setSelectedChunk)
  const reset = usePartWorkspaceStore((s) => s.reset)
  const setCurrentProject = useUiStore((s) => s.setCurrentProject)

  const partQuery = useQuery({
    queryKey: ['part', projectId, partId],
    queryFn: () => getPart(projectId!, partId!),
    enabled: Boolean(projectId && partId),
  })

  const summaryQuery = usePartSummaryQuery(projectId ?? '', partId ?? '')
  const chunksQuery = useChunksQuery(projectId ?? '', partId ?? '')

  const filteredChunks = useMemo(() => {
    if (!chunksQuery.data) return []
    return filterChunks(chunksQuery.data, filter, search)
  }, [chunksQuery.data, filter, search])

  useEffect(() => {
    if (!projectId || !partId) return
    if (partQuery.data) {
      setCurrentProject(projectId, partQuery.data.title)
    }
    return () => {
      setCurrentProject(null)
      reset()
    }
  }, [projectId, partId, partQuery.data, setCurrentProject, reset])

  useEffect(() => {
    if (!filteredChunks.length) return
    if (
      selectedChunkId === null ||
      !filteredChunks.some((c) => c.chunk_id === selectedChunkId)
    ) {
      setSelectedChunk(filteredChunks[0].chunk_id)
    }
  }, [filteredChunks, selectedChunkId, setSelectedChunk])

  if (!projectId || !partId) {
    return <p className="text-sm text-red-400">Missing route parameters.</p>
  }

  if (partQuery.isLoading || chunksQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (partQuery.isError || !partQuery.data) {
    return <p className="text-sm text-red-400">Failed to load part.</p>
  }

  return (
    <div className="space-y-4" data-testid="part-workspace">
      <Link
        to={`/projects/${encodeURIComponent(projectId)}`}
        className="text-sm text-[var(--color-muted-foreground)] hover:underline"
      >
        ← Back to project
      </Link>
      <WorkerStoppedBanner />
      <PartHeader
        part={partQuery.data}
        summary={summaryQuery.data}
        projectId={projectId}
        partId={partId}
        selectedChunkId={selectedChunkId}
      />
      <ReferenceVoicePanel
        projectId={projectId}
        partId={partId}
        part={partQuery.data}
      />
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="space-y-3">
          <ChunkFilters value={filter} onChange={setFilter} />
          <ChunkSearch value={search} onChange={setSearch} />
          <ChunkList
            chunks={filteredChunks}
            selectedChunkId={selectedChunkId}
            onSelect={setSelectedChunk}
          />
        </div>
        <ChunkDetails
          projectId={projectId}
          partId={partId}
          chunkId={selectedChunkId}
          referenceAudioReady={partQuery.data.reference_audio.exists}
        />
      </div>
    </div>
  )
}
