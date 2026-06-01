import { Badge } from '@/components/ui/badge'
import type { BuildStatus } from '@/types/api'

const VARIANT: Record<
  BuildStatus,
  'default' | 'outline' | 'secondary'
> = {
  Created: 'outline',
  Queued: 'secondary',
  Running: 'default',
  Completed: 'default',
  Failed: 'outline',
  Cancelled: 'outline',
}

interface StatusBadgeProps {
  status: BuildStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge
      variant={VARIANT[status]}
      data-testid={`build-status-${status.toLowerCase()}`}
    >
      {status}
    </Badge>
  )
}
