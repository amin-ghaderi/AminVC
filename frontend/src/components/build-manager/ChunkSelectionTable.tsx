import { Button } from '@/components/ui/button'
import type { Chunk } from '@/types/api'

interface ChunkSelectionTableProps {
  chunks: Chunk[]
  selectedChunks: number[]
  onToggle: (chunkId: number) => void
  onSelectAll: () => void
  onClear: () => void
  onSelectVcApproved: () => void
}

export function ChunkSelectionTable({
  chunks,
  selectedChunks,
  onToggle,
  onSelectAll,
  onClear,
  onSelectVcApproved,
}: ChunkSelectionTableProps) {
  return (
    <div className="space-y-3" data-testid="chunk-selection-table">
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onSelectAll}>
          Select All
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onClear}>
          Clear
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onSelectVcApproved}
        >
          Select VC Approved
        </Button>
      </div>
      <div className="overflow-x-auto rounded-lg border border-[var(--color-border)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-muted)]/40 text-left">
              <th className="px-3 py-2">Select</th>
              <th className="px-3 py-2">Chunk Number</th>
              <th className="px-3 py-2">State</th>
            </tr>
          </thead>
          <tbody>
            {chunks.map((chunk) => (
              <tr
                key={chunk.chunk_id}
                className="border-b border-[var(--color-border)] last:border-0"
                data-testid={`build-chunk-row-${chunk.chunk_id}`}
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selectedChunks.includes(chunk.chunk_id)}
                    onChange={() => onToggle(chunk.chunk_id)}
                    aria-label={`Select chunk ${chunk.chunk_id}`}
                    data-testid={`build-chunk-select-${chunk.chunk_id}`}
                  />
                </td>
                <td className="px-3 py-2">{chunk.chunk_id}</td>
                <td className="px-3 py-2">{chunk.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
