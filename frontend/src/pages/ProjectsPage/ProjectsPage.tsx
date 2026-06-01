import { CreateProjectDialog } from '@/components/projects/CreateProjectDialog'
import { ProjectCard } from '@/components/projects/ProjectCard'
import { EmptyState } from '@/components/shared/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { useProjectsList } from '@/hooks/useProjects'
import { useUiStore } from '@/store/uiStore'
import { useEffect } from 'react'

export function ProjectsPage() {
  const { data, isLoading, isError } = useProjectsList()
  const setCurrentProject = useUiStore((s) => s.setCurrentProject)

  useEffect(() => {
    setCurrentProject(null)
  }, [setCurrentProject])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-[var(--color-muted-foreground)]">
            Manage narration projects
          </p>
        </div>
        <CreateProjectDialog />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-sm text-red-400">Failed to load projects.</p>
      ) : !data?.length ? (
        <EmptyState
          title="No Projects Yet"
          description="Create Your First Project"
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((project) => (
            <ProjectCard key={project.project_id} project={project} />
          ))}
        </div>
      )}
    </div>
  )
}
