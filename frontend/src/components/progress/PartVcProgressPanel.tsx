import { Skeleton } from '@/components/ui/skeleton'
import { formatEtaSeconds } from '@/lib/formatEta'
import type { PartVcProgressView } from '@/lib/partVcProgress'

interface PartVcProgressPanelProps {
  progress: PartVcProgressView
  isLoading?: boolean
  isError?: boolean
  /** Compact layout for workspace VC tab */
  compact?: boolean
}

export function PartVcProgressPanel({
  progress,
  isLoading,
  isError,
  compact = false,
}: PartVcProgressPanelProps) {
  if (isError) {
    return (
      <p className="text-sm text-red-400" data-testid="part-vc-progress-error">
        Unable to load progress
      </p>
    )
  }

  if (isLoading) {
    return <Skeleton className="h-40 w-full" data-testid="part-vc-progress-loading" />
  }

  const chunkEtaLabel = formatEtaSeconds(progress.currentChunkEtaSeconds)
  const overallEtaLabel = formatEtaSeconds(progress.overallEtaSeconds)

  return (
    <div
      className="space-y-4 rounded-lg border border-[var(--color-border)] p-4"
      data-testid="part-vc-progress-panel"
    >
      {progress.hasActiveProgress ? (
        <section data-testid="part-vc-current-chunk">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
            Current Chunk
          </h3>
          {progress.currentChunkPosition !== null && progress.totalChunks > 0 ? (
            <p className="mt-2 text-base font-medium" data-testid="part-vc-chunk-position">
              Chunk {progress.currentChunkPosition} / {progress.totalChunks}
            </p>
          ) : null}
          {progress.currentChunkId !== null ? (
            <p className="text-sm text-[var(--color-muted-foreground)]" data-testid="part-vc-chunk-id">
              Chunk #{progress.currentChunkId}
            </p>
          ) : null}
          <p className="mt-2 text-sm" data-testid="part-vc-step">
            Step {progress.currentStep} / {progress.totalSteps}
          </p>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]" data-testid="part-vc-step-percent">
            {progress.stepPercent}%
          </p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--color-muted)]">
            <div
              className="h-full bg-[var(--color-primary)] transition-all"
              style={{ width: `${progress.stepPercent}%` }}
              data-testid="part-vc-step-bar"
              role="progressbar"
              aria-valuenow={progress.stepPercent}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <p className="mt-3 text-sm" data-testid="part-vc-chunk-eta">
            <span className="font-medium">Current Chunk ETA</span>
            <br />
            {chunkEtaLabel ?? '—'}
          </p>
        </section>
      ) : (
        <section data-testid="part-vc-current-chunk-empty">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
            Current Chunk
          </h3>
          <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
            No VC conversion currently active
          </p>
        </section>
      )}

      {!compact ? <hr className="border-[var(--color-border)]" /> : null}

      <section data-testid="part-vc-part-progress">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
          Part Progress
        </h3>
        <p className="mt-2 text-base font-medium" data-testid="part-vc-completed">
          {progress.completedChunks} / {progress.totalChunks} Completed
        </p>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]" data-testid="part-vc-overall-percent">
          {progress.progressPercent}%
        </p>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--color-muted)]">
          <div
            className="h-full bg-[var(--color-primary)] transition-all"
            style={{ width: `${progress.progressPercent}%` }}
            data-testid="part-vc-overall-bar"
            role="progressbar"
            aria-valuenow={progress.progressPercent}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </section>

      <section data-testid="part-vc-overall-eta">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
          Overall ETA
        </h3>
        {progress.overallEtaAvailable && overallEtaLabel ? (
          <p className="mt-2 text-base font-medium" data-testid="part-vc-overall-eta-value">
            {overallEtaLabel}
          </p>
        ) : (
          <div
            className="mt-2 text-sm text-[var(--color-muted-foreground)]"
            data-testid="part-vc-overall-eta-learning"
          >
            <p>Learning...</p>
            <p>Need completed VC chunks</p>
          </div>
        )}
      </section>
    </div>
  )
}
