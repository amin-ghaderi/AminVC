import type { EventEnvelope, PartSummary, VcProgressPayload } from '@/types/api'

import {
  findLatestVcProgressEventForPart,
  parseVcProgressPayload,
  vcProgressPercent,
} from '@/lib/vcProgress'

export interface PartVcProgressView {
  currentChunkId: number | null
  currentStep: number
  totalSteps: number
  completedChunks: number
  totalChunks: number
  currentChunkPosition: number | null
  currentChunkEtaSeconds: number | null
  overallEtaSeconds: number | null
  progressPercent: number
  stepPercent: number
  hasActiveProgress: boolean
  overallEtaAvailable: boolean
}

export function dedupeVcCompletionDurations(
  events: EventEnvelope[],
  projectId: string,
  partId: string,
): Map<number, number> {
  const latest = new Map<number, { timestamp: string; duration: number }>()
  for (const event of events) {
    if (event.event_type !== 'vc.chunk_completed') continue
    if (event.project_id !== projectId || event.part_id !== partId) continue
    if (event.chunk_id === null) continue
    const raw = event.payload.duration_seconds
    if (typeof raw !== 'number' || !Number.isFinite(raw)) continue
    const prev = latest.get(event.chunk_id)
    if (!prev || event.timestamp > prev.timestamp) {
      latest.set(event.chunk_id, { timestamp: event.timestamp, duration: raw })
    }
  }
  const result = new Map<number, number>()
  for (const [chunkId, { duration }] of latest) {
    result.set(chunkId, duration)
  }
  return result
}

export function averageVcChunkDuration(
  events: EventEnvelope[],
  projectId: string,
  partId: string,
): number | null {
  const durations = [...dedupeVcCompletionDurations(events, projectId, partId).values()]
  if (!durations.length) return null
  return durations.reduce((sum, d) => sum + d, 0) / durations.length
}

export function remainingVcChunksAfterCurrent(
  totalChunks: number,
  vcReady: number,
  vcProcessing: number,
): number {
  if (vcProcessing > 0) {
    return Math.max(0, totalChunks - vcReady - 1)
  }
  return Math.max(0, totalChunks - vcReady)
}

export function calculatePartEtaSeconds(
  currentChunkRemaining: number,
  avgChunkDuration: number,
  remainingChunks: number,
): number {
  return currentChunkRemaining + avgChunkDuration * Math.max(0, remainingChunks)
}

export function computePartVcProgress(input: {
  events: EventEnvelope[] | undefined
  summary: PartSummary | undefined
  projectId: string
  partId: string
  chunkId?: number
  requireChunkProcessing?: boolean
  chunkIsProcessing?: boolean
}): PartVcProgressView {
  const empty: PartVcProgressView = {
    currentChunkId: null,
    currentStep: 0,
    totalSteps: 0,
    completedChunks: 0,
    totalChunks: 0,
    currentChunkPosition: null,
    currentChunkEtaSeconds: null,
    overallEtaSeconds: null,
    progressPercent: 0,
    stepPercent: 0,
    hasActiveProgress: false,
    overallEtaAvailable: false,
  }

  if (!input.summary) return empty

  const { summary, projectId, partId } = input
  const totalChunks = summary.total_chunks
  const completedChunks = summary.vc_ready
  const progressPercent =
    totalChunks > 0 ? Math.floor((completedChunks / totalChunks) * 100) : 0

  if (input.requireChunkProcessing && !input.chunkIsProcessing) {
    return {
      ...empty,
      completedChunks,
      totalChunks,
      progressPercent,
    }
  }

  const events = input.events ?? []
  const progressEvent = findLatestVcProgressEventForPart(
    events,
    projectId,
    partId,
    input.chunkId,
  )
  const progress: VcProgressPayload | null = progressEvent
    ? parseVcProgressPayload(progressEvent.payload)
    : null

  const hasActiveProgress =
    Boolean(progress) &&
    summary.vc_processing > 0 &&
    (input.chunkId === undefined ||
      progressEvent?.chunk_id === input.chunkId)

  if (!hasActiveProgress || !progress) {
    const avgDuration = averageVcChunkDuration(events, projectId, partId)
    const remaining = remainingVcChunksAfterCurrent(
      totalChunks,
      completedChunks,
      summary.vc_processing,
    )
    const overallEtaSeconds =
      avgDuration !== null && remaining > 0
        ? calculatePartEtaSeconds(0, avgDuration, remaining)
        : null

    return {
      ...empty,
      completedChunks,
      totalChunks,
      progressPercent,
      overallEtaSeconds,
      overallEtaAvailable: avgDuration !== null,
    }
  }

  const currentChunkId = progressEvent?.chunk_id ?? null
  const currentChunkPosition =
    summary.vc_processing > 0 ? completedChunks + 1 : null
  const currentChunkEtaSeconds =
    progress.estimated_remaining_seconds > 0
      ? progress.estimated_remaining_seconds
      : null

  const avgDuration = averageVcChunkDuration(events, projectId, partId)
  const remaining = remainingVcChunksAfterCurrent(
    totalChunks,
    completedChunks,
    summary.vc_processing,
  )
  const overallEtaSeconds =
    avgDuration !== null
      ? calculatePartEtaSeconds(
          progress.estimated_remaining_seconds,
          avgDuration,
          remaining,
        )
      : null

  return {
    currentChunkId,
    currentStep: progress.current_step,
    totalSteps: progress.total_steps,
    completedChunks,
    totalChunks,
    currentChunkPosition,
    currentChunkEtaSeconds,
    overallEtaSeconds,
    progressPercent,
    stepPercent: vcProgressPercent(progress),
    hasActiveProgress: true,
    overallEtaAvailable: avgDuration !== null,
  }
}
