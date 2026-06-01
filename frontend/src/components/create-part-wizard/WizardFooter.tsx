import { Button } from '@/components/ui/button'

interface WizardFooterProps {
  onBack?: () => void
  onNext?: () => void
  backDisabled?: boolean
  nextDisabled?: boolean
  nextLabel?: string
  showBack?: boolean
  showNext?: boolean
}

export function WizardFooter({
  onBack,
  onNext,
  backDisabled,
  nextDisabled,
  nextLabel = 'Next',
  showBack = true,
  showNext = true,
}: WizardFooterProps) {
  return (
    <div className="flex items-center justify-between border-t border-[var(--color-border)] pt-4">
      {showBack ? (
        <Button type="button" variant="outline" onClick={onBack} disabled={backDisabled}>
          Back
        </Button>
      ) : (
        <span />
      )}
      {showNext ? (
        <Button type="button" onClick={onNext} disabled={nextDisabled}>
          {nextLabel}
        </Button>
      ) : (
        <span />
      )}
    </div>
  )
}
