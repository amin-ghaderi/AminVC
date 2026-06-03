import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  resetTestData,
  resetWorkspaceData,
  setWorkspaceReferenceExists,
} from '@/test/msw/handlers'
import { renderApp } from '@/test/renderApp'

const WORKSPACE_PATH = '/projects/demo/parts/part-ws'

function renderWorkspace() {
  return renderApp({ initialEntries: [WORKSPACE_PATH] })
}

async function waitForWorkspace() {
  await waitFor(() => {
    expect(screen.getByTestId('part-workspace')).toBeInTheDocument()
  })
}

describe('E9.2-A Reference Voice', () => {
  beforeEach(() => {
    resetTestData()
    resetWorkspaceData()
  })

  it('shows missing reference status and upload control', async () => {
    setWorkspaceReferenceExists(false)
    renderWorkspace()
    await waitForWorkspace()
    expect(screen.getByTestId('reference-voice-panel')).toBeInTheDocument()
    expect(screen.getByTestId('reference-voice-status')).toHaveTextContent('Missing')
    expect(screen.getByTestId('reference-voice-upload')).toBeInTheDocument()
  })

  it('shows ready reference with preview and replace/delete', async () => {
    renderWorkspace()
    await waitForWorkspace()
    expect(screen.getByTestId('reference-voice-status')).toHaveTextContent('Ready')
    expect(screen.getByTestId('reference-voice-preview')).toBeInTheDocument()
    expect(screen.getByTestId('reference-voice-replace')).toBeInTheDocument()
    expect(screen.getByTestId('reference-voice-delete')).toBeInTheDocument()
  })

  it('disables VC when reference missing', async () => {
    setWorkspaceReferenceExists(false)
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-2'))
    await user.click(screen.getByRole('tab', { name: 'VC' }))
    expect(screen.getByTestId('vc-reference-required')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeDisabled()
  })

  it('enables VC queue when reference present and narration approved', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-2'))
    await user.click(screen.getByRole('tab', { name: 'VC' }))
    expect(screen.queryByTestId('vc-reference-required')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeEnabled()
  })

  it('upload reference updates status to ready', async () => {
    setWorkspaceReferenceExists(false)
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()

    const file = new File([new ArrayBuffer(8)], 'reference.wav', {
      type: 'audio/wav',
    })
    const input = screen.getByTestId('reference-voice-file-input')
    await user.upload(input, file)

    await waitFor(() => {
      expect(screen.getByTestId('reference-voice-status')).toHaveTextContent('Ready')
    })
    expect(screen.getByText('Reference voice uploaded')).toBeInTheDocument()
  })

  it('delete reference returns to missing state', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('reference-voice-delete'))
    await waitFor(() => {
      expect(screen.getByTestId('reference-voice-status')).toHaveTextContent('Missing')
    })
  })
})
