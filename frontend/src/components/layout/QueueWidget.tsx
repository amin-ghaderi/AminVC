import { useQueueSnapshot } from '@/hooks/useQueue'
import { Skeleton } from '@/components/ui/skeleton'

export function QueueWidget() {
  const { data, isLoading, isError } = useQueueSnapshot()

  if (isLoading) {
    return <Skeleton className="h-10 w-44" />
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs">
        <span className="text-red-400">Queue unavailable</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs">
      <div className="font-medium">Queue</div>
      <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[var(--color-muted-foreground)]">
        <span>Queued: {data.queued}</span>
        <span>Running: {data.running}</span>
        <span>Failed: {data.failed}</span>
        <span>Completed: {data.completed}</span>
      </div>
    </div>
  )
}
