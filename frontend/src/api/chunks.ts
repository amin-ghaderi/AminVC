import { apiClient } from '@/api/client'
import type { Chunk, ChunkAssets } from '@/types/api'

function chunkPath(projectId: string, partId: string, chunkId?: number) {
  const base = `/projects/${encodeURIComponent(projectId)}/parts/${encodeURIComponent(partId)}/chunks`
  return chunkId !== undefined ? `${base}/${chunkId}` : base
}

export function listChunks(projectId: string, partId: string): Promise<Chunk[]> {
  return apiClient<Chunk[]>(chunkPath(projectId, partId))
}

export function getChunk(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(chunkPath(projectId, partId, chunkId))
}

export function updateChunkText(
  projectId: string,
  partId: string,
  chunkId: number,
  text: string,
): Promise<Chunk> {
  return apiClient<Chunk>(`${chunkPath(projectId, partId, chunkId)}/text`, {
    method: 'PUT',
    body: JSON.stringify({ text }),
  })
}

export function approveNarration(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(
    `${chunkPath(projectId, partId, chunkId)}/approve-narration`,
    { method: 'POST' },
  )
}

export function unapproveNarration(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(
    `${chunkPath(projectId, partId, chunkId)}/unapprove-narration`,
    { method: 'POST' },
  )
}

export function approveVc(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(`${chunkPath(projectId, partId, chunkId)}/approve-vc`, {
    method: 'POST',
  })
}

export function unapproveVc(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(
    `${chunkPath(projectId, partId, chunkId)}/unapprove-vc`,
    { method: 'POST' },
  )
}

export function rebuildNarration(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(
    `${chunkPath(projectId, partId, chunkId)}/rebuild-narration`,
    { method: 'POST' },
  )
}

export function rebuildVc(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<Chunk> {
  return apiClient<Chunk>(`${chunkPath(projectId, partId, chunkId)}/rebuild-vc`, {
    method: 'POST',
  })
}

export function getChunkAssets(
  projectId: string,
  partId: string,
  chunkId: number,
): Promise<ChunkAssets> {
  return apiClient<ChunkAssets>(
    `${chunkPath(projectId, partId, chunkId)}/assets`,
  )
}

export function narrationAudioUrl(
  projectId: string,
  partId: string,
  chunkId: number,
): string {
  return `/api/v1${chunkPath(projectId, partId, chunkId)}/audio/narration`
}

export function vcAudioUrl(
  projectId: string,
  partId: string,
  chunkId: number,
): string {
  return `/api/v1${chunkPath(projectId, partId, chunkId)}/audio/vc`
}
