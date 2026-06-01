import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { PartCard } from '@/components/parts/PartCard'
import { EmptyState } from '@/components/shared/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { usePartsList } from '@/hooks/useParts'
import { useProject } from '@/hooks/useProjects'
import { useUiStore } from '@/store/uiStore'

export function ProjectDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const projectQuery = useProject(projectId)
  const partsQuery = usePartsList(projectId)
  const setCurrentProject = useUiStore((s) => s.setCurrentProject)

  useEffect(() => {
    if (projectId && projectQuery.data) {
      setCurrentProject(projectId, projectQuery.data.title)
    }
    return () => {
      setCurrentProject(null)
    }
  }, [projectId, projectQuery.data, setCurrentProject])

  const loading = projectQuery.isLoading || partsQuery.isLoading

  return (
    <div className="space-y-6">
      {projectQuery.isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
      ) : projectQuery.isError || !projectQuery.data ? (
        <p className="text-sm text-red-400">Failed to load project.</p>
      ) : (
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {projectQuery.data.title || projectQuery.data.project_id}
          </h1>
          <p className="text-sm text-[var(--color-muted-foreground)]">
            {projectQuery.data.project_id}
          </p>
        </div>
      )}

      <div className="flex justify-end">
        {projectId ? (
          <Button asChild>
            <Link to={`/projects/${encodeURIComponent(projectId)}/parts/new`}>
              + New Part
            </Link>
          </Button>
        ) : null}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : partsQuery.isError ? (
        <p className="text-sm text-red-400">Failed to load parts.</p>
      ) : !partsQuery.data?.length ? (
        <EmptyState
          title="No Parts Yet"
          description="Create Your First Part"
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {partsQuery.data.map((part) => (
            <PartCard key={part.part_id} part={part} />
          ))}
        </div>
      )}
    </div>
  )
}
