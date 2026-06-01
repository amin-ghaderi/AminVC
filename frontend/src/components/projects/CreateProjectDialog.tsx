import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/shared/ToastProvider'
import { useCreateProject } from '@/hooks/useProjects'
import { ApiError } from '@/api/client'

export function CreateProjectDialog() {
  const [open, setOpen] = useState(false)
  const [projectId, setProjectId] = useState('')
  const [title, setTitle] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const { toast } = useToast()
  const createProject = useCreateProject()

  function reset() {
    setProjectId('')
    setTitle('')
    setFieldError(null)
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!projectId.trim() || !title.trim()) {
      setFieldError('Project ID and Title are required.')
      return
    }
    setFieldError(null)
    createProject.mutate(
      { project_id: projectId.trim(), title: title.trim() },
      {
        onSuccess: () => {
          setOpen(false)
          reset()
        },
        onError: (error) => {
          const message =
            error instanceof ApiError
              ? error.message
              : error instanceof TypeError
                ? 'Network Error'
                : 'Create Project Failed'
          toast({
            title: 'Create Project Failed',
            description: message,
            variant: 'error',
          })
        },
      },
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button>+ New Project</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Project</DialogTitle>
          <DialogDescription>Add a new narration project.</DialogDescription>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="project-id">Project ID</Label>
            <Input
              id="project-id"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              placeholder="my-project"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="project-title">Title</Label>
            <Input
              id="project-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="My Project"
            />
          </div>
          {fieldError ? (
            <p className="text-sm text-red-400">{fieldError}</p>
          ) : null}
          <Button type="submit" disabled={createProject.isPending}>
            {createProject.isPending ? 'Creating…' : 'Create'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
