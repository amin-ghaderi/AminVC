import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { deleteReferenceAudio, referenceAudioUrl, uploadReferenceAudio } from '@/api/reference'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/shared/ToastProvider'
import { queryKeys } from '@/hooks/queryKeys'
import type { Part } from '@/types/api'

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

interface ReferenceVoicePanelProps {
  projectId: string
  partId: string
  part: Part
}

export function ReferenceVoicePanel({
  projectId,
  partId,
  part,
}: ReferenceVoicePanelProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [busy, setBusy] = useState(false)

  const ready = part.reference_audio.exists

  async function invalidatePart() {
    await queryClient.invalidateQueries({ queryKey: ['part', projectId, partId] })
  }

  async function handleFile(file: File) {
    setBusy(true)
    try {
      await uploadReferenceAudio(projectId, partId, file)
      await invalidatePart()
      toast({ title: ready ? 'Reference voice replaced' : 'Reference voice uploaded' })
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : 'Upload failed'
      toast({ title: 'Upload failed', description: message, variant: 'error' })
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleDelete() {
    setBusy(true)
    try {
      await deleteReferenceAudio(projectId, partId)
      await invalidatePart()
      toast({ title: 'Reference voice deleted' })
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : 'Delete failed'
      toast({ title: 'Delete failed', description: message, variant: 'error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid="reference-voice-panel"
    >
      <h2 className="text-lg font-semibold">Reference Voice</h2>
      <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
        Status:{' '}
        <span data-testid="reference-voice-status">
          {ready ? 'Ready' : 'Missing'}
        </span>
      </p>

      {ready ? (
        <div className="mt-3 space-y-3">
          <div className="text-sm">
            <p data-testid="reference-voice-filename">
              {part.reference_audio.path ?? 'reference.wav'}
            </p>
            {part.reference_audio.size_bytes != null ? (
              <p
                className="text-[var(--color-muted-foreground)]"
                data-testid="reference-voice-size"
              >
                {formatBytes(part.reference_audio.size_bytes)}
              </p>
            ) : null}
          </div>
          <audio
            controls
            className="w-full max-w-md"
            src={referenceAudioUrl(projectId, partId)}
            data-testid="reference-voice-preview"
          />
          <div className="flex flex-wrap gap-2">
            <input
              ref={inputRef}
              type="file"
              accept="audio/wav,.wav"
              className="hidden"
              data-testid="reference-voice-file-input"
              onChange={(event) => {
                const file = event.target.files?.[0]
                if (file) void handleFile(file)
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => inputRef.current?.click()}
              data-testid="reference-voice-replace"
            >
              Replace
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={busy}
              onClick={() => void handleDelete()}
              data-testid="reference-voice-delete"
            >
              Delete
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-3">
          <input
            ref={inputRef}
            type="file"
            accept="audio/wav,.wav"
            className="hidden"
            data-testid="reference-voice-file-input"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void handleFile(file)
            }}
          />
          <Button
            type="button"
            size="sm"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
            data-testid="reference-voice-upload"
          >
            Upload WAV
          </Button>
        </div>
      )}
    </section>
  )
}
