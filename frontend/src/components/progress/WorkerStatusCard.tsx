import { Badge } from '@/components/ui/badge'
import type { WorkerStatus } from '@/types/api'

export interface WorkerCardModel {
  id: string
  running: boolean
  state: string
}

interface WorkerStatusCardProps {
  workers: WorkerCardModel[]
}

function formatState(state: string): string {
  const normalized = state.toLowerCase()
  if (normalized.includes('poll')) return 'Polling'
  if (normalized.includes('exec') || normalized.includes('process')) return 'Executing'
  if (normalized === 'idle') return 'Idle'
  return state
}

export function workerFromStatus(status: WorkerStatus, id = 'worker-1'): WorkerCardModel {
  return {
    id,
    running: status.running,
    state: status.state,
  }
}

export function WorkerStatusCard({ workers }: WorkerStatusCardProps) {
  return (
    <div className="space-y-3" data-testid="worker-status-panel">
      <h2 className="text-lg font-semibold">Worker Status</h2>
      <div className="grid gap-3 md:grid-cols-2">
        {workers.map((worker) => (
          <div
            key={worker.id}
            className="rounded-lg border border-[var(--color-border)] p-4"
            data-testid={`worker-card-${worker.id}`}
          >
            <div className="flex items-center justify-between">
              <p className="font-medium">{worker.running ? 'Running' : 'Stopped'}</p>
              <Badge variant="outline">{formatState(worker.state)}</Badge>
            </div>
            <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
              State: {worker.state}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
