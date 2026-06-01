import { formatFileSize } from '@/lib/textStats'

interface AudioPlayerBlockProps {
  src: string
  fileSize: number | null
  state: string
  label: string
}

export function AudioPlayerBlock({
  src,
  fileSize,
  state,
  label,
}: AudioPlayerBlockProps) {
  return (
    <div className="space-y-3 rounded-lg border border-[var(--color-border)] p-4">
      <p className="text-sm font-medium">{label}</p>
      <audio controls className="w-full" src={src} data-testid="audio-player">
        <track kind="captions" />
      </audio>
      <div className="flex flex-wrap gap-4 text-xs text-[var(--color-muted-foreground)]">
        <span>
          File Size: {fileSize !== null ? formatFileSize(fileSize) : '—'}
        </span>
        <span>State: {state || '—'}</span>
      </div>
    </div>
  )
}
