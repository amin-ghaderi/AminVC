import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { StepCreateChunks } from '@/components/create-part-wizard/steps/StepCreateChunks'
import { StepChunkSettings } from '@/components/create-part-wizard/steps/StepChunkSettings'
import { StepEditor } from '@/components/create-part-wizard/steps/StepEditor'
import { StepExtractText } from '@/components/create-part-wizard/steps/StepExtractText'
import { StepPartInfo } from '@/components/create-part-wizard/steps/StepPartInfo'
import { StepUploadPdf } from '@/components/create-part-wizard/steps/StepUploadPdf'
import { StepIndicator } from '@/components/create-part-wizard/StepIndicator'
import { UnsavedChangesGuard } from '@/components/create-part-wizard/UnsavedChangesGuard'
import { WizardFooter } from '@/components/create-part-wizard/WizardFooter'
import { WizardHeader } from '@/components/create-part-wizard/WizardHeader'
import { useToast } from '@/components/shared/ToastProvider'
import {
  useCreateChunksMutation,
  useCreatePartMutation,
  useExtractTextMutation,
  useUploadPdfMutation,
} from '@/hooks/useCreatePartWizardMutations'
import { queryKeys } from '@/hooks/queryKeys'
import { useProject } from '@/hooks/useProjects'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'

export function CreatePartWizardPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const projectQuery = useProject(projectId)

  const step = useCreatePartWizardStore((s) => s.step)
  const partId = useCreatePartWizardStore((s) => s.partId)
  const title = useCreatePartWizardStore((s) => s.title)
  const uploadedFile = useCreatePartWizardStore((s) => s.uploadedFile)
  const pdfUploaded = useCreatePartWizardStore((s) => s.pdfUploaded)
  const extractedText = useCreatePartWizardStore((s) => s.extractedText)
  const editedText = useCreatePartWizardStore((s) => s.editedText)
  const textDirty = useCreatePartWizardStore((s) => s.textDirty)
  const chunkSize = useCreatePartWizardStore((s) => s.chunkSize)
  const chunksCreated = useCreatePartWizardStore((s) => s.chunksCreated)
  const setStep = useCreatePartWizardStore((s) => s.setStep)
  const setPartInfo = useCreatePartWizardStore((s) => s.setPartInfo)
  const setPdfUploaded = useCreatePartWizardStore((s) => s.setPdfUploaded)
  const setExtractedText = useCreatePartWizardStore((s) => s.setExtractedText)
  const setEditedText = useCreatePartWizardStore((s) => s.setEditedText)
  const setChunksCreated = useCreatePartWizardStore((s) => s.setChunksCreated)
  const reset = useCreatePartWizardStore((s) => s.reset)

  const [fieldError, setFieldError] = useState<string | null>(null)
  const [extractDone, setExtractDone] = useState(false)

  const createPartMutation = useCreatePartMutation(projectId ?? '')
  const uploadMutation = useUploadPdfMutation(projectId ?? '', partId)
  const extractMutation = useExtractTextMutation(projectId ?? '', partId)
  const chunksMutation = useCreateChunksMutation(projectId ?? '', partId)

  useEffect(() => {
    reset()
    setExtractDone(false)
    return () => reset()
  }, [projectId, reset])

  const showToast = useCallback(
    (title: string, error: unknown) => {
      const description =
        error instanceof ApiError
          ? error.message
          : error instanceof TypeError
            ? 'Network Error'
            : undefined
      toast({ title, description, variant: 'error' })
    },
    [toast],
  )

  const handleStep1Next = () => {
    if (!partId.trim() || !title.trim()) {
      setFieldError('Part ID and Title are required.')
      return
    }
    setFieldError(null)
    createPartMutation.mutate(
      { part_id: partId.trim(), title: title.trim() },
      {
        onSuccess: (part) => {
          setPartInfo(part.part_id, part.title)
          setStep(2)
        },
        onError: (error) => showToast('Create Part Failed', error),
      },
    )
  }

  const handleUpload = () => {
    if (!uploadedFile) return
    uploadMutation.mutate(uploadedFile, {
      onSuccess: () => setPdfUploaded(true),
      onError: (error) => showToast('Upload failed', error),
    })
  }

  const handleExtract = () => {
    extractMutation.mutate(undefined, {
      onSuccess: (data) => {
        setExtractedText(data.text)
        setEditedText(data.text, false)
        setExtractDone(true)
      },
      onError: (error) => showToast('Extraction failed', error),
    })
  }

  const handleCreateChunks = () => {
    chunksMutation.mutate(
      { text: editedText, chunk_size: chunkSize },
      {
        onSuccess: (data) => {
          setChunksCreated(data.chunks_created)
          void queryClient.invalidateQueries({
            queryKey: queryKeys.parts.list(projectId!),
          })
        },
        onError: (error) => showToast('Chunk creation failed', error),
      },
    )
  }

  const busy =
    createPartMutation.isPending ||
    uploadMutation.isPending ||
    extractMutation.isPending ||
    chunksMutation.isPending

  const success = chunksCreated !== null

  if (!projectId) {
    return <p className="text-sm text-red-400">Missing project.</p>
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <UnsavedChangesGuard when={textDirty && step >= 4 && !success} />
      <WizardHeader projectTitle={projectQuery.data?.title} />
      <StepIndicator currentStep={step} />

      <div className="min-h-[280px] rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-6">
        {step === 1 && <StepPartInfo fieldError={fieldError} />}
        {step === 2 && (
          <StepUploadPdf
            onUpload={handleUpload}
            uploading={uploadMutation.isPending}
            uploadError={
              uploadMutation.isError
                ? uploadMutation.error instanceof ApiError
                  ? uploadMutation.error.message
                  : 'Upload failed'
                : null
            }
          />
        )}
        {step === 3 && (
          <StepExtractText
            extracting={extractMutation.isPending}
            extracted={extractDone}
            extractedText={extractedText}
            onExtract={handleExtract}
            onContinue={() => setStep(4)}
          />
        )}
        {step === 4 && <StepEditor />}
        {step === 5 && <StepChunkSettings />}
        {step === 6 && (
          <StepCreateChunks
            projectId={projectId}
            creating={chunksMutation.isPending}
            success={success}
            chunksCreated={chunksCreated}
            onCreate={handleCreateChunks}
          />
        )}
      </div>

      {!success && step < 6 ? (
        <WizardFooter
          showBack={step > 1}
          backDisabled={busy}
          onBack={() => setStep(step - 1)}
          onNext={() => {
            if (step === 1) handleStep1Next()
            else if (step === 2) setStep(3)
            else if (step === 4) setStep(5)
            else if (step === 5) setStep(6)
          }}
          nextDisabled={
            busy ||
            (step === 1 && createPartMutation.isPending) ||
            (step === 2 && !pdfUploaded) ||
            (step === 3 && !extractDone)
          }
          nextLabel={step === 1 && createPartMutation.isPending ? 'Creating…' : 'Next'}
          showNext={step !== 3}
        />
      ) : null}

      {step === 1 && !success ? null : step === 6 && success ? (
        <div className="flex justify-start">
          <button
            type="button"
            className="text-sm text-[var(--color-muted-foreground)] hover:underline"
            onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}`)}
          >
            Cancel wizard
          </button>
        </div>
      ) : (
        <div className="flex justify-start">
          <button
            type="button"
            className="text-sm text-[var(--color-muted-foreground)] hover:underline"
            disabled={busy}
            data-testid="wizard-cancel"
            onClick={() => {
              if (textDirty && step >= 4) {
                const leave = window.confirm(
                  'You have unsaved changes.\nLeave anyway?',
                )
                if (!leave) return
              }
              navigate(`/projects/${encodeURIComponent(projectId)}`)
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
