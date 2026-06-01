import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient, ApiError } from '@/api/client'
import { WorkerWidget } from '@/components/layout/WorkerWidget'
import { QueueWidget } from '@/components/layout/QueueWidget'
import { AppProviders } from '@/app/providers/AppProviders'
import { renderApp } from '@/test/renderApp'
import {
  resetTestData,
  setProjectsList,
  setQueueSnapshot,
  setWorkerStatus,
} from '@/test/msw/handlers'
import { server } from '@/test/msw/server'
import { render } from '@testing-library/react'

describe('E8.1-A Foundation', () => {
  beforeEach(() => {
    resetTestData()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('1. redirects / to /projects', async () => {
    renderApp({ initialEntries: ['/'] })
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Projects' })).toBeInTheDocument()
    })
  })

  it('2. renders projects list', async () => {
    renderApp({ initialEntries: ['/projects'] })
    await waitFor(() => {
      expect(screen.getByText('Demo Project')).toBeInTheDocument()
      expect(screen.getByText('demo')).toBeInTheDocument()
    })
  })

  it('3. creates a project', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/projects'] })
    await waitFor(() => screen.getByText('Demo Project'))

    await user.click(screen.getByRole('button', { name: '+ New Project' }))
    await user.type(screen.getByLabelText(/project id/i), 'new-proj')
    await user.type(screen.getByLabelText(/^title$/i), 'New Project')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(screen.getByText('New Project')).toBeInTheDocument()
      expect(screen.getByText('new-proj')).toBeInTheDocument()
    })
  })

  it('4. opens a project from the grid', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/projects'] })
    await waitFor(() => screen.getByText('Demo Project'))
    await user.click(screen.getByRole('link', { name: 'Open' }))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Demo Project' })).toBeInTheDocument()
      expect(screen.getByText('No Parts Yet')).toBeInTheDocument()
    })
  })

  it('5. loads project dashboard', async () => {
    renderApp({ initialEntries: ['/projects/demo'] })
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Demo Project' })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: '+ New Part' })).toBeInTheDocument()
    })
  })

  it('6. opens create part wizard from dashboard', async () => {
    const user = userEvent.setup()
    renderApp({ initialEntries: ['/projects/demo'] })
    await waitFor(() => screen.getByText('No Parts Yet'))

    await user.click(screen.getByRole('link', { name: '+ New Part' }))

    await waitFor(() => {
      expect(screen.getByText('Create Part Wizard')).toBeInTheDocument()
      expect(screen.getByTestId('step-part-info')).toBeInTheDocument()
    })
  })

  it('7. worker widget refreshes on interval', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    setWorkerStatus({ running: false, state: 'idle' })

    render(
      <AppProviders>
        <WorkerWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText('Stopped')).toBeInTheDocument()
      expect(screen.getByText(/State: idle/)).toBeInTheDocument()
    })

    setWorkerStatus({ running: true, state: 'processing' })
    await vi.advanceTimersByTimeAsync(3100)

    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument()
      expect(screen.getByText(/State: processing/)).toBeInTheDocument()
    })
  })

  it('8. queue widget refreshes on interval', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    setQueueSnapshot({
      queued: 1,
      running: 0,
      completed: 2,
      failed: 0,
      cancelled: 0,
    })

    render(
      <AppProviders>
        <QueueWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText(/Queued: 1/)).toBeInTheDocument()
    })

    setQueueSnapshot({
      queued: 5,
      running: 1,
      completed: 10,
      failed: 2,
      cancelled: 0,
    })
    await vi.advanceTimersByTimeAsync(3100)

    await waitFor(() => {
      expect(screen.getByText(/Queued: 5/)).toBeInTheDocument()
      expect(screen.getByText(/Failed: 2/)).toBeInTheDocument()
    })
  })

  it('9. api client throws parsed API errors', async () => {
    server.use(
      http.get('/api/v1/projects', () =>
        HttpResponse.json({ error: 'Server exploded' }, { status: 500 }),
      ),
    )
    await expect(apiClient('/projects')).rejects.toSatisfy((err: unknown) => {
      return err instanceof ApiError && err.message === 'Server exploded'
    })
  })

  it('9b. shows toast on create project failure', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/projects', () =>
        HttpResponse.json({ error: 'duplicate id' }, { status: 409 }),
      ),
    )
    renderApp({ initialEntries: ['/projects'] })
    await waitFor(() => screen.getByText('Demo Project'))

    await user.click(screen.getByRole('button', { name: '+ New Project' }))
    await user.type(screen.getByLabelText(/project id/i), 'dup')
    await user.type(screen.getByLabelText(/^title$/i), 'Dup')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(screen.getByText('Create Project Failed')).toBeInTheDocument()
      expect(screen.getByText('duplicate id')).toBeInTheDocument()
    })
  })

  it('10a. shows empty projects state', async () => {
    setProjectsList([])
    renderApp({ initialEntries: ['/projects'] })
    await waitFor(() => {
      expect(screen.getByText('No Projects Yet')).toBeInTheDocument()
      expect(screen.getByText('Create Your First Project')).toBeInTheDocument()
    })
  })

  it('10b. shows empty parts state', async () => {
    setProjectsList([
      {
        project_id: 'empty',
        title: 'Empty',
        created_at: '',
        updated_at: '',
        status: 'active',
        parts: [],
      },
    ])
    renderApp({ initialEntries: ['/projects/empty'] })
    await waitFor(() => {
      expect(screen.getByText('No Parts Yet')).toBeInTheDocument()
      expect(screen.getByText('Create Your First Part')).toBeInTheDocument()
    })
  })
})
