import { Skeleton } from '@/components/ui/skeleton'
import { formatEtaClock } from '@/lib/formatEta'
import type { PartVcProgressView } from '@/lib/partVcProgress'

interface PartVcProgressPanelProps {
  progress: PartVcProgressView
  isLoading?: boolean
  isError?: boolean
  /** Compact layout for workspace VC tab */
  compact?: boolean
}

function Divider() {
  return <hr className="border-[var(--color-border)]" />
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
    return <Skeleton className="h-48 w-full" data-testid="part-vc-progress-loading" />
  }

  const segmentEtaLabel = formatEtaClock(progress.segmentEtaSeconds)
  const chunkEtaLabel = progress.chunkEtaLearning
    ? null
    : formatEtaClock(progress.chunkEtaSeconds)
  const overallEtaLabel = formatEtaClock(progress.overallEtaSeconds)

  if (!progress.hasActiveProgress) {
    return (
      <div
        className="space-y-4 rounded-lg border border-[var(--color-border)] p-4"
        data-testid="part-vc-progress-panel"
      >
        <section data-testid="part-vc-inactive">
          <p className="text-sm text-[var(--color-muted-foreground)]">
            No VC conversion currently active
          </p>
        </section>
        {!compact ? (
          <>
            <Divider />
            <section data-testid="part-vc-narration-chunk">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
                Narration Chunk
              </h3>
              <p className="mt-2 text-base font-medium" data-testid="part-vc-narration-position">
                {progress.completedChunks} / {progress.totalChunks}
              </p>
            </section>
          </>
        ) : null}
      </div>
    )
  }

  return (
    <div
      className="space-y-4 rounded-lg border border-[var(--color-border)] p-4"
      data-testid="part-vc-progress-panel"
    >
      <section data-testid="part-vc-narration-chunk">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
          Narration Chunk
        </h3>
        <p className="mt-2 text-base font-medium" data-testid="part-vc-narration-position">
          {progress.narrationChunkPosition ?? progress.completedChunks + 1} /{' '}
          {progress.totalChunks}
        </p>
      </section>

      <Divider />

      {progress.hasSegmentProgress &&
      progress.segmentIndex !== null &&
      progress.segmentTotal !== null ? (
        <section data-testid="part-vc-segment">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
            VC Segment
          </h3>
          <p className="mt-2 text-base font-medium" data-testid="part-vc-segment-position">
            {progress.segmentIndex} / {progress.segmentTotal}
          </p>
        </section>
      ) : null}

      {progress.hasSegmentProgress ? <Divider /> : null}

      <section data-testid="part-vc-diffusion-step">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-muted-foreground)]">
          Diffusion Step
        </h3>
        <p className="mt-2 text-base font-medium" data-testid="part-vc-step">
          {progress.currentStep} / {progress.totalSteps}
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
      </section>

      <Divider />

      <section className="space-y-2" data-testid="part-vc-etas">
        <div className="flex justify-between text-sm" data-testid="part-vc-segment-eta">
          <span className="font-medium">Segment ETA</span>
          <span>{segmentEtaLabel ?? '—'}</span>
        </div>
        <div className="flex justify-between text-sm" data-testid="part-vc-chunk-eta">
          <span className="font-medium">Chunk ETA</span>
          {progress.chunkEtaLearning ? (
            <span
              className="text-[var(--color-muted-foreground)]"
              data-testid="part-vc-chunk-eta-learning"
            >
              Learning...
            </span>
          ) : (
            <span>{chunkEtaLabel ?? '—'}</span>
          )}
        </div>
        <div className="flex justify-between text-sm" data-testid="part-vc-overall-eta">
          <span className="font-medium">Part ETA</span>
          {progress.overallEtaAvailable && overallEtaLabel ? (
            <span data-testid="part-vc-overall-eta-value">{overallEtaLabel}</span>
          ) : (
            <span
              className="text-[var(--color-muted-foreground)]"
              data-testid="part-vc-overall-eta-learning"
            >
              Learning...
            </span>
          )}
        </div>
      </section>

      {!compact ? (
        <>
          <Divider />
          <section data-testid="part-vc-part-summary">
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Part completion: {progress.completedChunks} / {progress.totalChunks} (
              {progress.progressPercent}%)
            </p>
          </section>
        </>
      ) : null}
    </div>
  )
}
