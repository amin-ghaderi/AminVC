import type { AgentStatus } from '@/types/api'

function agentCloudBase(): string {
  const raw = import.meta.env.VITE_AGENT_CLOUD_URL
  if (typeof raw === 'string' && raw.trim()) {
    return raw.trim().replace(/\/$/, '')
  }
  return ''
}

export function agentStatusUrl(deviceId: string): string {
  const path = `/agent/status/${encodeURIComponent(deviceId)}`
  const base = agentCloudBase()
  return base ? `${base}${path}` : path
}

export async function getAgentStatus(deviceId: string): Promise<AgentStatus> {
  try {
    const response = await fetch(agentStatusUrl(deviceId))
    if (!response.ok) {
      return { device_id: deviceId, online: false, last_seen: null }
    }
    const body = (await response.json()) as AgentStatus
    return {
      device_id: body.device_id ?? deviceId,
      online: Boolean(body.online),
      last_seen: body.last_seen ?? null,
    }
  } catch {
    return { device_id: deviceId, online: false, last_seen: null }
  }
}
