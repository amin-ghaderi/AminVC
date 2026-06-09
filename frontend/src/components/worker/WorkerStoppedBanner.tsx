import { Button } from '@/components/ui/button'
import { useWorkerStatusMonitor } from '@/hooks/useQueueMonitor'
import { useStartWorker } from '@/hooks/useWorker'

export function WorkerStoppedBanner() {
  const workerQuery = useWorkerStatusMonitor()
  const startMutation = useStartWorker()

  if (workerQuery.isLoading || workerQuery.isError || !workerQuery.data) {
    return null
  }

  if (workerQuery.data.running) {
    return null
  }

  return (
    <div
      className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3"
      data-testid="worker-stopped-banner"
      role="status"
    >
      <p className="font-medium text-amber-100">Worker is stopped.</p>
      <p className="mt-1 text-sm text-amber-100/80">
        Queued jobs will not execute.
      </p>
      <Button
        type="button"
        size="sm"
        className="mt-3"
        disabled={startMutation.isPending}
        onClick={() => startMutation.mutate()}
        data-testid="worker-banner-start-button"
      >
        {startMutation.isPending ? 'Starting…' : 'Start Worker'}
      </Button>
    </div>
  )
}
