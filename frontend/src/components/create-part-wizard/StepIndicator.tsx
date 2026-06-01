import { cn } from '@/lib/utils'

const STEP_LABELS = [
  'Part Info',
  'Upload PDF',
  'Extract Text',
  'Editor',
  'Chunk Settings',
  'Create Chunks',
]

interface StepIndicatorProps {
  currentStep: number
}

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <ol
      className="flex flex-wrap gap-2"
      aria-label="Wizard steps"
      data-testid="step-indicator"
    >
      {STEP_LABELS.map((label, index) => {
        const stepNumber = index + 1
        const active = stepNumber === currentStep
        const done = stepNumber < currentStep
        return (
          <li
            key={label}
            className={cn(
              'rounded-full border px-3 py-1 text-xs font-medium',
              active &&
                'border-[var(--color-primary)] bg-[var(--color-primary)] text-[var(--color-primary-foreground)]',
              done &&
                !active &&
                'border-[var(--color-border)] text-[var(--color-muted-foreground)]',
              !active &&
                !done &&
                'border-[var(--color-border)] text-[var(--color-muted-foreground)] opacity-60',
            )}
          >
            {stepNumber}. {label}
          </li>
        )
      })}
    </ol>
  )
}
