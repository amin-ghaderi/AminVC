import { useRef } from 'react'

import { Button } from '@/components/ui/button'
import { formatFileSize } from '@/lib/textStats'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'

interface StepUploadPdfProps {
  onUpload: () => void
  uploading: boolean
  uploadError: string | null
}

export function StepUploadPdf({
  onUpload,
  uploading,
  uploadError,
}: StepUploadPdfProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const uploadedFile = useCreatePartWizardStore((s) => s.uploadedFile)
  const pdfUploaded = useCreatePartWizardStore((s) => s.pdfUploaded)
  const setUploadedFile = useCreatePartWizardStore((s) => s.setUploadedFile)

  function handleFile(file: File | undefined) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return
    }
    setUploadedFile(file)
  }

  return (
    <div className="space-y-4" data-testid="step-upload-pdf">
      <div
        className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-[var(--color-border)] px-6 py-12 text-center"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          handleFile(e.dataTransfer.files[0])
        }}
      >
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Drop PDF here
        </p>
        <p className="my-2 text-xs text-[var(--color-muted-foreground)]">or</p>
        <Button
          type="button"
          variant="outline"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
        >
          Browse File
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {uploadedFile ? (
        <div className="rounded-lg border border-[var(--color-border)] p-4 text-sm">
          <p>
            <span className="text-[var(--color-muted-foreground)]">File Name: </span>
            {uploadedFile.name}
          </p>
          <p className="mt-1">
            <span className="text-[var(--color-muted-foreground)]">File Size: </span>
            {formatFileSize(uploadedFile.size)}
          </p>
        </div>
      ) : null}

      <Button
        type="button"
        onClick={onUpload}
        disabled={!uploadedFile || uploading || pdfUploaded}
      >
        {uploading ? 'Uploading PDF…' : pdfUploaded ? 'Uploaded' : 'Upload'}
      </Button>

      {uploadError ? <p className="text-sm text-red-400">{uploadError}</p> : null}
    </div>
  )
}
