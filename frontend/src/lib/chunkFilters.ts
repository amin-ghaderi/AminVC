import type { Chunk, ChunkListFilter } from '@/types/api'

const NARRATION_STATES = new Set([
  'NarrationQueued',
  'NarrationProcessing',
  'NarrationReady',
  'NarrationApproved',
  'NarrationFailed',
])

const VC_STATES = new Set([
  'VCQueued',
  'VCProcessing',
  'VCReady',
  'VCApproved',
  'VCFailed',
  'BuildReady',
])

export function formatChunkNumber(chunkId: number): string {
  return String(chunkId).padStart(3, '0')
}

export function matchesChunkFilter(chunk: Chunk, filter: ChunkListFilter): boolean {
  switch (filter) {
    case 'all':
      return true
    case 'narration':
      return NARRATION_STATES.has(chunk.state)
    case 'vc':
      return VC_STATES.has(chunk.state)
    case 'approved':
      return chunk.narration_approved || chunk.vc_approved
    case 'failed':
      return chunk.state === 'NarrationFailed' || chunk.state === 'VCFailed'
    case 'interrupted':
      return chunk.state === 'Interrupted'
    default:
      return true
  }
}

export function matchesChunkSearch(chunk: Chunk, search: string): boolean {
  const q = search.trim().toLowerCase()
  if (!q) return true
  const padded = formatChunkNumber(chunk.chunk_id).toLowerCase()
  return (
    padded.includes(q) ||
    String(chunk.chunk_id).includes(q) ||
    chunk.text.toLowerCase().includes(q)
  )
}

export function filterChunks(
  chunks: Chunk[],
  filter: ChunkListFilter,
  search: string,
): Chunk[] {
  return chunks
    .filter((c) => matchesChunkFilter(c, filter))
    .filter((c) => matchesChunkSearch(c, search))
}
