/** Human-readable ETA (e.g. 4m, 51m). */
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
