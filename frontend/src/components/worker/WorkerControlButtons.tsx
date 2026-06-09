import { Button } from '@/components/ui/button'
import { useStartWorker, useStopWorker } from '@/hooks/useWorker'

interface WorkerControlButtonsProps {
  running: boolean
  size?: 'default' | 'sm'
  className?: string
}

export function WorkerControlButtons({
  running,
  size = 'sm',
  className,
}: WorkerControlButtonsProps) {
  const startMutation = useStartWorker()
  const stopMutation = useStopWorker()
  const pending = startMutation.isPending || stopMutation.isPending

  return (
    <div className={className ?? 'flex items-center gap-2'}>
      <Button
        type="button"
        size={size}
        variant="default"
        disabled={running || pending}
        onClick={() => startMutation.mutate()}
        data-testid="worker-start-button"
      >
        {startMutation.isPending ? 'Starting…' : 'Start'}
      </Button>
      <Button
        type="button"
        size={size}
        variant="outline"
        disabled={!running || pending}
        onClick={() => stopMutation.mutate()}
        data-testid="worker-stop-button"
      >
        {stopMutation.isPending ? 'Stopping…' : 'Stop'}
      </Button>
    </div>
  )
}
