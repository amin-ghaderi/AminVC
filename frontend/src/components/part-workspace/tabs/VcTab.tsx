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
import { vcAudioUrl } from '@/api/chunks'
import {
  useApproveVcMutation,
  useQueueVcMutation,
  useRebuildVcMutation,
  useUnapproveVcMutation,
} from '@/hooks/usePartWorkspace'
import type { Chunk, ChunkAssets } from '@/types/api'

interface VcTabProps {
  projectId: string
  partId: string
  chunk: Chunk
  assets: ChunkAssets | undefined
}

export function VcTab({ projectId, partId, chunk, assets }: VcTabProps) {
  const [rebuildOpen, setRebuildOpen] = useState(false)
  const { toast } = useToast()
  const queueMutation = useQueueVcMutation(projectId, partId)
  const approveMutation = useApproveVcMutation(projectId, partId, chunk.chunk_id)
  const unapproveMutation = useUnapproveVcMutation(
    projectId,
    partId,
    chunk.chunk_id,
  )
  const rebuildMutation = useRebuildVcMutation(projectId, partId, chunk.chunk_id)

  const jobBody = {
    project_id: projectId,
    part_id: partId,
    chunk_id: chunk.chunk_id,
  }

  const narrationApproved =
    chunk.state === 'NarrationApproved' || chunk.narration_approved

  if (!assets?.vc_exists) {
    return (
      <div className="space-y-4" data-testid="vc-tab">
        <p className="text-sm text-[var(--color-muted-foreground)]">
          No VC generated yet
        </p>
        <Button
          type="button"
          onClick={() =>
            queueMutation.mutate(jobBody, {
              onSuccess: () => toast({ title: 'VC queued' }),
              onError: (error) => {
                const message =
                  error instanceof ApiError ? error.message : 'Queue failed'
                toast({
                  title:
                    message === 'Narration approval required'
                      ? 'Narration approval required'
                      : 'Queue failed',
                  description: message,
                  variant: 'error',
                })
              },
            })
          }
          disabled={!narrationApproved || queueMutation.isPending}
        >
          Queue VC
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="vc-tab">
      <AudioPlayerBlock
        label="VC"
        src={vcAudioUrl(projectId, partId, chunk.chunk_id)}
        fileSize={assets.vc_size}
        state={chunk.vc.status || chunk.state}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            queueMutation.mutate(jobBody, {
              onSuccess: () => toast({ title: 'VC queued' }),
              onError: (error) => {
                const message =
                  error instanceof ApiError ? error.message : 'Queue failed'
                toast({
                  title:
                    message.toLowerCase().includes('approval')
                      ? 'Narration approval required'
                      : 'Queue failed',
                  description: message,
                  variant: 'error',
                })
              },
            })
          }
          disabled={!narrationApproved || queueMutation.isPending}
        >
          Queue VC
        </Button>
        <Button
          type="button"
          onClick={() =>
            approveMutation.mutate(undefined, {
              onSuccess: () => toast({ title: 'VC approved' }),
              onError: (error) =>
                toast({
                  title: 'Approve failed',
                  description:
                    error instanceof ApiError ? error.message : undefined,
                  variant: 'error',
                }),
            })
          }
          disabled={chunk.state !== 'VCReady' || approveMutation.isPending}
        >
          Approve VC
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            unapproveMutation.mutate(undefined, {
              onSuccess: () => toast({ title: 'VC unapproved' }),
            })
          }
          disabled={chunk.state !== 'VCApproved' || unapproveMutation.isPending}
        >
          Unapprove VC
        </Button>
        <Button type="button" variant="outline" onClick={() => setRebuildOpen(true)}>
          Rebuild VC
        </Button>
      </div>
      <Dialog open={rebuildOpen} onOpenChange={setRebuildOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rebuild VC?</DialogTitle>
            <DialogDescription>
              This will invalidate existing VC output. Continue?
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
                    toast({ title: 'VC rebuild requested' })
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
