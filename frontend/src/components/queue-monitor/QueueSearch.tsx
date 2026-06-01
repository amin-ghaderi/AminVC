import { Input } from '@/components/ui/input'

interface QueueSearchProps {
  value: string
  onChange: (value: string) => void
}

export function QueueSearch({ value, onChange }: QueueSearchProps) {
  return (
    <Input
      placeholder="Search project, part, chunk, job ID…"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid="queue-search"
      className="h-8 text-sm"
    />
  )
}
