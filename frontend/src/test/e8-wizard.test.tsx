import { act, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { estimateChunkCount } from '@/lib/textStats'
import { useCreatePartWizardStore } from '@/store/createPartWizardStore'
import { resetTestData } from '@/test/msw/handlers'
import { server } from '@/test/msw/server'
import { renderWizard } from '@/test/renderWizard'

const SAMPLE_PDF = new File(['%PDF-1.4 test'], 'chapter.pdf', {
  type: 'application/pdf',
})

async function completePartInfo(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/part id/i), 'part-wiz')
  await user.type(screen.getByLabelText(/^title$/i), 'Wizard Part')
  await user.click(screen.getByRole('button', { name: 'Next' }))
  await waitFor(() => {
    expect(screen.getByTestId('step-upload-pdf')).toBeInTheDocument()
  })
}

async function uploadPdf(user: ReturnType<typeof userEvent.setup>) {
  const input = document.querySelector(
    'input[type="file"]',
  ) as HTMLInputElement
  await user.upload(input, SAMPLE_PDF)
  await user.click(screen.getByRole('button', { name: 'Upload' }))
  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Uploaded' })).toBeDisabled()
  })
}

describe('E8.1-B Create Part Wizard', () => {
  beforeEach(() => {
    resetTestData()
  })

  it('1. create part step validates and advances', async () => {
    const user = userEvent.setup()
    renderWizard()
    await user.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText(/Part ID and Title are required/)).toBeInTheDocument()
    await completePartInfo(user)
  })

  it('2. PDF upload step', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
    await uploadPdf(user)
    expect(screen.getByText(/chapter\.pdf/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled()
  })

  it('3. extract text step', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => {
      expect(screen.getByTestId('step-extract-results')).toBeInTheDocument()
      expect(screen.getByText(/Characters:/)).toBeInTheDocument()
      expect(screen.getByText(/Words:/)).toBeInTheDocument()
    })
  })

  it('4. editor loads after continue', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await waitFor(() => {
      expect(screen.getByTestId('step-editor')).toBeInTheDocument()
      expect(screen.getByTestId('part-text-editor')).toBeInTheDocument()
    })
  })

  it('5. chunk size selection', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByTestId('chunk-size-700'))
    expect(screen.getByTestId('chunk-size-700')).toHaveClass(
      'bg-[var(--color-primary)]',
    )
  })

  it('6. chunk count estimate updates', async () => {
    const text = 'a'.repeat(1600)
    expect(estimateChunkCount(text.length, 800)).toBe(2)
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    const estimate = screen.getByTestId('chunk-count-estimate')
    expect(Number(estimate.textContent)).toBeGreaterThan(0)
  })

  it('7. chunk creation shows success', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Create Chunks' }))
    await waitFor(() => {
      expect(screen.getByText('Part Created Successfully')).toBeInTheDocument()
      expect(screen.getByText(/Chunks Created:/)).toBeInTheDocument()
    })
  })

  it('8. navigation between steps via back', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await user.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByTestId('step-part-info')).toBeInTheDocument()
  })

  it('9. validation on step 1', async () => {
    const user = userEvent.setup()
    renderWizard()
    await user.type(screen.getByLabelText(/part id/i), 'only-id')
    await user.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText(/Part ID and Title are required/)).toBeInTheDocument()
  })

  it('10. unsaved changes warning on cancel', async () => {
    const user = userEvent.setup()
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await screen.findByTestId('part-text-editor')
    act(() => {
      useCreatePartWizardStore
        .getState()
        .setEditedText('متن ویرایش شده برای آزمایش', true)
    })
    await user.click(screen.getByTestId('wizard-cancel'))
    expect(confirmSpy).toHaveBeenCalledWith(
      expect.stringContaining('You have unsaved changes'),
    )
    confirmSpy.mockRestore()
  })

  it('11. upload error shows toast', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/projects/:projectId/parts/:partId/source', () =>
        HttpResponse.json({ error: 'bad pdf' }, { status: 400 }),
      ),
    )
    renderWizard()
    await completePartInfo(user)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, SAMPLE_PDF)
    await user.click(screen.getByRole('button', { name: 'Upload' }))
    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument()
    })
  })

  it('12. success flow back to project', async () => {
    const user = userEvent.setup()
    renderWizard()
    await completePartInfo(user)
    await uploadPdf(user)
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Extract Text' }))
    await waitFor(() => screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Continue To Editor' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Next' }))
    await user.click(screen.getByRole('button', { name: 'Create Chunks' }))
    await waitFor(() => screen.getByText('Part Created Successfully'))
    await user.click(screen.getByRole('link', { name: 'Back To Project' }))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Demo Project' })).toBeInTheDocument()
    })
  })
})
