/** Short ETA (e.g. 4m, 51m) — legacy compact display. */
export function formatEtaSeconds(seconds: number | null | undefined): string | null {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return null
  }
  const rounded = Math.max(0, Math.round(seconds))
  if (rounded < 60) {
    return `${rounded}s`
  }
  const minutes = Math.round(rounded / 60)
  return `${minutes}m`
}

/** Clock-style ETA (e.g. 00:24, 03:17, 26:41). */
export function formatEtaClock(seconds: number | null | undefined): string | null {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
    return null
  }
  const total = Math.max(0, Math.round(seconds))
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const secs = total % 60
  const mm = String(minutes).padStart(2, '0')
  const ss = String(secs).padStart(2, '0')
  if (hours > 0) {
    return `${hours}:${mm}:${ss}`
  }
  return `${mm}:${ss}`
}
