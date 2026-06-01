import { useEffect, useState } from 'react'
import { useBlocker } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface UnsavedChangesGuardProps {
  when: boolean
}

export function UnsavedChangesGuard({ when }: UnsavedChangesGuardProps) {
  const blocker = useBlocker(when)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (blocker.state === 'blocked') {
      setOpen(true)
    }
  }, [blocker.state])

  useEffect(() => {
    if (!when) return
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [when])

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next && blocker.state === 'blocked') {
          blocker.reset()
        }
        setOpen(next)
      }}
    >
      <DialogContent data-testid="unsaved-changes-dialog">
        <DialogHeader>
          <DialogTitle>Unsaved changes</DialogTitle>
          <DialogDescription>
            You have unsaved changes. Leave anyway?
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              if (blocker.state === 'blocked') blocker.reset()
              setOpen(false)
            }}
          >
            Stay
          </Button>
          <Button
            type="button"
            onClick={() => {
              if (blocker.state === 'blocked') blocker.proceed?.()
              setOpen(false)
            }}
          >
            Leave anyway
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
