const PREVIEW_LENGTH = 1000

export function countCharacters(text: string): number {
  return text.length
}

export function countWords(text: string): number {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

export function textPreview(text: string, maxLength = PREVIEW_LENGTH): string {
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}…`
}

export function estimateChunkCount(textLength: number, chunkSize: number): number {
  if (textLength <= 0 || chunkSize <= 0) return 0
  return Math.max(1, Math.ceil(textLength / chunkSize))
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
