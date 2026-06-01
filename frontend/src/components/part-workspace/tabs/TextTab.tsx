import { useEffect, useState } from 'react'

import { PartTextEditor } from '@/components/create-part-wizard/PartTextEditor'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/shared/ToastProvider'
import {
  useRebuildNarrationMutation,
  useSaveChunkTextMutation,
} from '@/hooks/usePartWorkspace'
import { ApiError } from '@/api/client'

interface TextTabProps {
  projectId: string
  partId: string
  chunkId: number
  initialText: string
}

export function TextTab({ projectId, partId, chunkId, initialText }: TextTabProps) {
  const [draft, setDraft] = useState(initialText)
  const [rebuildOpen, setRebuildOpen] = useState(false)
  const { toast } = useToast()
  const saveMutation = useSaveChunkTextMutation(projectId, partId, chunkId)
  const rebuildMutation = useRebuildNarrationMutation(projectId, partId, chunkId)

  useEffect(() => {
    setDraft(initialText)
  }, [initialText, chunkId])

  function handleSave() {
    saveMutation.mutate(draft, {
      onSuccess: () => toast({ title: 'Text saved' }),
      onError: (error) =>
        toast({
          title: 'Save failed',
          description: error instanceof ApiError ? error.message : undefined,
          variant: 'error',
        }),
    })
  }

  function handleRebuild() {
    rebuildMutation.mutate(undefined, {
      onSuccess: () => {
        setRebuildOpen(false)
        toast({ title: 'Narration rebuild requested' })
      },
      onError: (error) =>
        toast({
          title: 'Rebuild failed',
          description: error instanceof ApiError ? error.message : undefined,
          variant: 'error',
        }),
    })
  }

  return (
    <div className="space-y-4" data-testid="text-tab">
      <PartTextEditor content={draft} onChange={setDraft} />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={handleSave}
          disabled={saveMutation.isPending}
        >
          {saveMutation.isPending ? 'Saving…' : 'Save Text'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => setRebuildOpen(true)}
          disabled={rebuildMutation.isPending}
        >
          Rebuild Narration
        </Button>
      </div>
      <Dialog open={rebuildOpen} onOpenChange={setRebuildOpen}>
        <DialogContent data-testid="rebuild-narration-dialog">
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
            <Button type="button" onClick={handleRebuild}>
              Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
