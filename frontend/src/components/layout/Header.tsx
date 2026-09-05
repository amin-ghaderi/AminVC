import { Link } from 'react-router-dom'

import { AgentStatusWidget } from '@/components/layout/AgentStatusWidget'
import { QueueWidget } from '@/components/layout/QueueWidget'
import { WorkerWidget } from '@/components/layout/WorkerWidget'
import { useUiStore } from '@/store/uiStore'

export function Header() {
  const projectId = useUiStore((s) => s.currentProjectId)
  const projectTitle = useUiStore((s) => s.currentProjectTitle)

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-card)] px-6">
      <div className="flex items-center gap-4">
        <Link to="/projects" className="text-lg font-semibold tracking-tight">
          AminVC
        </Link>
        {projectId ? (
          <div className="text-sm text-[var(--color-muted-foreground)]">
            <span className="text-[var(--color-foreground)]">
              {projectTitle || projectId}
            </span>
            <span className="mx-2">·</span>
            <span>{projectId}</span>
          </div>
        ) : null}
      </div>
      <div className="flex items-center gap-3">
        <AgentStatusWidget />
        <WorkerWidget />
        <QueueWidget />
      </div>
    </header>
  )
}
