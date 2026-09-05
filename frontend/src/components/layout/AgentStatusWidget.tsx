import { useState, type FormEvent } from 'react'

import { useAgentStatus } from '@/hooks/useAgentStatus'
import {
  readAgentDeviceId,
  writeAgentDeviceId,
} from '@/lib/agentDeviceId'

export function AgentStatusWidget() {
  const [deviceId, setDeviceId] = useState(readAgentDeviceId)
  const [draft, setDraft] = useState(deviceId)
  const { data, isLoading } = useAgentStatus(deviceId)

  function onSave(event: FormEvent) {
    event.preventDefault()
    const next = draft.trim()
    if (!next) {
      return
    }
    writeAgentDeviceId(next)
    setDeviceId(next)
  }

  if (!deviceId) {
    return (
      <form
        className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs"
        data-testid="agent-status"
        onSubmit={onSave}
      >
        <span className="text-[var(--color-muted-foreground)]">Local Agent</span>
        <input
          className="h-7 w-28 rounded border border-[var(--color-border)] bg-[var(--color-background)] px-2 text-xs"
          data-testid="agent-device-id-input"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="device id"
          value={draft}
        />
        <button data-testid="agent-device-id-save" type="submit">
          Save
        </button>
      </form>
    )
  }

  const online = Boolean(data?.online)
  const label =
    isLoading && !data
      ? 'Checking local agent…'
      : online
        ? '🟢 Local Agent Connected'
        : '🔴 Local Agent Offline'

  return (
    <div
      className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-xs"
      data-testid="agent-status"
    >
      <div data-testid="agent-status-label">{label}</div>
    </div>
  )
}
