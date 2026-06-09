import { WorkerControlButtons } from '@/components/worker/WorkerControlButtons'
import { useWorkerStatus } from '@/hooks/useWorker'
import { Skeleton } from '@/components/ui/skeleton'

export function WorkerWidget() {
  const { data, isLoading, isError } = useWorkerStatus()

  if (isLoading) {
    return <Skeleton className="h-10 w-36" />
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs">
        <span className="text-red-400">Worker unavailable</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs">
      <div className="font-medium">
        {data.running ? 'Running' : 'Stopped'}
      </div>
      <div className="text-[var(--color-muted-foreground)]">State: {data.state}</div>
      <WorkerControlButtons running={data.running} className="mt-2 flex items-center gap-2" />
    </div>
  )
}
