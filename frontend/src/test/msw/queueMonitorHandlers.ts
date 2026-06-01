import { http, HttpResponse } from 'msw'

import {
  getRecentEventsForMock,
  syncRecentEvents,
} from '@/test/msw/recentEventsStore'
import { getWorkspaceEventsForMock } from '@/test/msw/workspaceHandlers'
import type { EventEnvelope, QueueJobsResponse, QueueSnapshot } from '@/types/api'

const API = '/api/v1'

const defaultJobs: QueueJobsResponse = {
  queued: [
    {
      job_id: 'job-q-1',
      job_type: 'narration',
      project_id: 'demo',
      part_id: 'part-1',
      chunk_id: 1,
      status: 'queued',
      created_at: '2026-01-01T10:00:00Z',
      started_at: null,
      completed_at: null,
      attempts: 0,
      last_error: null,
    },
    {
      job_id: 'job-q-2',
      job_type: 'vc',
      project_id: 'demo',
      part_id: 'part-2',
      chunk_id: 2,
      status: 'queued',
      created_at: '2026-01-01T10:05:00Z',
      started_at: null,
      completed_at: null,
      attempts: 0,
      last_error: null,
    },
  ],
  running: [
    {
      job_id: 'job-r-1',
      job_type: 'vc',
      project_id: 'demo',
      part_id: 'part-3',
      chunk_id: 3,
      status: 'running',
      created_at: '2026-01-01T09:00:00Z',
      started_at: '2026-01-01T09:01:00Z',
      completed_at: null,
      attempts: 1,
      last_error: null,
    },
  ],
  completed: [
    {
      job_id: 'job-c-1',
      job_type: 'narration',
      project_id: 'demo',
      part_id: 'part-4',
      chunk_id: 4,
      status: 'completed',
      created_at: '2026-01-01T08:00:00Z',
      started_at: '2026-01-01T08:01:00Z',
      completed_at: '2026-01-01T08:02:00Z',
      attempts: 1,
      last_error: null,
    },
  ],
  failed: [
    {
      job_id: 'job-f-1',
      job_type: 'narration',
      project_id: 'demo',
      part_id: 'part-5',
      chunk_id: 5,
      status: 'failed',
      created_at: '2026-01-01T07:00:00Z',
      started_at: '2026-01-01T07:01:00Z',
      completed_at: '2026-01-01T07:02:00Z',
      attempts: 2,
      last_error: 'TTS quota exceeded',
    },
  ],
  cancelled: [],
}

const defaultSnapshot: QueueSnapshot = {
  queued: 2,
  running: 1,
  completed: 3,
  failed: 1,
  cancelled: 0,
}

const defaultEvents: EventEnvelope[] = [
  {
    event_id: 'ev-1',
    event_type: 'queue.job_queued',
    timestamp: '2026-01-02T10:00:00Z',
    project_id: 'demo',
    part_id: 'part-1',
    chunk_id: 1,
    payload: { job_type: 'narration' },
  },
  {
    event_id: 'ev-2',
    event_type: 'worker.job_started',
    timestamp: '2026-01-02T10:01:00Z',
    project_id: 'demo',
    part_id: 'part-3',
    chunk_id: 3,
    payload: {},
  },
  {
    event_id: 'ev-3',
    event_type: 'vc.progress',
    timestamp: '2026-01-02T10:02:00Z',
    project_id: 'demo',
    part_id: 'part-3',
    chunk_id: 3,
    payload: {
      current_step: 12,
      total_steps: 30,
      elapsed_seconds: 48,
      estimated_remaining_seconds: 72,
    },
  },
  {
    event_id: 'ev-4',
    event_type: 'narration.approved',
    timestamp: '2026-01-02T09:00:00Z',
    project_id: 'demo',
    part_id: 'part-2',
    chunk_id: 2,
    payload: {},
  },
]

let monitorSnapshot = { ...defaultSnapshot }
let monitorJobs: QueueJobsResponse = structuredClone(defaultJobs)
let monitorEvents: EventEnvelope[] = [...defaultEvents]

function publishMonitorEvents() {
  syncRecentEvents(getWorkspaceEventsForMock(), monitorEvents)
}

export function resetQueueMonitorData() {
  monitorSnapshot = { ...defaultSnapshot }
  monitorJobs = structuredClone(defaultJobs)
  monitorEvents = [...defaultEvents]
  publishMonitorEvents()
}

export function getMonitorEventsForMock() {
  return monitorEvents
}

export function setMonitorEvents(events: EventEnvelope[]) {
  monitorEvents = events
  publishMonitorEvents()
}

export function setMonitorSnapshot(snapshot: QueueSnapshot) {
  monitorSnapshot = snapshot
}

export function getMonitorJobs() {
  return monitorJobs
}

export function setMonitorJobs(jobs: QueueJobsResponse) {
  monitorJobs = structuredClone(jobs)
}

export function queueBuildJob(
  projectId: string,
  partId: string,
  buildId: string,
) {
  monitorJobs = {
    ...monitorJobs,
    queued: [
      ...monitorJobs.queued.filter((j) => j.job_id !== buildId),
      {
        job_id: buildId,
        job_type: 'build',
        project_id: projectId,
        part_id: partId,
        chunk_id: null,
        status: 'queued',
        created_at: '2026-01-03T10:05:00Z',
        started_at: null,
        completed_at: null,
        attempts: 0,
        last_error: null,
      },
    ],
  }
}

export function removeQueuedBuildJob(buildId: string) {
  removeQueued(buildId)
}

export function pushMonitorEvent(event: EventEnvelope) {
  monitorEvents = [...monitorEvents, event]
  publishMonitorEvents()
}

function removeQueued(jobId: string) {
  const cancelledJob = monitorJobs.queued.find((j) => j.job_id === jobId)
  monitorJobs = {
    ...monitorJobs,
    queued: monitorJobs.queued.filter((j) => j.job_id !== jobId),
    cancelled: cancelledJob
      ? [...monitorJobs.cancelled, { ...cancelledJob, status: 'cancelled' }]
      : monitorJobs.cancelled,
  }
  monitorSnapshot = {
    ...monitorSnapshot,
    queued: monitorJobs.queued.length,
    cancelled: monitorJobs.cancelled.length,
  }
}

export const queueMonitorHandlers = [
  http.get(`${API}/queue`, () => HttpResponse.json(monitorSnapshot)),
  http.get(`${API}/queue/jobs`, () => HttpResponse.json(monitorJobs)),
  http.post(`${API}/queue/cancel/:jobId`, ({ params }) => {
    removeQueued(String(params.jobId))
    return HttpResponse.json({ job_id: String(params.jobId), status: 'cancelled' })
  }),
  http.get(`${API}/events/recent`, () => HttpResponse.json(getRecentEventsForMock())),
]
