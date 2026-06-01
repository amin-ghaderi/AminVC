interface WizardHeaderProps {
  projectTitle?: string
}

export function WizardHeader({ projectTitle }: WizardHeaderProps) {
  return (
    <div className="border-b border-[var(--color-border)] pb-4">
      <h1 className="text-2xl font-semibold tracking-tight">Create Part Wizard</h1>
      {projectTitle ? (
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Project: {projectTitle}
        </p>
      ) : null}
    </div>
  )
}
