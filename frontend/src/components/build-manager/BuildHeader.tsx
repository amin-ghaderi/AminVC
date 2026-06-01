import { Link } from 'react-router-dom'

import type { Part } from '@/types/api'

interface BuildHeaderProps {
  part: Part
  projectId: string
}

export function BuildHeader({ part, projectId }: BuildHeaderProps) {
  return (
    <div
      className="flex flex-col gap-4 border-b border-[var(--color-border)] pb-4"
      data-testid="build-header"
    >
      <Link
        to={`/projects/${projectId}/parts/${part.part_id}`}
        className="text-sm text-[var(--color-muted-foreground)] hover:underline"
      >
        ← Back to workspace
      </Link>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {part.title || part.part_id}
        </h1>
        <p
          className="text-sm text-[var(--color-muted-foreground)]"
          data-testid="build-header-part-id"
        >
          {part.part_id}
        </p>
      </div>
    </div>
  )
}
