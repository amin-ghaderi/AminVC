import { Skeleton } from '@/components/ui/skeleton'
import { vcProgressPercent } from '@/lib/vcProgress'
import type { VcProgressPayload } from '@/types/api'

interface VcProgressWidgetProps {
  progress: VcProgressPayload | null | undefined
  isLoading: boolean
  isError?: boolean
}

export function VcProgressWidget({
  progress,
  isLoading,
  isError,
}: VcProgressWidgetProps) {
  if (isError) {
    return (
      <p className="text-sm text-red-400" data-testid="vc-progress-error">
        Unable to load events
      </p>
    )
  }

  if (isLoading) {
    return <Skeleton className="h-32 w-full" data-testid="vc-progress-loading" />
  }

  if (!progress) {
    return (
      <div
        className="rounded-lg border border-dashed border-[var(--color-border)] p-6 text-center"
        data-testid="vc-progress-empty"
      >
        <h2 className="text-lg font-semibold">VC Progress</h2>
        <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
          No VC conversion currently active
        </p>
      </div>
    )
  }

  const percent = vcProgressPercent(progress)

  return (
    <div
      className="rounded-lg border border-[var(--color-border)] p-4"
      data-testid="vc-progress-widget"
    >
      <h2 className="text-lg font-semibold">VC Progress</h2>
      <p className="mt-3 text-sm" data-testid="vc-progress-step">
        Step {progress.current_step} / {progress.total_steps}
      </p>
      <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
        Elapsed {Math.round(progress.elapsed_seconds)}s · Remaining{' '}
        {Math.round(progress.estimated_remaining_seconds)}s
      </p>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-[var(--color-muted)]">
        <div
          className="h-full bg-[var(--color-primary)] transition-all"
          style={{ width: `${percent}%` }}
          data-testid="vc-progress-bar"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">{percent}%</p>
    </div>
  )
}
