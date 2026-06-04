import type { EventEnvelope, PartSummary, VcProgressPayload } from '@/types/api'

import {
  findLatestVcProgressEventForPart,
  hasSegmentProgress,
  parseVcProgressPayload,
  vcProgressPercent,
} from '@/lib/vcProgress'

export interface PartVcProgressView {
  currentChunkId: number | null
  narrationChunkPosition: number | null
  currentStep: number
  totalSteps: number
  segmentIndex: number | null
  segmentTotal: number | null
  completedChunks: number
  totalChunks: number
  segmentEtaSeconds: number | null
  chunkEtaSeconds: number | null
  chunkEtaLearning: boolean
  overallEtaSeconds: number | null
  progressPercent: number
  stepPercent: number
  hasActiveProgress: boolean
  hasSegmentProgress: boolean
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

/** Completed internal segment durations within the current chunk (from vc.progress history). */
export function completedSegmentDurationsForChunk(
  events: EventEnvelope[],
  projectId: string,
  partId: string,
  chunkId: number,
): number[] {
  const sorted = events
    .filter(
      (e) =>
        e.event_type === 'vc.progress' &&
        e.project_id === projectId &&
        e.part_id === partId &&
        e.chunk_id === chunkId,
    )
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp))

  const durations: number[] = []
  let lastSegment: number | null = null
  let lastTimestamp: string | null = null

  for (const event of sorted) {
    const progress = parseVcProgressPayload(event.payload)
    if (!progress || !hasSegmentProgress(progress)) continue
    const seg = progress.segment_index!
    if (lastSegment !== null && seg !== lastSegment && lastTimestamp) {
      const elapsed =
        (new Date(event.timestamp).getTime() - new Date(lastTimestamp).getTime()) /
        1000
      if (elapsed > 0) durations.push(elapsed)
    }
    lastSegment = seg
    lastTimestamp = event.timestamp
  }
  return durations
}

export function averageSegmentDuration(durations: number[]): number | null {
  if (!durations.length) return null
  return durations.reduce((sum, d) => sum + d, 0) / durations.length
}

export function calculateChunkEtaSeconds(
  segmentRemainingSeconds: number,
  segmentIndex: number,
  segmentTotal: number,
  avgSegmentDuration: number | null,
): { seconds: number | null; learning: boolean } {
  if (avgSegmentDuration === null) {
    return { seconds: null, learning: true }
  }
  const remainingSegments = Math.max(0, segmentTotal - segmentIndex)
  return {
    seconds: segmentRemainingSeconds + avgSegmentDuration * remainingSegments,
    learning: false,
  }
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
    narrationChunkPosition: null,
    currentStep: 0,
    totalSteps: 0,
    segmentIndex: null,
    segmentTotal: null,
    completedChunks: 0,
    totalChunks: 0,
    segmentEtaSeconds: null,
    chunkEtaSeconds: null,
    chunkEtaLearning: false,
    overallEtaSeconds: null,
    progressPercent: 0,
    stepPercent: 0,
    hasActiveProgress: false,
    hasSegmentProgress: false,
    overallEtaAvailable: false,
  }

  if (!input.summary) return empty

  const { summary, projectId, partId } = input
  const totalChunks = summary.total_chunks
  const completedChunks = summary.vc_ready
  const progressPercent =
    totalChunks > 0 ? Math.floor((completedChunks / totalChunks) * 100) : 0
  const narrationChunkPosition =
    summary.vc_processing > 0 ? completedChunks + 1 : null

  if (input.requireChunkProcessing && !input.chunkIsProcessing) {
    return {
      ...empty,
      completedChunks,
      totalChunks,
      progressPercent,
      narrationChunkPosition,
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
      narrationChunkPosition,
      overallEtaSeconds,
      overallEtaAvailable: avgDuration !== null,
    }
  }

  const currentChunkId = progressEvent?.chunk_id ?? null
  const segmentVisible = hasSegmentProgress(progress)
  const segmentEtaSeconds =
    progress.estimated_remaining_seconds > 0
      ? progress.estimated_remaining_seconds
      : null

  let chunkEtaSeconds: number | null = null
  let chunkEtaLearning = false
  if (
    segmentVisible &&
    progress.segment_index != null &&
    progress.segment_total != null &&
    currentChunkId !== null
  ) {
    const segDurations = completedSegmentDurationsForChunk(
      events,
      projectId,
      partId,
      currentChunkId,
    )
    const avgSeg = averageSegmentDuration(segDurations)
    const chunkEta = calculateChunkEtaSeconds(
      progress.estimated_remaining_seconds,
      progress.segment_index,
      progress.segment_total,
      avgSeg,
    )
    chunkEtaSeconds = chunkEta.seconds
    chunkEtaLearning = chunkEta.learning
  }

  const chunkRemainingForPart =
    chunkEtaSeconds ?? progress.estimated_remaining_seconds
  const avgDuration = averageVcChunkDuration(events, projectId, partId)
  const remaining = remainingVcChunksAfterCurrent(
    totalChunks,
    completedChunks,
    summary.vc_processing,
  )
  const overallEtaSeconds =
    avgDuration !== null
      ? calculatePartEtaSeconds(
          chunkRemainingForPart,
          avgDuration,
          remaining,
        )
      : null

  return {
    currentChunkId,
    narrationChunkPosition,
    currentStep: progress.current_step,
    totalSteps: progress.total_steps,
    segmentIndex: progress.segment_index ?? null,
    segmentTotal: progress.segment_total ?? null,
    completedChunks,
    totalChunks,
    segmentEtaSeconds,
    chunkEtaSeconds,
    chunkEtaLearning,
    overallEtaSeconds,
    progressPercent,
    stepPercent: vcProgressPercent(progress),
    hasActiveProgress: true,
    hasSegmentProgress: segmentVisible,
    overallEtaAvailable: avgDuration !== null,
  }
}
