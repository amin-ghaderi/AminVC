import { useMutation } from '@tanstack/react-query'

import {
  createPart,
  createPartChunks,
  extractPartText,
  uploadSourcePdf,
} from '@/api/parts'
import type { ChunkingRequest, CreatePartRequest } from '@/types/api'

export function useCreatePartMutation(projectId: string) {
  return useMutation({
    mutationFn: (body: CreatePartRequest) => createPart(projectId, body),
  })
}

export function useUploadPdfMutation(projectId: string, partId: string) {
  return useMutation({
    mutationFn: (file: File) => uploadSourcePdf(projectId, partId, file),
  })
}

export function useExtractTextMutation(projectId: string, partId: string) {
  return useMutation({
    mutationFn: () => extractPartText(projectId, partId),
  })
}

export function useCreateChunksMutation(projectId: string, partId: string) {
  return useMutation({
    mutationFn: (body: ChunkingRequest) =>
      createPartChunks(projectId, partId, body),
  })
}
