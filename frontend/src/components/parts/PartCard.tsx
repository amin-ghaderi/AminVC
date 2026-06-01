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
import type { Part } from '@/types/api'

interface PartCardProps {
  part: Part
}

export function PartCard({ part }: PartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{part.title || part.part_id}</CardTitle>
        <CardDescription>{part.part_id}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-[var(--color-muted-foreground)]">
          State: {part.state || '—'}
        </p>
      </CardContent>
      <CardFooter>
        <Button asChild size="sm">
          <Link
            to={`/projects/${encodeURIComponent(part.project_id)}/parts/${encodeURIComponent(part.part_id)}`}
          >
            Open
          </Link>
        </Button>
      </CardFooter>
    </Card>
  )
}
