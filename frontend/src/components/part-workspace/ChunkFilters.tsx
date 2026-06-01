import { cn } from '@/lib/utils'
import type { ChunkListFilter } from '@/types/api'

const FILTERS: { id: ChunkListFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'narration', label: 'Narration' },
  { id: 'vc', label: 'VC' },
  { id: 'approved', label: 'Approved' },
  { id: 'failed', label: 'Failed' },
  { id: 'interrupted', label: 'Interrupted' },
]

interface ChunkFiltersProps {
  value: ChunkListFilter
  onChange: (filter: ChunkListFilter) => void
}

export function ChunkFilters({ value, onChange }: ChunkFiltersProps) {
  return (
    <div className="flex flex-wrap gap-1" data-testid="chunk-filters">
      {FILTERS.map((item) => (
        <button
          key={item.id}
          type="button"
          className={cn(
            'rounded-md px-2 py-1 text-xs font-medium',
            value === item.id
              ? 'bg-[var(--color-primary)] text-[var(--color-primary-foreground)]'
              : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-accent)]',
          )}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
