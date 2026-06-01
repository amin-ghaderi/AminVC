import { Input } from '@/components/ui/input'

interface ChunkSearchProps {
  value: string
  onChange: (value: string) => void
}

export function ChunkSearch({ value, onChange }: ChunkSearchProps) {
  return (
    <Input
      placeholder="Search chunk number or text…"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid="chunk-search"
      className="h-8 text-sm"
    />
  )
}
