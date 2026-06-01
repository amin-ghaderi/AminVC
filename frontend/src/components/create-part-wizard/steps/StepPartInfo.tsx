import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'

interface StepPartInfoProps {
  fieldError: string | null
}

export function StepPartInfo({ fieldError }: StepPartInfoProps) {
  const partId = useCreatePartWizardStore((s) => s.partId)
  const title = useCreatePartWizardStore((s) => s.title)
  const setPartInfo = useCreatePartWizardStore((s) => s.setPartInfo)

  return (
    <div className="space-y-4" data-testid="step-part-info">
      <div className="grid gap-2">
        <Label htmlFor="wizard-part-id">Part ID</Label>
        <Input
          id="wizard-part-id"
          value={partId}
          onChange={(e) => setPartInfo(e.target.value, title)}
          placeholder="part-01"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="wizard-part-title">Title</Label>
        <Input
          id="wizard-part-title"
          value={title}
          onChange={(e) => setPartInfo(partId, e.target.value)}
          placeholder="Chapter 1"
        />
      </div>
      {fieldError ? <p className="text-sm text-red-400">{fieldError}</p> : null}
    </div>
  )
}
