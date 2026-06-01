import type { Chunk } from '@/types/api'

export function isVcApprovedForBuild(chunk: Chunk): boolean {
  return chunk.state === 'VCApproved' || chunk.vc_approved === true
}

export function filterVcApprovedChunks(chunks: Chunk[]): Chunk[] {
  return chunks.filter(isVcApprovedForBuild)
}
