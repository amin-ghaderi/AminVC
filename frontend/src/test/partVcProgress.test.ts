import { describe, expect, it } from 'vitest'

import {
  averageVcChunkDuration,
  calculatePartEtaSeconds,
  computePartVcProgress,
  dedupeVcCompletionDurations,
  remainingVcChunksAfterCurrent,
} from '@/lib/partVcProgress'
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
      current_step: 17,
      total_steps: 30,
      elapsed_seconds: 100,
      estimated_remaining_seconds: 240,
    },
    ...overrides,
  }
}

function completionEvent(
  chunkId: number,
  duration: number,
  timestamp: string,
): EventEnvelope {
  return {
    event_id: `c-${chunkId}-${timestamp}`,
    event_type: 'vc.chunk_completed',
    timestamp,
    project_id: 'demo',
    part_id: 'part-1',
    chunk_id: chunkId,
    payload: { duration_seconds: duration },
  }
}

describe('partVcProgress', () => {
  it('dedupes completion durations by chunk', () => {
    const events = [
      completionEvent(1, 480, '2026-01-01T10:00:00Z'),
      completionEvent(1, 60, '2026-01-01T11:00:00Z'),
      completionEvent(2, 540, '2026-01-01T10:30:00Z'),
    ]
    const map = dedupeVcCompletionDurations(events, 'demo', 'part-1')
    expect(map.get(1)).toBe(60)
    expect(map.get(2)).toBe(540)
  })

  it('returns null average when no completions', () => {
    expect(averageVcChunkDuration([], 'demo', 'part-1')).toBeNull()
  })

  it('calculates part ETA from formula', () => {
    expect(calculatePartEtaSeconds(240, 480, 4)).toBe(240 + 480 * 4)
  })

  it('remaining chunks subtracts in-flight chunk', () => {
    expect(remainingVcChunksAfterCurrent(7, 2, 1)).toBe(4)
  })

  it('computes part progress percent from vc_ready', () => {
    const view = computePartVcProgress({
      events: [],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.completedChunks).toBe(2)
    expect(view.totalChunks).toBe(7)
    expect(view.progressPercent).toBe(28)
  })

  it('computes overall ETA when completions exist', () => {
    const events = [
      progressEvent({}),
      completionEvent(1, 480, '2026-01-01T09:00:00Z'),
      completionEvent(2, 600, '2026-01-01T09:30:00Z'),
    ]
    const view = computePartVcProgress({
      events,
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.overallEtaAvailable).toBe(true)
    expect(view.overallEtaSeconds).toBe(240 + 540 * 4)
  })

  it('shows learning state when no completion history', () => {
    const view = computePartVcProgress({
      events: [progressEvent({})],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
    })
    expect(view.overallEtaAvailable).toBe(false)
    expect(view.overallEtaSeconds).toBeNull()
  })

  it('hides active chunk when requireChunkProcessing and not processing', () => {
    const view = computePartVcProgress({
      events: [progressEvent({})],
      summary: summaryBase,
      projectId: 'demo',
      partId: 'part-1',
      chunkId: 3,
      requireChunkProcessing: true,
      chunkIsProcessing: false,
    })
    expect(view.hasActiveProgress).toBe(false)
  })
})
