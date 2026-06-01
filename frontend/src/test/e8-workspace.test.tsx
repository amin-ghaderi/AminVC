import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { WORKSPACE_POLL_MS } from '@/hooks/usePartWorkspace'
import { resetTestData } from '@/test/msw/handlers'
import { server } from '@/test/msw/server'
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

describe('E8.1-C Part Workspace', () => {
  beforeEach(() => {
    resetTestData()
  })

  it('1. loads workspace', async () => {
    renderWorkspace()
    await waitForWorkspace()
    expect(screen.getByTestId('part-header')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Workspace Part' }),
    ).toBeInTheDocument()
    expect(screen.getByTestId('chunk-list')).toBeInTheDocument()
  })

  it('2. chunk selection', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-3'))
    await waitFor(() => {
      expect(screen.getByTestId('chunk-details')).toBeInTheDocument()
    })
  })

  it('3. search filters chunks', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.type(screen.getByTestId('chunk-search'), 'Gamma')
    await waitFor(() => {
      expect(screen.getByTestId('chunk-row-3')).toBeInTheDocument()
      expect(screen.queryByTestId('chunk-row-1')).not.toBeInTheDocument()
    })
  })

  it('4. filters by failed', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByRole('button', { name: 'Failed' }))
    await waitFor(() => {
      expect(screen.getByTestId('chunk-row-5')).toBeInTheDocument()
      expect(screen.queryByTestId('chunk-row-1')).not.toBeInTheDocument()
    })
  })

  it('5. text save shows toast', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await waitFor(() => screen.getByTestId('text-tab'))
    await user.click(screen.getByRole('button', { name: 'Save Text' }))
    await waitFor(() => {
      expect(screen.getByText('Text saved')).toBeInTheDocument()
    })
  })

  it('6. rebuild narration shows warning dialog', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await waitFor(() => screen.getByTestId('text-tab'))
    await user.click(screen.getByRole('button', { name: 'Rebuild Narration' }))
    expect(
      screen.getByText(
        /This will invalidate existing narration and VC outputs/,
      ),
    ).toBeInTheDocument()
  })

  it('7. queue narration from narration tab', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await user.click(screen.getByRole('tab', { name: 'Narration' }))
    await waitFor(() => screen.getByTestId('narration-tab'))
    await user.click(screen.getByRole('button', { name: 'Queue Narration' }))
    await waitFor(() => {
      expect(screen.getByText('Narration queued')).toBeInTheDocument()
    })
  })

  it('8. approve narration when ready', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await user.click(screen.getByRole('tab', { name: 'Narration' }))
    await user.click(screen.getByRole('button', { name: 'Approve Narration' }))
    await waitFor(() => {
      expect(screen.getByText('Narration approved')).toBeInTheDocument()
    })
  })

  it('9. queue VC disabled without narration approval', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await user.click(screen.getByRole('tab', { name: 'VC' }))
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeDisabled()
  })

  it('10. approve VC when ready', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-3'))
    await user.click(screen.getByRole('tab', { name: 'VC' }))
    await user.click(screen.getByRole('button', { name: 'Approve VC' }))
    await waitFor(() => {
      expect(screen.getByTestId('chunk-row-3')).toHaveTextContent('VCApproved')
    })
  })

  it('11. history filtering by chunk', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-2'))
    await user.click(screen.getByRole('tab', { name: 'History' }))
    await waitFor(() => {
      expect(screen.getByTestId('history-list')).toBeInTheDocument()
      expect(screen.getByText('narration.approved')).toBeInTheDocument()
    })
  })

  it('12a. no chunk selected empty state', async () => {
    server.use(
      http.get('/api/v1/projects/:projectId/parts/:partId/chunks', () =>
        HttpResponse.json([]),
      ),
    )
    renderWorkspace()
    await waitFor(() => {
      expect(screen.getByText('Select a chunk')).toBeInTheDocument()
    })
  })

  it('12b. narration vc and history empty states', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-6'))
    await user.click(screen.getByRole('tab', { name: 'Narration' }))
    expect(screen.getByText('No narration generated yet')).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'VC' }))
    expect(screen.getByText('No VC generated yet')).toBeInTheDocument()
    await user.click(screen.getByTestId('chunk-row-4'))
    await user.click(screen.getByRole('tab', { name: 'History' }))
    expect(screen.getByTestId('history-empty')).toBeInTheDocument()
  })

  it('13. polling interval is 5 seconds', () => {
    expect(WORKSPACE_POLL_MS).toBe(5000)
  })

  it('14. API error toast on save failure', async () => {
    const user = userEvent.setup()
    server.use(
      http.put('/api/v1/projects/:projectId/parts/:partId/chunks/:chunkId/text', () =>
        HttpResponse.json({ error: 'save failed' }, { status: 500 }),
      ),
    )
    renderWorkspace()
    await waitForWorkspace()
    await user.click(screen.getByTestId('chunk-row-1'))
    await user.click(screen.getByRole('button', { name: 'Save Text' }))
    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument()
    })
  })

  it('15. invalidation updates chunk list after approve', async () => {
    const user = userEvent.setup()
    renderWorkspace()
    await waitForWorkspace()
    expect(screen.getByTestId('chunk-row-1')).toHaveTextContent('NarrationReady')
    await user.click(screen.getByTestId('chunk-row-1'))
    await user.click(screen.getByRole('tab', { name: 'Narration' }))
    await user.click(screen.getByRole('button', { name: 'Approve Narration' }))
    await waitFor(() => {
      expect(screen.getByTestId('chunk-row-1')).toHaveTextContent('NarrationApproved')
    })
  })
})
