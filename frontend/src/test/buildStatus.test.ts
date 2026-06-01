import { describe, expect, it } from 'vitest'

import { deriveBuildStatus } from '@/lib/buildStatus'
import type { QueueJobsResponse } from '@/types/api'

const emptyJobs: QueueJobsResponse = {
  queued: [],
  running: [],
  completed: [],
  failed: [],
  cancelled: [],
}

describe('deriveBuildStatus', () => {
  it('returns Created by default', () => {
    expect(deriveBuildStatus('build-001', emptyJobs)).toBe('Created')
  })

  it('returns Queued when job is queued', () => {
    const jobs: QueueJobsResponse = {
      ...emptyJobs,
      queued: [
        {
          job_id: 'build-001',
          job_type: 'build',
          project_id: 'demo',
          part_id: 'part-ws',
          chunk_id: null,
          status: 'queued',
          created_at: '',
          started_at: null,
          completed_at: null,
          attempts: 0,
          last_error: null,
        },
      ],
    }
    expect(deriveBuildStatus('build-001', jobs)).toBe('Queued')
  })

  it('returns Completed when download is available', () => {
    expect(
      deriveBuildStatus('build-001', emptyJobs, { downloadAvailable: true }),
    ).toBe('Completed')
  })
})
