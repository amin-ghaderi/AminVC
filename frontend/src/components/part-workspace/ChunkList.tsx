import { ChunkRow } from '@/components/part-workspace/ChunkRow'
import type { Chunk } from '@/types/api'

interface ChunkListProps {
  chunks: Chunk[]
  selectedChunkId: number | null
  onSelect: (chunkId: number) => void
}

export function ChunkList({ chunks, selectedChunkId, onSelect }: ChunkListProps) {
  if (!chunks.length) {
    return (
      <p className="text-sm text-[var(--color-muted-foreground)]">No chunks match.</p>
    )
  }

  return (
    <div className="flex flex-col gap-2" data-testid="chunk-list">
      {chunks.map((chunk) => (
        <ChunkRow
          key={chunk.chunk_id}
          chunk={chunk}
          selected={selectedChunkId === chunk.chunk_id}
          onSelect={() => onSelect(chunk.chunk_id)}
        />
      ))}
    </div>
  )
}
