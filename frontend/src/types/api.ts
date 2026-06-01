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

export interface AssetSlot {
  status: string
  file: string | null
  duration_seconds: number | null
}

export interface Chunk {
  chunk_id: number
  state: string
  narration_approved: boolean
  vc_approved: boolean
  text: string
  narration: AssetSlot
  vc: AssetSlot
  retry_count: number
  last_error: string | null
  updated_at: string
}

export interface ChunkAssets {
  narration_exists: boolean
  vc_exists: boolean
  narration_url: string
  vc_url: string
  narration_size: number | null
  vc_size: number | null
}

export interface EventEnvelope {
  event_id: string
  event_type: string
  timestamp: string
  project_id: string | null
  part_id: string | null
  chunk_id: number | null
  payload: Record<string, unknown>
}

export interface QueueJobBody {
  project_id: string
  part_id: string
  chunk_id: number
}

export interface QueueJob {
  job_id: string
  job_type: string
  project_id: string
  part_id: string
  chunk_id: number | null
  status: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  attempts: number
  last_error: string | null
}

export interface QueueJobsResponse {
  queued: QueueJob[]
  running: QueueJob[]
  completed: QueueJob[]
  failed: QueueJob[]
  cancelled: QueueJob[]
}

export interface VcProgressPayload {
  current_step: number
  total_steps: number
  elapsed_seconds: number
  estimated_remaining_seconds: number
}

export interface Build {
  build_id: string
  project_id: string
  part_id: string
  name: string
  created_at: string
  updated_at: string
  chunks: number[]
  output_file: string
  duration_seconds: number | null
}

export interface CreateBuildRequest {
  name: string
  chunks: number[]
  build_id?: string | null
}

export type BuildStatus =
  | 'Created'
  | 'Queued'
  | 'Running'
  | 'Completed'
  | 'Failed'
  | 'Cancelled'

export type QueueMonitorFilter = 'all' | 'narration' | 'vc' | 'build'

export type ChunkListFilter =
  | 'all'
  | 'narration'
  | 'vc'
  | 'approved'
  | 'failed'
  | 'interrupted'

export interface ApiErrorBody {
  error: string
}

export type ChunkQuality = 600 | 700 | 800 | 900 | 1000

export const CHUNK_QUALITY_OPTIONS: ChunkQuality[] = [
  600, 700, 800, 900, 1000,
]
