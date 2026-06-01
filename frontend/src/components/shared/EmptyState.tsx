interface EmptyStateProps {
  title: string
  description: string
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] px-6 py-16 text-center">
      <h2 className="text-lg font-medium">{title}</h2>
      <p className="mt-2 max-w-sm text-sm text-[var(--color-muted-foreground)]">
        {description}
      </p>
    </div>
  )
}
