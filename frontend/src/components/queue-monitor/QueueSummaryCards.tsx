import type { QueueSnapshot } from '@/types/api'

interface QueueSummaryCardsProps {
  snapshot: QueueSnapshot | undefined
}

const cards = [
  { key: 'queued' as const, label: 'Queued' },
  { key: 'running' as const, label: 'Running' },
  { key: 'completed' as const, label: 'Completed' },
  { key: 'failed' as const, label: 'Failed' },
  { key: 'cancelled' as const, label: 'Cancelled' },
]

export function QueueSummaryCards({ snapshot }: QueueSummaryCardsProps) {
  return (
    <div
      className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"
      data-testid="queue-summary-cards"
    >
      {cards.map((card) => (
        <div
          key={card.key}
          className="rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-4"
          data-testid={`queue-summary-${card.key}`}
        >
          <p className="text-xs text-[var(--color-muted-foreground)]">{card.label}</p>
          <p className="mt-1 text-2xl font-semibold">{snapshot?.[card.key] ?? '—'}</p>
        </div>
      ))}
    </div>
  )
}
