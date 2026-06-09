import { describe, expect, it } from 'vitest'

import {
  averageSegmentDuration,
  calculateChunkEtaSeconds,
  completedSegmentDurationsForChunk,
  computePartVcProgress,
  dedupeVcCompletionDurations,
  remainingVcChunksAfterCurrent,
} from '@/lib/partVcProgress'
import { hasSegmentProgress, parseVcProgressPayload } from '@/lib/vcProgress'
import type { EventEnvelope, PartSummary } from '@/types/api'

const summaryBase: PartSummary = {
  total_chunks: 7,
  narration_ready: 5,
  narration_approved: 5,
  vc_ready: 2,
  vc_approved: 0,
  vc_queued: 4,
  vc_processing: 1,
  failed: 0,
  interrupted: 0,
}

function progressEvent(
  overrides: Partial<EventEnvelope> & { payload?: Record<string, unknown> },
): EventEnvelope {
  return {
    event_id: 'p1',
    event_type: 'vc.progress',
    timestamp: '2026-06-01T12:00:00Z',
    project_id: 'demo',
    part_id: 'part-1',
    chunk_id: 3,
    payload: {
      current_step: 11,
      total_steps: 30,
      elapsed_seconds: 100,
      estimated_remaining_seconds: 240,
      segment_index: 3,
      segment_total: 8,
    },
    ...overrides,
  }
}

describe('vcProgress segment parsing', () => {
  it('parses segment fields', () => {
    const p = parseVcProgressPayload({
      current_step: 11,
      total_steps: 30,
      segment_index: 3,
      segment_total: 8,
    })
    expect(p && hasSegmentProgress(p)).toBe(true)
  })

  it('falls back when segment fields missing', () => {
    const p = parseVcProgressPayload({ current_step: 1, total_steps: 30 })
    expect(p && hasSegmentProgress(p)).toBe(false)
  })
})

describe('partVcProgress', () => {
  it('computes chunk ETA with segment history', () => {
    const result = calculateChunkEtaSeconds(240, 3, 8, 120)
    expect(result.learning).toBe(false)
    expect(result.seconds).toBe(240 + 120 * 5)
  })

  it('chunk ETA learning without segment history', () => {
    const result = calculateChunkEtaSeconds(240, 3, 8, null)
    expect(result.learning).toBe(true)
  })

  it('derives completed segment durations from events', () => {
    const events: EventEnvelope[] = [
      progressEvent({ timestamp: '2026-06-01T12:00:00Z', payload: { current_step: 1, total_steps: 30, segment_index: 1, segment_total: 3, elapsed_seconds: 0, estimated_remaining_seconds: 0 } }),
      progressEvent({ timestamp: '2026-06-01T12:02:00Z', payload: { current_step: 30, total_steps: 30, segment_index: 1, segment_total: 3, elapsed_seconds: 120, estimated_remaining_seconds: 0 } }),
      progressEvent({ timestamp: '2026-06-01T12:02:10Z', payload: { current_step: 1, total_steps: 30, segment_index: 2, segment_total: 3, elapsed_seconds: 0, estimated_remaining_seconds: 0 } }),
    ]
    const durations = completedSegmentDurationsForChunk(events, 'demo', 'part-1', 3)
    expect(durations.length).toBe(1)
    expect(durations[0]).toBe(10)
  })

  it('exposes segment index in active view', () => {
    const view = computePartVcProgress({
      events: [progressEvent({})],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.hasSegmentProgress).toBe(true)
    expect(view.segmentIndex).toBe(3)
    expect(view.segmentTotal).toBe(8)
    expect(view.narrationChunkPosition).toBe(3)
  })

  it('falls back without segment fields', () => {
    const view = computePartVcProgress({
      events: [
        progressEvent({
          payload: {
            current_step: 5,
            total_steps: 30,
            elapsed_seconds: 0,
            estimated_remaining_seconds: 60,
          },
        }),
      ],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.hasActiveProgress).toBe(true)
    expect(view.hasSegmentProgress).toBe(false)
    expect(view.segmentIndex).toBeNull()
    expect(view.currentStep).toBe(5)
    expect(view.totalSteps).toBe(30)
  })

  it('activates hierarchy when vc.progress exists even if vc_processing is 0', () => {
    const view = computePartVcProgress({
      events: [progressEvent({ payload: { current_step: 13, total_steps: 30, elapsed_seconds: 10, estimated_remaining_seconds: 200 } })],
      summary: { ...summaryBase, vc_processing: 0 },
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.hasActiveProgress).toBe(true)
    expect(view.currentStep).toBe(13)
    expect(view.totalSteps).toBe(30)
    expect(view.narrationChunkPosition).toBe(3)
  })

  it('shows segment section when segment fields are present', () => {
    const view = computePartVcProgress({
      events: [progressEvent({})],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.hasActiveProgress).toBe(true)
    expect(view.hasSegmentProgress).toBe(true)
    expect(view.segmentIndex).toBe(3)
    expect(view.segmentTotal).toBe(8)
  })

  it('scopes active progress to chunk when chunkId is provided', () => {
    const view = computePartVcProgress({
      events: [progressEvent({ chunk_id: 5 })],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
      chunkId: 3,
      requireChunkProcessing: true,
      chunkIsProcessing: true,
    })
    expect(view.hasActiveProgress).toBe(false)
  })

  it('activates for scoped chunk when chunkId matches progress event', () => {
    const view = computePartVcProgress({
      events: [progressEvent({ chunk_id: 3 })],
      summary: { ...summaryBase, vc_processing: 0 },
      projectId: 'demo',
      partId: 'part-1',
      chunkId: 3,
      requireChunkProcessing: true,
      chunkIsProcessing: true,
    })
    expect(view.hasActiveProgress).toBe(true)
    expect(view.currentStep).toBe(11)
  })

  it('stays inactive without matching vc.progress events', () => {
    const view = computePartVcProgress({
      events: [],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.hasActiveProgress).toBe(false)
  })
})
