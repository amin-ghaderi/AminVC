import { HistoryTab } from '@/components/part-workspace/tabs/HistoryTab'
import { NarrationTab } from '@/components/part-workspace/tabs/NarrationTab'
import { TextTab } from '@/components/part-workspace/tabs/TextTab'
import { VcTab } from '@/components/part-workspace/tabs/VcTab'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  useChunkAssetsQuery,
  useChunkQuery,
  useRecentEventsQuery,
} from '@/hooks/usePartWorkspace'
import { usePartWorkspaceStore } from '@/store/partWorkspaceStore'

interface ChunkDetailsProps {
  projectId: string
  partId: string
  chunkId: number | null
}

export function ChunkDetails({ projectId, partId, chunkId }: ChunkDetailsProps) {
  const activeTab = usePartWorkspaceStore((s) => s.activeTab)
  const setActiveTab = usePartWorkspaceStore((s) => s.setActiveTab)

  const chunkQuery = useChunkQuery(projectId, partId, chunkId)
  const assetsQuery = useChunkAssetsQuery(projectId, partId, chunkId)
  const eventsQuery = useRecentEventsQuery()

  if (chunkId === null) {
    return (
      <div
        className="flex h-full min-h-[320px] items-center justify-center rounded-lg border border-dashed border-[var(--color-border)]"
        data-testid="chunk-details-empty"
      >
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Select a chunk
        </p>
      </div>
    )
  }

  if (chunkQuery.isLoading) {
    return <Skeleton className="h-80 w-full" />
  }

  if (chunkQuery.isError || !chunkQuery.data) {
    return (
      <p className="text-sm text-red-400">Failed to load chunk details.</p>
    )
  }

  const chunk = chunkQuery.data

  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid="chunk-details"
    >
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="text">Text</TabsTrigger>
          <TabsTrigger value="narration">Narration</TabsTrigger>
          <TabsTrigger value="vc">VC</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>
        <TabsContent value="text">
          <TextTab
            projectId={projectId}
            partId={partId}
            chunkId={chunk.chunk_id}
            initialText={chunk.text}
          />
        </TabsContent>
        <TabsContent value="narration">
          <NarrationTab
            projectId={projectId}
            partId={partId}
            chunk={chunk}
            assets={assetsQuery.data}
          />
        </TabsContent>
        <TabsContent value="vc">
          <VcTab
            projectId={projectId}
            partId={partId}
            chunk={chunk}
            assets={assetsQuery.data}
          />
        </TabsContent>
        <TabsContent value="history">
          <HistoryTab
            projectId={projectId}
            partId={partId}
            chunkId={chunk.chunk_id}
            events={eventsQuery.data}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
