import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

interface StepCreateChunksProps {
  projectId: string
  partId: string
  creating: boolean
  success: boolean
  chunksCreated: number | null
  onCreate: () => void
}

export function StepCreateChunks({
  projectId,
  partId,
  creating,
  success,
  chunksCreated,
  onCreate,
}: StepCreateChunksProps) {
  if (success && chunksCreated !== null) {
    return (
      <div className="space-y-6 text-center" data-testid="step-success">
        <div>
          <h2 className="text-xl font-semibold">Part Created Successfully</h2>
          <p className="mt-2 text-[var(--color-muted-foreground)]">
            Chunks Created: {chunksCreated}
          </p>
        </div>
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button asChild>
            <Link
              to={`/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}`}
            >
              Open Part Workspace
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/projects/${encodeURIComponent(projectId)}`}>
              Back To Project
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="step-create-chunks">
      <p className="text-sm text-[var(--color-muted-foreground)]">
        Save the part by creating chunks from your edited text.
      </p>
      <Button type="button" onClick={onCreate} disabled={creating}>
        {creating ? 'Creating Chunks…' : 'Create Chunks'}
      </Button>
    </div>
  )
}
