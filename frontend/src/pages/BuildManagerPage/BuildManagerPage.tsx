import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { BuildCreationPanel } from '@/components/build-manager/BuildCreationPanel'
import { BuildHeader } from '@/components/build-manager/BuildHeader'
import { BuildList } from '@/components/build-manager/BuildList'
import { useToast } from '@/components/shared/ToastProvider'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError } from '@/api/client'
import { filterVcApprovedChunks } from '@/lib/buildChunks'
import {
  useBuildDownloadCheck,
  useBuildEvents,
  useBuildManagerChunks,
  useBuildManagerPart,
  useBuildQueueJobs,
  useBuildsQuery,
  useCancelBuildJob,
  useCreateBuild,
  useQueueBuildMutation,
} from '@/hooks/useBuildManager'
import { useBuildManagerStore } from '@/store/buildManagerStore'

export function BuildManagerPage() {
  const { projectId = '', partId = '' } = useParams()
  const { toast } = useToast()

  const selectedChunks = useBuildManagerStore((s) => s.selectedChunks)
  const expandedBuildId = useBuildManagerStore((s) => s.expandedBuildId)
  const setSelectedChunks = useBuildManagerStore((s) => s.setSelectedChunks)
  const toggleChunk = useBuildManagerStore((s) => s.toggleChunk)
  const clearSelection = useBuildManagerStore((s) => s.clearSelection)
  const setExpandedBuild = useBuildManagerStore((s) => s.setExpandedBuild)

  const partQuery = useBuildManagerPart(projectId, partId)
  const chunksQuery = useBuildManagerChunks(projectId, partId)
  const buildsQuery = useBuildsQuery(projectId, partId)
  const jobsQuery = useBuildQueueJobs()
  const eventsQuery = useBuildEvents()

  const createMutation = useCreateBuild(projectId, partId)
  const queueMutation = useQueueBuildMutation(projectId, partId)
  const cancelMutation = useCancelBuildJob()

  const [queuingId, setQueuingId] = useState<string | null>(null)
  const [cancellingId, setCancellingId] = useState<string | null>(null)

  const eligibleChunks = useMemo(
    () => filterVcApprovedChunks(chunksQuery.data ?? []),
    [chunksQuery.data],
  )

  const primaryBuildId = buildsQuery.data?.[0]?.build_id ?? ''
  const downloadCheck = useBuildDownloadCheck(
    projectId,
    partId,
    primaryBuildId,
    Boolean(primaryBuildId),
  )

  const downloadReadyByBuildId = useMemo(() => {
    const map: Record<string, boolean> = {}
    if (primaryBuildId && downloadCheck.data) {
      map[primaryBuildId] = true
    }
    return map
  }, [primaryBuildId, downloadCheck.data])

  function handleSelectAll() {
    setSelectedChunks(eligibleChunks.map((c) => c.chunk_id))
  }

  function handleSelectVcApproved() {
    setSelectedChunks(eligibleChunks.map((c) => c.chunk_id))
  }

  function handleCreate(name: string) {
    createMutation.mutate(
      { name, chunks: selectedChunks },
      {
        onSuccess: () => {
          toast({ title: 'Build Created' })
          clearSelection()
        },
        onError: (error) =>
          toast({
            title: 'Create build failed',
            description: error instanceof ApiError ? error.message : undefined,
            variant: 'error',
          }),
      },
    )
  }

  function handleQueue(buildId: string) {
    setQueuingId(buildId)
    queueMutation.mutate(buildId, {
      onSuccess: () => toast({ title: 'Build queued' }),
      onError: (error) =>
        toast({
          title: 'Queue build failed',
          description: error instanceof ApiError ? error.message : undefined,
          variant: 'error',
        }),
      onSettled: () => setQueuingId(null),
    })
  }

  function handleCancel(buildId: string) {
    setCancellingId(buildId)
    cancelMutation.mutate(buildId, {
      onSuccess: () => toast({ title: 'Build cancelled' }),
      onError: (error) =>
        toast({
          title: 'Cancel failed',
          description: error instanceof ApiError ? error.message : undefined,
          variant: 'error',
        }),
      onSettled: () => setCancellingId(null),
    })
  }

  function handleToggleExpand(buildId: string) {
    setExpandedBuild(expandedBuildId === buildId ? null : buildId)
  }

  if (partQuery.isLoading) {
    return <Skeleton className="h-48 w-full" data-testid="build-manager-loading" />
  }

  if (partQuery.isError || !partQuery.data) {
    return (
      <p className="text-sm text-red-400" data-testid="build-manager-part-error">
        Unable to load part
      </p>
    )
  }

  return (
    <div className="space-y-6" data-testid="build-manager-page">
      <BuildHeader part={partQuery.data} projectId={projectId} />

      <BuildCreationPanel
        allChunks={chunksQuery.data}
        selectedChunks={selectedChunks}
        onToggle={toggleChunk}
        onSelectAll={handleSelectAll}
        onClear={clearSelection}
        onSelectVcApproved={handleSelectVcApproved}
        onCreate={handleCreate}
        creating={createMutation.isPending}
      />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Existing Builds</h2>
        <BuildList
          builds={buildsQuery.data}
          loading={buildsQuery.isLoading}
          error={buildsQuery.isError}
          projectId={projectId}
          partId={partId}
          jobs={jobsQuery.data}
          events={eventsQuery.data}
          downloadReadyByBuildId={downloadReadyByBuildId}
          expandedBuildId={expandedBuildId}
          onToggleExpand={handleToggleExpand}
          onQueue={handleQueue}
          onCancel={handleCancel}
          queuingId={queuingId}
          cancellingId={cancellingId}
        />
      </section>
    </div>
  )
}
