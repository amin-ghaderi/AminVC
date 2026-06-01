import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface CreateBuildFormProps {
  selectedCount: number
  onSubmit: (name: string) => void
  submitting: boolean
}

export function CreateBuildForm({
  selectedCount,
  onSubmit,
  submitting,
}: CreateBuildFormProps) {
  const [name, setName] = useState('')

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed || selectedCount === 0) {
      return
    }
    onSubmit(trimmed)
    setName('')
  }

  return (
    <form
      className="flex flex-col gap-3 sm:flex-row sm:items-end"
      onSubmit={handleSubmit}
      data-testid="create-build-form"
    >
      <div className="flex-1 space-y-2">
        <Label htmlFor="build-name">Build Name</Label>
        <Input
          id="build-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Final Audiobook"
          required
          data-testid="build-name-input"
        />
      </div>
      <Button
        type="submit"
        disabled={submitting || selectedCount === 0 || !name.trim()}
        data-testid="create-build-submit"
      >
        Create Build
      </Button>
    </form>
  )
}
