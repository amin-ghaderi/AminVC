import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import {
  EVENTS_POLL_MS,
  QUEUE_MONITOR_POLL_MS,
  VC_PROGRESS_POLL_MS,
} from '@/hooks/pollingConstants'
import { resetTestData, setWorkerStatus } from '@/test/msw/handlers'
import { useQueueMonitorStore } from '@/store/queueMonitorStore'
import { getMonitorJobs, setMonitorEvents } from '@/test/msw/queueMonitorHandlers'
import { server } from '@/test/msw/server'
import { renderApp } from '@/test/renderApp'

describe('E8.1-D Queue Monitor & Progress', () => {
  beforeEach(() => {
    resetTestData()
    setWorkerStatus({ running: true, state: 'executing' })
    useQueueMonitorStore.getState().setFilter('all')
    useQueueMonitorStore.getState().setSearch('')
  })

  it('1. queue page load', async () => {
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => {
      expect(screen.getByTestId('queue-monitor-page')).toBeInTheDocument()
    })
  })

  it('2. queue summary cards', async () => {
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => {
      const queued = screen.getByTestId('queue-summary-queued')
      expect(queued).toHaveTextContent('Queued')
      expect(queued.textContent).toMatch(/2/)
    })
  })

  it('3. running jobs section', async () => {
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => {
      expect(screen.getByTestId('running-job-job-r-1')).toBeInTheDocument()
      expect(screen.getByText('RUNNING')).toBeInTheDocument()
    })
  })

  it('4. queued jobs section', async () => {
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => {
      expect(screen.getByTestId('queued-job-job-q-1')).toBeInTheDocument()
    })
  })

  it('5. cancel queued job', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => screen.getByTestId('queued-job-job-q-1'))
    await user.click(
      within(screen.getByTestId('queued-job-job-q-1')).getByRole('button', {
        name: 'Cancel',
      }),
    )
    await waitFor(() => {
      expect(screen.getByText('Job cancelled')).toBeInTheDocument()
      expect(getMonitorJobs().queued.find((j) => j.job_id === 'job-q-1')).toBeUndefined()
    })
  })

  it('6. filters narration jobs', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => screen.getByTestId('queued-job-job-q-1'))
    await user.click(screen.getByRole('button', { name: 'Narration' }))
    await waitFor(() => {
      expect(screen.getByTestId('queued-job-job-q-1')).toBeInTheDocument()
      expect(screen.queryByTestId('queued-job-job-q-2')).not.toBeInTheDocument()
    })
  })

  it('7. search by job id', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(() => screen.getByTestId('queued-job-job-q-1'))
    await user.type(screen.getByTestId('queue-search'), 'job-q-2')
    await waitFor(() => {
      expect(screen.getByTestId('queued-job-job-q-2')).toBeInTheDocument()
      expect(screen.queryByTestId('queued-job-job-q-1')).not.toBeInTheDocument()
    })
  })

  it('8. progress dashboard load', async () => {
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      expect(screen.getByTestId('progress-dashboard-page')).toBeInTheDocument()
    })
  })

  it('9. VC progress extraction', async () => {
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      expect(screen.getByTestId('part-vc-progress-panel')).toBeInTheDocument()
      expect(screen.getByTestId('part-vc-step')).toHaveTextContent('Step 12 / 30')
      expect(screen.getByTestId('part-vc-completed')).toHaveTextContent('2 / 7 Completed')
    })
  })

  it('10. progress bar calculation', async () => {
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      const bar = screen.getByTestId('part-vc-step-bar')
      expect(bar).toHaveStyle({ width: '40%' })
    })
  })

  it('11. no progress state', async () => {
    setMonitorEvents([
      {
        event_id: 'x',
        event_type: 'queue.job_queued',
        timestamp: '2026-01-01T00:00:00Z',
        project_id: 'demo',
        part_id: 'p',
        chunk_id: 1,
        payload: {},
      },
    ])
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      expect(screen.getByTestId('part-vc-current-chunk-empty')).toBeInTheDocument()
      expect(
        screen.getByText('No VC conversion currently active'),
      ).toBeInTheDocument()
    })
  })

  it('12. worker status display', async () => {
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      const card = screen.getByTestId('worker-card-worker-1')
      expect(card).toBeInTheDocument()
      expect(within(card).getByText('Running')).toBeInTheDocument()
    })
  })

  it('13. recent events rendering', async () => {
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(() => {
      const list = screen.getByTestId('recent-events-list')
      expect(list).toBeInTheDocument()
      expect(within(list).getByText('vc.progress')).toBeInTheDocument()
      expect(within(list).getByText('worker.job_started')).toBeInTheDocument()
    })
  })

  it('14. polling intervals', () => {
    expect(QUEUE_MONITOR_POLL_MS).toBe(3000)
    expect(VC_PROGRESS_POLL_MS).toBe(2000)
    expect(EVENTS_POLL_MS).toBe(2000)
  })

  it('15a. queue load error message', async () => {
    server.use(
      http.get('/api/v1/queue/jobs', () =>
        HttpResponse.json({ error: 'down' }, { status: 500 }),
      ),
    )
    renderApp({ initialEntries: ['/queue'] })
    await waitFor(
      () => {
        expect(screen.getByTestId('queue-jobs-error')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )
  })

  it('15b. worker load error message', async () => {
    server.use(
      http.get('/api/v1/worker', () =>
        HttpResponse.json({ error: 'worker down' }, { status: 500 }),
      ),
    )
    renderApp({ initialEntries: ['/progress'] })
    await waitFor(
      () => {
        expect(screen.getByTestId('worker-load-error')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )
  })
})
