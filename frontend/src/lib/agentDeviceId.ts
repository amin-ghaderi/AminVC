export const AGENT_DEVICE_ID_STORAGE_KEY = 'aminvc_device_id'

export function readAgentDeviceId(): string {
  try {
    return localStorage.getItem(AGENT_DEVICE_ID_STORAGE_KEY)?.trim() ?? ''
  } catch {
    return ''
  }
}

export function writeAgentDeviceId(deviceId: string): void {
  localStorage.setItem(AGENT_DEVICE_ID_STORAGE_KEY, deviceId.trim())
}
