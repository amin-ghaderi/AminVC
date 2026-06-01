import { Badge } from '@/components/ui/badge'
import { formatChunkNumber } from '@/lib/chunkFilters'
import { cn } from '@/lib/utils'
import type { Chunk } from '@/types/api'

interface ChunkRowProps {
  chunk: Chunk
  selected: boolean
  onSelect: () => void
}

export function ChunkRow({ chunk, selected, onSelect }: ChunkRowProps) {
  return (
    <button
      type="button"
      data-testid={`chunk-row-${chunk.chunk_id}`}
      className={cn(
        'flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left text-sm transition-colors',
        selected
          ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/10'
          : 'border-[var(--color-border)] hover:bg-[var(--color-accent)]',
      )}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono font-medium">{formatChunkNumber(chunk.chunk_id)}</span>
        <span className="text-xs text-[var(--color-muted-foreground)]">
          {chunk.state}
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {chunk.narration_approved ? (
          <Badge variant="outline" className="text-[10px]">
            N approved
          </Badge>
        ) : null}
        {chunk.vc_approved ? (
          <Badge variant="outline" className="text-[10px]">
            VC appr.
          </Badge>
        ) : null}
      </div>
    </button>
  )
}
