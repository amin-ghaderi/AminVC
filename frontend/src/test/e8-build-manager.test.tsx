import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  BUILDS_POLL_MS,
  BUILD_EVENTS_POLL_MS,
  BUILD_QUEUE_JOBS_POLL_MS,
} from '@/hooks/pollingConstants'
import { resetTestData } from '@/test/msw/handlers'
import {
  getBuildsForPart,
  setBuildDownloadReady,
  setBuildsForPart,
} from '@/test/msw/buildManagerHandlers'
import { getMonitorJobs, setMonitorJobs } from '@/test/msw/queueMonitorHandlers'
import { getWorkspaceChunks } from '@/test/msw/workspaceHandlers'
import { useBuildManagerStore } from '@/store/buildManagerStore'
import { server } from '@/test/msw/server'
import { renderApp } from '@/test/renderApp'
import type { Build } from '@/types/api'

const BUILD_PATH = '/projects/demo/parts/part-ws/builds'

function renderBuildManager() {
  return renderApp({ initialEntries: [BUILD_PATH] })
}

async function waitForBuildPage() {
  await waitFor(() => {
    expect(screen.getByTestId('build-manager-page')).toBeInTheDocument()
  })
}

const sampleBuild: Build = {
  build_id: 'build-001',
  project_id: 'demo',
  part_id: 'part-ws',
  name: 'Test Build',
  created_at: '2026-01-03T09:00:00Z',
  updated_at: '2026-01-03T09:00:00Z',
  chunks: [3, 4],
  output_file: 'builds/build-001.wav',
  duration_seconds: null,
}

describe('E8.1-E Build Manager', () => {
  beforeEach(() => {
    resetTestData()
    useBuildManagerStore.getState().clearSelection()
    useBuildManagerStore.getState().setExpandedBuild(null)
  })

  it('1. load build page', async () => {
    renderBuildManager()
    await waitForBuildPage()
    expect(screen.getByTestId('build-header')).toBeInTheDocument()
  })

  it('2. VC-approved filtering', async () => {
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('build-chunk-row-3')).toBeInTheDocument()
      expect(screen.getByTestId('build-chunk-row-4')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('build-chunk-row-1')).not.toBeInTheDocument()
  })

  it('3. select chunks', async () => {
    const user = userEvent.setup()
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('build-chunk-select-4'))
    expect(screen.getByTestId('build-chunk-select-4')).toBeChecked()
  })

  it('4. select all', async () => {
    const user = userEvent.setup()
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByRole('button', { name: 'Select All' }))
    expect(screen.getByTestId('build-chunk-select-3')).toBeChecked()
    expect(screen.getByTestId('build-chunk-select-4')).toBeChecked()
  })

  it('5. clear selection', async () => {
    const user = userEvent.setup()
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByRole('button', { name: 'Select All' }))
    await user.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.getByTestId('build-chunk-select-3')).not.toBeChecked()
  })

  it('6. create build', async () => {
    const user = userEvent.setup()
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('build-chunk-select-4'))
    await user.type(screen.getByTestId('build-name-input'), 'Final Audiobook')
    await user.click(screen.getByTestId('create-build-submit'))
    await waitFor(() => {
      expect(screen.getByText('Build Created')).toBeInTheDocument()
      expect(getBuildsForPart('demo', 'part-ws')).toHaveLength(1)
    })
  })

  it('7. build list load', async () => {
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('build-card-build-001')).toBeInTheDocument()
      expect(screen.getByText('Test Build')).toBeInTheDocument()
    })
  })

  it('8. status derivation queued', async () => {
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    const jobs = getMonitorJobs()
    setMonitorJobs({
      ...jobs,
      queued: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'queued',
          created_at: '2026-01-03T10:00:00Z',
          started_at: null,
          completed_at: null,
          attempts: 0,
          last_error: null,
        },
      ],
    })
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('build-status-queued')).toBeInTheDocument()
    })
  })

  it('9. status derivation running', async () => {
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    const jobs = getMonitorJobs()
    setMonitorJobs({
      ...jobs,
      running: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'running',
          created_at: '2026-01-03T10:00:00Z',
          started_at: '2026-01-03T10:01:00Z',
          completed_at: null,
          attempts: 1,
          last_error: null,
        },
      ],
    })
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('build-status-running')).toBeInTheDocument()
    })
  })

  it('10. status derivation completed', async () => {
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    const jobs = getMonitorJobs()
    setMonitorJobs({
      ...jobs,
      completed: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'completed',
          created_at: '2026-01-03T09:00:00Z',
          started_at: '2026-01-03T09:01:00Z',
          completed_at: '2026-01-03T09:02:00Z',
          attempts: 1,
          last_error: null,
        },
      ],
    })
    setBuildDownloadReady('demo', 'part-ws', 'build-001', true)
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('build-status-completed')).toBeInTheDocument()
    })
  })

  it('11. queue build', async () => {
    const user = userEvent.setup()
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('queue-build-build-001'))
    await waitFor(() => {
      expect(screen.getByText('Build queued')).toBeInTheDocument()
      const queued = getMonitorJobs().queued.find((j) => j.job_id === 'build-001')
      expect(queued?.job_type).toBe('build')
    })
  })

  it('12. cancel build', async () => {
    const user = userEvent.setup()
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    const jobs = getMonitorJobs()
    setMonitorJobs({
      ...jobs,
      queued: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'queued',
          created_at: '2026-01-03T10:00:00Z',
          started_at: null,
          completed_at: null,
          attempts: 0,
          last_error: null,
        },
      ],
    })
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('cancel-build-build-001'))
    await waitFor(() => {
      expect(
        getMonitorJobs().queued.find((j) => j.job_id === 'build-001'),
      ).toBeUndefined()
    })
  })

  it('13. download link rendering', async () => {
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    const jobs = getMonitorJobs()
    setMonitorJobs({
      ...jobs,
      completed: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'completed',
          created_at: '2026-01-03T09:00:00Z',
          started_at: '2026-01-03T09:01:00Z',
          completed_at: '2026-01-03T09:02:00Z',
          attempts: 1,
          last_error: null,
        },
      ],
    })
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      const link = screen.getByTestId('download-build-build-001')
      expect(link).toHaveAttribute('href', expect.stringContaining('/builds/build-001/download'))
    })
  })

  it('14. build details expand', async () => {
    const user = userEvent.setup()
    setBuildsForPart('demo', 'part-ws', [sampleBuild])
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('expand-build-build-001'))
    await waitFor(() => {
      expect(screen.getByTestId('build-details')).toBeInTheDocument()
      expect(screen.getByTestId('build-last-activity')).toBeInTheDocument()
    })
  })

  it('15. empty state no VC approved chunks', async () => {
    server.use(
      http.get('/api/v1/projects/:projectId/parts/:partId/chunks', () =>
        HttpResponse.json(
          getWorkspaceChunks().map((c) => ({
            ...c,
            state: 'NarrationReady',
            vc_approved: false,
          })),
        ),
      ),
    )
    renderBuildManager()
    await waitForBuildPage()
    await waitFor(() => {
      expect(screen.getByTestId('no-vc-approved-empty')).toBeInTheDocument()
      expect(
        screen.getByText('No VC-approved chunks available for build creation.'),
      ).toBeInTheDocument()
    })
  })

  it('16. polling intervals', () => {
    expect(BUILDS_POLL_MS).toBe(5000)
    expect(BUILD_QUEUE_JOBS_POLL_MS).toBe(3000)
    expect(BUILD_EVENTS_POLL_MS).toBe(5000)
  })

  it('17. API error toast', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/projects/:projectId/parts/:partId/builds', () =>
        HttpResponse.json({ error: 'create failed' }, { status: 500 }),
      ),
    )
    renderBuildManager()
    await waitForBuildPage()
    await user.click(screen.getByTestId('build-chunk-select-4'))
    await user.type(screen.getByTestId('build-name-input'), 'Fail Build')
    await user.click(screen.getByTestId('create-build-submit'))
    await waitFor(() => {
      expect(screen.getByText('Create build failed')).toBeInTheDocument()
    })
  })
})
