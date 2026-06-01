import { getBuildLastActivity } from '@/lib/buildActivity'
import type { Build, EventEnvelope } from '@/types/api'

interface BuildDetailsProps {
  build: Build
  events: EventEnvelope[] | undefined
}

export function BuildDetails({ build, events }: BuildDetailsProps) {
  const lastActivity = getBuildLastActivity(build.build_id, events)

  return (
    <div
      className="mt-4 space-y-2 border-t border-[var(--color-border)] pt-4 text-sm"
      data-testid="build-details"
    >
      <p>
        <span className="text-[var(--color-muted-foreground)]">Build ID: </span>
        <span className="font-mono">{build.build_id}</span>
      </p>
      <p>
        <span className="text-[var(--color-muted-foreground)]">Chunks: </span>
        {build.chunks.join(', ')}
      </p>
      <p>
        <span className="text-[var(--color-muted-foreground)]">Output File: </span>
        {build.output_file || '—'}
      </p>
      {build.duration_seconds != null ? (
        <p data-testid="build-duration">
          <span className="text-[var(--color-muted-foreground)]">Duration: </span>
          {Math.round(build.duration_seconds)}s
        </p>
      ) : null}
      <p data-testid="build-last-activity">
        <span className="text-[var(--color-muted-foreground)]">Last Activity: </span>
        {lastActivity ?? '—'}
      </p>
    </div>
  )
}
