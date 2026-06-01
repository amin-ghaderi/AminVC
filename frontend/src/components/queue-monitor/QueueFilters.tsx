import { cn } from '@/lib/utils'
import type { QueueMonitorFilter } from '@/types/api'

const FILTERS: { id: QueueMonitorFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'narration', label: 'Narration' },
  { id: 'vc', label: 'VC' },
  { id: 'build', label: 'Build' },
]

interface QueueFiltersProps {
  value: QueueMonitorFilter
  onChange: (value: QueueMonitorFilter) => void
}

export function QueueFilters({ value, onChange }: QueueFiltersProps) {
  return (
    <div className="flex flex-wrap gap-1" data-testid="queue-filters">
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
