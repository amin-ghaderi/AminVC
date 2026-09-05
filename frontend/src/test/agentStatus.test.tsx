import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { AgentStatusWidget } from '@/components/layout/AgentStatusWidget'
import { AppProviders } from '@/app/providers/AppProviders'
import { AGENT_DEVICE_ID_STORAGE_KEY } from '@/lib/agentDeviceId'
import { renderApp } from '@/test/renderApp'
import { resetTestData } from '@/test/msw/handlers'
import { server } from '@/test/msw/server'
import { render } from '@testing-library/react'

function mockAgentStatus(online: boolean, deviceId = 'dev-1') {
  server.use(
    http.get('/agent/status/:deviceId', ({ params }) =>
      HttpResponse.json({
        device_id: String(params.deviceId),
        online,
        last_seen: online ? '2026-09-05T16:00:00+00:00' : null,
      }),
    ),
  )
  localStorage.setItem(AGENT_DEVICE_ID_STORAGE_KEY, deviceId)
}

describe('Phase 1 local agent status', () => {
  beforeEach(() => {
    resetTestData()
    localStorage.removeItem(AGENT_DEVICE_ID_STORAGE_KEY)
  })

  it('asks for a device id when none is stored', () => {
    render(
      <AppProviders>
        <AgentStatusWidget />
      </AppProviders>,
    )

    expect(screen.getByTestId('agent-device-id-input')).toBeInTheDocument()
    expect(screen.queryByTestId('agent-status-label')).not.toBeInTheDocument()
  })

  it('shows connected when the cloud status is online', async () => {
    mockAgentStatus(true)

    render(
      <AppProviders>
        <AgentStatusWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('agent-status-label')).toHaveTextContent(
        'Local Agent Connected',
      )
    })
  })

  it('shows offline when the cloud status is offline', async () => {
    mockAgentStatus(false)

    render(
      <AppProviders>
        <AgentStatusWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('agent-status-label')).toHaveTextContent(
        'Local Agent Offline',
      )
    })
  })

  it('shows offline when the cloud endpoint is unreachable', async () => {
    localStorage.setItem(AGENT_DEVICE_ID_STORAGE_KEY, 'dev-1')
    server.use(
      http.get('/agent/status/:deviceId', () => HttpResponse.error()),
    )

    render(
      <AppProviders>
        <AgentStatusWidget />
      </AppProviders>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('agent-status-label')).toHaveTextContent(
        'Local Agent Offline',
      )
    })
  })

  it('saves a device id and then polls status', async () => {
    const user = userEvent.setup()
    mockAgentStatus(true, 'paired-device')
    localStorage.removeItem(AGENT_DEVICE_ID_STORAGE_KEY)

    render(
      <AppProviders>
        <AgentStatusWidget />
      </AppProviders>,
    )

    await user.type(screen.getByTestId('agent-device-id-input'), 'paired-device')
    await user.click(screen.getByTestId('agent-device-id-save'))

    expect(localStorage.getItem(AGENT_DEVICE_ID_STORAGE_KEY)).toBe(
      'paired-device',
    )
    await waitFor(() => {
      expect(screen.getByTestId('agent-status-label')).toHaveTextContent(
        'Local Agent Connected',
      )
    })
  })

  it('renders the status widget in the app header', async () => {
    mockAgentStatus(false)

    renderApp({ initialEntries: ['/projects'] })

    await waitFor(() => {
      expect(screen.getByTestId('agent-status')).toBeInTheDocument()
      expect(screen.getByTestId('agent-status-label')).toHaveTextContent(
        'Local Agent Offline',
      )
    })
  })
})
