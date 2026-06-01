import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { Project } from '@/types/api'

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{project.title || project.project_id}</CardTitle>
        <CardDescription>{project.project_id}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-[var(--color-muted-foreground)]">
          {project.parts.length} part{project.parts.length === 1 ? '' : 's'}
        </p>
      </CardContent>
      <CardFooter>
        <Button asChild size="sm">
          <Link to={`/projects/${encodeURIComponent(project.project_id)}`}>
            Open
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
