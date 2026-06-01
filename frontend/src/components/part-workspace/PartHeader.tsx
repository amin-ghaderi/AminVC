import { useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { queryKeys } from '@/hooks/queryKeys'
import type { Part, PartSummary } from '@/types/api'
import { useWorkspaceInvalidation } from '@/hooks/usePartWorkspace'

interface PartHeaderProps {
  part: Part
  summary: PartSummary | undefined
  projectId: string
  partId: string
  selectedChunkId: number | null
}

export function PartHeader({
  part,
  summary,
  projectId,
  partId,
  selectedChunkId,
}: PartHeaderProps) {
  const queryClient = useQueryClient()
  const { refreshAll } = useWorkspaceInvalidation(projectId, partId)

  function handleRefresh() {
    refreshAll(selectedChunkId)
    void queryClient.refetchQueries({
      queryKey: queryKeys.partSummary(projectId, partId),
    })
  }

  return (
    <div
      className="flex flex-col gap-4 border-b border-[var(--color-border)] pb-4"
      data-testid="part-header"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {part.title || part.part_id}
          </h1>
          <p className="text-sm text-[var(--color-muted-foreground)]">
            {part.part_id}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={handleRefresh}>
            Refresh
          </Button>
          <Button type="button" size="sm" disabled className="gap-2">
            Queue Approved For VC
            <Badge variant="outline">Coming Soon</Badge>
          </Button>
        </div>
      </div>
      {summary ? (
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">Narration Ready: {summary.narration_ready}</Badge>
          <Badge variant="outline">
            Narration Approved: {summary.narration_approved}
          </Badge>
          <Badge variant="outline">VC Ready: {summary.vc_ready}</Badge>
          <Badge variant="outline">VC Approved: {summary.vc_approved}</Badge>
          <Badge variant="outline">Failed: {summary.failed}</Badge>
          <Badge variant="outline">Interrupted: {summary.interrupted}</Badge>
        </div>
      ) : null}
    </div>
  )
}
