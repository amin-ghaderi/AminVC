import { Label } from '@/components/ui/label'
import { estimateChunkCount } from '@/lib/textStats'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'
import { CHUNK_QUALITY_OPTIONS, type ChunkQuality } from '@/types/api'
import { cn } from '@/lib/utils'

export function StepChunkSettings() {
  const editedText = useCreatePartWizardStore((s) => s.editedText)
  const chunkSize = useCreatePartWizardStore((s) => s.chunkSize)
  const setChunkSize = useCreatePartWizardStore((s) => s.setChunkSize)

  const estimate = estimateChunkCount(editedText.length, chunkSize)

  return (
    <div className="space-y-6" data-testid="step-chunk-settings">
      <div>
        <p className="text-sm font-medium">Chunk Quality</p>
        <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
          Smaller = more chunks · Larger = fewer chunks
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {CHUNK_QUALITY_OPTIONS.map((size) => (
            <button
              key={size}
              type="button"
              className={cn(
                'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                chunkSize === size
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-primary-foreground)]'
                  : 'border-[var(--color-border)] hover:bg-[var(--color-accent)]',
              )}
              onClick={() => setChunkSize(size as ChunkQuality)}
              data-testid={`chunk-size-${size}`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>
      <div className="rounded-lg border border-[var(--color-border)] p-4">
        <Label className="text-sm">Approximate chunk count</Label>
        <p className="mt-2 text-2xl font-semibold" data-testid="chunk-count-estimate">
          {estimate}
        </p>
      </div>
    </div>
  )
}
