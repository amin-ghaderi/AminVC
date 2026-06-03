import { describe, expect, it } from 'vitest'

import {
  findLatestVcProgress,
  findLatestVcProgressEventForPart,
  vcProgressPercent,
} from '@/lib/vcProgress'
import type { EventEnvelope } from '@/types/api'

describe('vcProgress', () => {
  it('extracts latest vc.progress event', () => {
    const events: EventEnvelope[] = [
      {
        event_id: '1',
        event_type: 'vc.progress',
        timestamp: '2026-01-01T10:00:00Z',
        project_id: null,
        part_id: null,
        chunk_id: null,
        payload: { current_step: 5, total_steps: 30, elapsed_seconds: 10, estimated_remaining_seconds: 50 },
      },
      {
        event_id: '2',
        event_type: 'vc.progress',
        timestamp: '2026-01-01T11:00:00Z',
        project_id: null,
        part_id: null,
        chunk_id: null,
        payload: {
          current_step: 12,
          total_steps: 30,
          elapsed_seconds: 48,
          estimated_remaining_seconds: 72,
        },
      },
    ]
    const progress = findLatestVcProgress(events)
    expect(progress?.current_step).toBe(12)
    expect(progress?.total_steps).toBe(30)
  })

  it('finds latest progress for a part and chunk', () => {
    const events: EventEnvelope[] = [
      {
        event_id: '1',
        event_type: 'vc.progress',
        timestamp: '2026-01-01T11:00:00Z',
        project_id: 'demo',
        part_id: 'part-1',
        chunk_id: 1,
        payload: { current_step: 5, total_steps: 30, elapsed_seconds: 0, estimated_remaining_seconds: 0 },
      },
      {
        event_id: '2',
        event_type: 'vc.progress',
        timestamp: '2026-01-01T12:00:00Z',
        project_id: 'demo',
        part_id: 'part-1',
        chunk_id: 2,
        payload: { current_step: 12, total_steps: 30, elapsed_seconds: 0, estimated_remaining_seconds: 0 },
      },
    ]
    const event = findLatestVcProgressEventForPart(events, 'demo', 'part-1', 2)
    expect(event?.chunk_id).toBe(2)
    expect(event?.payload.current_step).toBe(12)
  })

  it('calculates progress bar percent', () => {
    expect(
      vcProgressPercent({
        current_step: 12,
        total_steps: 30,
        elapsed_seconds: 48,
        estimated_remaining_seconds: 72,
      }),
    ).toBe(40)
  })
})
