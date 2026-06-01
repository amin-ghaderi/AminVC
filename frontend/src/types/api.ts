export interface Project {
  project_id: string
  title: string
  created_at: string
  updated_at: string
  status: string
  parts: string[]
}

export interface Part {
  part_id: string
  project_id: string
  title: string
  state: string
  processing_profile: string
  chunks_total: number
  chunks_completed_narration: number
  chunks_completed_vc: number
  current_chunk: number | null
  created_at: string
  updated_at: string
}

export interface WorkerStatus {
  running: boolean
  state: string
}

export interface QueueSnapshot {
  queued: number
  running: number
  completed: number
  failed: number
  cancelled: number
}

export interface CreateProjectRequest {
  project_id: string
  title: string
}

export interface CreatePartRequest {
  part_id: string
  title: string
}

export interface SourceUploadResponse {
  filename: string
  size_bytes: number
  path: string
}

export interface ExtractTextResponse {
  text: string
}

export interface ChunkingRequest {
  text: string
  chunk_size: number
}

export interface ChunkingResponse {
  chunks_created: number
}

export interface PartSummary {
  total_chunks: number
  narration_ready: number
  narration_approved: number
  vc_ready: number
  vc_approved: number
  failed: number
  interrupted: number
}

export interface ApiErrorBody {
  error: string
}

export type ChunkQuality = 600 | 700 | 800 | 900 | 1000

export const CHUNK_QUALITY_OPTIONS: ChunkQuality[] = [
  600, 700, 800, 900, 1000,
]
