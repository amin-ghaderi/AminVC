import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { WorkerWidget } from '@/components/layout/WorkerWidget'
import { WorkerStoppedBanner } from '@/components/worker/WorkerStoppedBanner'
import { AppProviders } from '@/app/providers/AppProviders'
import { renderApp } from '@/test/renderApp'
import { resetTestData, setWorkerStatus } from '@/test/msw/handlers'
import { server } from '@/test/msw/server'
import { render } from '@testing-library/react'

describe('E9.3-B Worker controls', () => {
  beforeEach(() => {
    resetTestData()
  })

  it('shows Start enabled and Stop disabled when worker is stopped', async () => {
    setWorkerStatus({ running: false, state: 'STOPPED' })

    render(
      <AppProviders>
        <WorkerWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByText('Stopped')).toBeInTheDocument()
    })

    expect(screen.getByTestId('worker-start-button')).toBeEnabled()
    expect(screen.getByTestId('worker-stop-button')).toBeDisabled()
  })

  it('starts worker from header widget and refreshes status', async () => {
    const user = userEvent.setup()
    setWorkerStatus({ running: false, state: 'STOPPED' })

    render(
      <AppProviders>
        <WorkerWidget />
      </AppProviders>,
    )

    await waitFor(() => screen.getByTestId('worker-start-button'))
    await user.click(screen.getByTestId('worker-start-button'))

    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument()
    })
    expect(screen.getByTestId('worker-stop-button')).toBeEnabled()
    expect(screen.getByTestId('worker-start-button')).toBeDisabled()
  })

  it('stops worker from header widget', async () => {
    const user = userEvent.setup()
    setWorkerStatus({ running: true, state: 'IDLE' })

    render(
      <AppProviders>
        <WorkerWidget />
      </AppProviders>,
    )

    await waitFor(() => screen.getByTestId('worker-stop-button'))
    await user.click(screen.getByTestId('worker-stop-button'))

    await waitFor(() => {
      expect(screen.getByText('Stopped')).toBeInTheDocument()
    })
  })

  it('shows stopped banner on queue page when worker is stopped', async () => {
    setWorkerStatus({ running: false, state: 'STOPPED' })

    renderApp({ initialEntries: ['/queue'] })

    await waitFor(() => {
      expect(screen.getByTestId('worker-stopped-banner')).toBeInTheDocument()
      expect(screen.getByText('Worker is stopped.')).toBeInTheDocument()
      expect(screen.getByText('Queued jobs will not execute.')).toBeInTheDocument()
    })
  })

  it('hides stopped banner when worker is running', async () => {
    setWorkerStatus({ running: true, state: 'IDLE' })

    renderApp({ initialEntries: ['/progress'] })

    await waitFor(() => {
      expect(screen.getByTestId('progress-dashboard-page')).toBeInTheDocument()
    })
    expect(screen.queryByTestId('worker-stopped-banner')).not.toBeInTheDocument()
  })

  it('starts worker from banner button', async () => {
    const user = userEvent.setup()
    setWorkerStatus({ running: false, state: 'STOPPED' })

    render(
      <AppProviders>
        <WorkerStoppedBanner />
      </AppProviders>,
    )

    await waitFor(() => screen.getByTestId('worker-banner-start-button'))
    await user.click(screen.getByTestId('worker-banner-start-button'))

    await waitFor(() => {
      expect(screen.queryByTestId('worker-stopped-banner')).not.toBeInTheDocument()
    })
  })

  it('invalidates worker status after start mutation', async () => {
    const user = userEvent.setup()
    let getCount = 0

    server.use(
      http.get('/api/v1/worker', () => {
        getCount += 1
        if (getCount < 2) {
          return HttpResponse.json({ running: false, state: 'STOPPED' })
        }
        return HttpResponse.json({ running: true, state: 'IDLE' })
      }),
      http.post('/api/v1/worker/start', () =>
        HttpResponse.json({ status: 'started' }),
      ),
    )

    render(
      <AppProviders>
        <WorkerWidget />
      </AppProviders>,
    )

    await waitFor(() => screen.getByTestId('worker-start-button'))
    await user.click(screen.getByTestId('worker-start-button'))

    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument()
      expect(getCount).toBeGreaterThanOrEqual(2)
    })
  })
})
