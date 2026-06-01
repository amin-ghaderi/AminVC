import { PartTextEditor } from '@/components/create-part-wizard/PartTextEditor'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'

export function StepEditor() {
  const editedText = useCreatePartWizardStore((s) => s.editedText)
  const setEditedText = useCreatePartWizardStore((s) => s.setEditedText)

  return (
    <div data-testid="step-editor">
      <PartTextEditor
        content={editedText}
        onChange={(text) => setEditedText(text, true)}
      />
    </div>
  )
}
