import { http, HttpResponse } from 'msw'

import type { Build, EventEnvelope } from '@/types/api'
import { pushMonitorEvent, queueBuildJob } from '@/test/msw/queueMonitorHandlers'

const API = '/api/v1'

const buildsByKey = new Map<string, Build[]>()
const downloadReady = new Set<string>()

function partKey(projectId: string, partId: string) {
  return `${projectId}:${partId}`
}

function buildKey(projectId: string, partId: string, buildId: string) {
  return `${partKey(projectId, partId)}:${buildId}`
}

export function resetBuildManagerData() {
  buildsByKey.clear()
  downloadReady.clear()
}

export function getBuildsForPart(projectId: string, partId: string) {
  return buildsByKey.get(partKey(projectId, partId)) ?? []
}

export function setBuildsForPart(projectId: string, partId: string, builds: Build[]) {
  buildsByKey.set(partKey(projectId, partId), builds)
}

export function setBuildDownloadReady(
  projectId: string,
  partId: string,
  buildId: string,
  ready: boolean,
) {
  const key = buildKey(projectId, partId, buildId)
  if (ready) {
    downloadReady.add(key)
  } else {
    downloadReady.delete(key)
  }
}

function nextBuildId(projectId: string, partId: string): string {
  const existing = getBuildsForPart(projectId, partId)
  const max = existing.reduce((acc, b) => {
    const match = /^build-(\d+)$/.exec(b.build_id)
    const n = match ? Number(match[1]) : 0
    return Math.max(acc, n)
  }, 0)
  return `build-${String(max + 1).padStart(3, '0')}`
}

export const buildManagerHandlers = [
  http.get(`${API}/projects/:projectId/parts/:partId/builds`, ({ params }) => {
    const list = getBuildsForPart(String(params.projectId), String(params.partId))
    return HttpResponse.json(list)
  }),
  http.post(`${API}/projects/:projectId/parts/:partId/builds`, async ({ params, request }) => {
    const body = (await request.json()) as { name: string; chunks: number[]; build_id?: string }
    const projectId = String(params.projectId)
    const partId = String(params.partId)
    const buildId = body.build_id ?? nextBuildId(projectId, partId)
    const build: Build = {
      build_id: buildId,
      project_id: projectId,
      part_id: partId,
      name: body.name,
      created_at: '2026-01-03T10:00:00Z',
      updated_at: '2026-01-03T10:00:00Z',
      chunks: body.chunks,
      output_file: `builds/${buildId}.wav`,
      duration_seconds: null,
    }
    const list = [...getBuildsForPart(projectId, partId), build]
    setBuildsForPart(projectId, partId, list)
    return HttpResponse.json(build, { status: 201 })
  }),
  http.get(
    `${API}/projects/:projectId/parts/:partId/builds/:buildId`,
    ({ params }) => {
      const build = getBuildsForPart(String(params.projectId), String(params.partId)).find(
        (b) => b.build_id === String(params.buildId),
      )
      if (!build) {
        return HttpResponse.json({ error: 'Build not found' }, { status: 404 })
      }
      return HttpResponse.json(build)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/builds/:buildId/queue`,
    ({ params }) => {
      const projectId = String(params.projectId)
      const partId = String(params.partId)
      const buildId = String(params.buildId)
      const build = getBuildsForPart(projectId, partId).find((b) => b.build_id === buildId)
      if (!build) {
        return HttpResponse.json({ error: 'Build not found' }, { status: 404 })
      }
      queueBuildJob(projectId, partId, buildId)
      const event: EventEnvelope = {
        event_id: `ev-build-q-${buildId}`,
        event_type: 'queue.job_queued',
        timestamp: '2026-01-03T10:05:00Z',
        project_id: projectId,
        part_id: partId,
        chunk_id: null,
        payload: { job_id: buildId, job_type: 'build' },
      }
      pushMonitorEvent(event)
      return HttpResponse.json({ job_id: buildId, job_type: 'build', status: 'queued' })
    },
  ),
  http.get(
    `${API}/projects/:projectId/parts/:partId/builds/:buildId/download`,
    ({ params }) => {
      const key = buildKey(
        String(params.projectId),
        String(params.partId),
        String(params.buildId),
      )
      if (!downloadReady.has(key)) {
        return HttpResponse.json({ error: 'Build output not found' }, { status: 404 })
      }
      return new HttpResponse(new Uint8Array([0x52, 0x49, 0x46, 0x46]), {
        headers: {
          'Content-Type': 'audio/wav',
          'Content-Disposition': `attachment; filename="${String(params.buildId)}.wav"`,
        },
      })
    },
  ),
]
