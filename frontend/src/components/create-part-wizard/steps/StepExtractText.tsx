import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  countCharacters,
  countWords,
  textPreview,
} from '@/lib/textStats'

interface StepExtractTextProps {
  extracting: boolean
  extracted: boolean
  extractedText: string
  onExtract: () => void
  onContinue: () => void
}

export function StepExtractText({
  extracting,
  extracted,
  extractedText,
  onExtract,
  onContinue,
}: StepExtractTextProps) {
  if (!extracted) {
    return (
      <div className="space-y-4" data-testid="step-extract-text">
        <Button type="button" onClick={onExtract} disabled={extracting}>
          {extracting ? 'Extracting…' : 'Extract Text'}
        </Button>
        {extracting ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <p className="text-sm text-[var(--color-muted-foreground)]">Loading…</p>
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="step-extract-results">
      <div className="grid gap-2 text-sm sm:grid-cols-2">
        <p>
          <span className="text-[var(--color-muted-foreground)]">Characters: </span>
          {countCharacters(extractedText)}
        </p>
        <p>
          <span className="text-[var(--color-muted-foreground)]">Words: </span>
          {countWords(extractedText)}
        </p>
      </div>
      <div>
        <p className="mb-2 text-sm font-medium">Preview</p>
        <pre
          className="max-h-48 overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-muted)]/30 p-3 text-sm whitespace-pre-wrap"
          dir="rtl"
          lang="fa"
        >
          {textPreview(extractedText)}
        </pre>
      </div>
      <Button type="button" onClick={onContinue}>
        Continue To Editor
      </Button>
    </div>
  )
}
