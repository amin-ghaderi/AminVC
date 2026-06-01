import { useState } from 'react'

import { AudioPlayerBlock } from '@/components/part-workspace/AudioPlayerBlock'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/shared/ToastProvider'
import { ApiError } from '@/api/client'
import { narrationAudioUrl } from '@/api/chunks'
import {
  useApproveNarrationMutation,
  useQueueNarrationMutation,
  useRebuildNarrationMutation,
  useUnapproveNarrationMutation,
} from '@/hooks/usePartWorkspace'
import type { Chunk, ChunkAssets } from '@/types/api'

interface NarrationTabProps {
  projectId: string
  partId: string
  chunk: Chunk
  assets: ChunkAssets | undefined
}

export function NarrationTab({
  projectId,
  partId,
  chunk,
  assets,
}: NarrationTabProps) {
  const [rebuildOpen, setRebuildOpen] = useState(false)
  const { toast } = useToast()
  const queueMutation = useQueueNarrationMutation(projectId, partId)
  const approveMutation = useApproveNarrationMutation(
    projectId,
    partId,
    chunk.chunk_id,
  )
  const unapproveMutation = useUnapproveNarrationMutation(
    projectId,
    partId,
    chunk.chunk_id,
  )
  const rebuildMutation = useRebuildNarrationMutation(
    projectId,
    partId,
    chunk.chunk_id,
  )

  const jobBody = {
    project_id: projectId,
    part_id: partId,
    chunk_id: chunk.chunk_id,
  }

  if (!assets?.narration_exists) {
    return (
      <div className="space-y-4" data-testid="narration-tab">
        <p className="text-sm text-[var(--color-muted-foreground)]">
          No narration generated yet
        </p>
        <Button
          type="button"
          onClick={() =>
            queueMutation.mutate(jobBody, {
              onSuccess: () => toast({ title: 'Narration queued' }),
              onError: (error) =>
                toast({
                  title: 'Queue failed',
                  description:
                    error instanceof ApiError ? error.message : undefined,
                  variant: 'error',
                }),
            })
          }
          disabled={queueMutation.isPending}
        >
          Queue Narration
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="narration-tab">
      <AudioPlayerBlock
        label="Narration"
        src={narrationAudioUrl(projectId, partId, chunk.chunk_id)}
        fileSize={assets.narration_size}
        state={chunk.narration.status || chunk.state}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            queueMutation.mutate(jobBody, {
              onSuccess: () => toast({ title: 'Narration queued' }),
              onError: (error) =>
                toast({
                  title: 'Queue failed',
                  description:
                    error instanceof ApiError ? error.message : undefined,
                  variant: 'error',
                }),
            })
          }
          disabled={queueMutation.isPending}
        >
          Queue Narration
        </Button>
        <Button
          type="button"
          onClick={() =>
            approveMutation.mutate(undefined, {
              onSuccess: () => toast({ title: 'Narration approved' }),
              onError: (error) =>
                toast({
                  title: 'Approve failed',
                  description:
                    error instanceof ApiError ? error.message : undefined,
                  variant: 'error',
                }),
            })
          }
          disabled={chunk.state !== 'NarrationReady' || approveMutation.isPending}
        >
          Approve Narration
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            unapproveMutation.mutate(undefined, {
              onSuccess: () => toast({ title: 'Narration unapproved' }),
              onError: (error) =>
                toast({
                  title: 'Unapprove failed',
                  description:
                    error instanceof ApiError ? error.message : undefined,
                  variant: 'error',
                }),
            })
          }
          disabled={
            chunk.state !== 'NarrationApproved' || unapproveMutation.isPending
          }
        >
          Unapprove Narration
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => setRebuildOpen(true)}
        >
          Rebuild Narration
        </Button>
      </div>
      <Dialog open={rebuildOpen} onOpenChange={setRebuildOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rebuild narration?</DialogTitle>
            <DialogDescription>
              This will invalidate existing narration and VC outputs. Continue?
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setRebuildOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() =>
                rebuildMutation.mutate(undefined, {
                  onSuccess: () => {
                    setRebuildOpen(false)
                    toast({ title: 'Narration rebuild requested' })
                  },
                })
              }
            >
              Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
