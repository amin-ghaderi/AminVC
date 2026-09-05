import { http, HttpResponse } from 'msw'

import type { Part, Project, QueueSnapshot, WorkerStatus } from '@/types/api'
import {
  buildManagerHandlers,
  resetBuildManagerData,
} from '@/test/msw/buildManagerHandlers'
import {
  queueMonitorHandlers,
  resetQueueMonitorData,
  setMonitorSnapshot,
} from '@/test/msw/queueMonitorHandlers'
import {
  resetWorkspaceData,
  workspaceHandlers,
} from '@/test/msw/workspaceHandlers'

const API = '/api/v1'

let projects: Project[] = [
  {
    project_id: 'demo',
    title: 'Demo Project',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    status: 'active',
    parts: [],
  },
]

let partsByProject: Record<string, Part[]> = {}
const partSourceUploaded = new Set<string>()
const partExtractedText: Record<string, string> = {}
const partChunkCounts: Record<string, number> = {}

function partKey(projectId: string, partId: string) {
  return `${projectId}:${partId}`
}

let workerStatus: WorkerStatus = { running: false, state: 'idle' }

export {
  resetWorkspaceData,
  setWorkspaceReferenceExists,
} from '@/test/msw/workspaceHandlers'

export { resetQueueMonitorData } from '@/test/msw/queueMonitorHandlers'
export { resetBuildManagerData } from '@/test/msw/buildManagerHandlers'

export function resetTestData() {
  resetWorkspaceData()
  resetQueueMonitorData() // publishes merged recent events for MSW
  resetBuildManagerData()
  projects = [
    {
      project_id: 'demo',
      title: 'Demo Project',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      status: 'active',
      parts: [],
    },
  ]
  partsByProject = {}
  partSourceUploaded.clear()
  for (const key of Object.keys(partExtractedText)) {
    delete partExtractedText[key]
  }
  for (const key of Object.keys(partChunkCounts)) {
    delete partChunkCounts[key]
  }
  workerStatus = { running: false, state: 'idle' }
}

export function setProjectsList(list: Project[]) {
  projects = list
}

export function setWorkerStatus(status: WorkerStatus) {
  workerStatus = status
}

export function setQueueSnapshot(snapshot: QueueSnapshot) {
  setMonitorSnapshot(snapshot)
}

export const handlers = [
  http.get(`${API}/projects`, () => HttpResponse.json(projects)),
  http.get(`${API}/projects/:projectId`, ({ params }) => {
    const project = projects.find((p) => p.project_id === params.projectId)
    if (!project) {
      return HttpResponse.json({ error: 'Project not found' }, { status: 404 })
    }
    return HttpResponse.json(project)
  }),
  http.post(`${API}/projects`, async ({ request }) => {
    const body = (await request.json()) as { project_id: string; title: string }
    const project: Project = {
      project_id: body.project_id,
      title: body.title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'active',
      parts: [],
    }
    projects = [...projects, project]
    return HttpResponse.json(project, { status: 201 })
  }),
  http.get(`${API}/projects/:projectId/parts`, ({ params }) => {
    const list = partsByProject[String(params.projectId)] ?? []
    return HttpResponse.json(list)
  }),
  http.post(`${API}/projects/:projectId/parts`, async ({ params, request }) => {
    const body = (await request.json()) as { part_id?: string; title: string }
    const projectId = String(params.projectId)
    const part: Part = {
      part_id: body.part_id ?? 'auto-part',
      project_id: projectId,
      title: body.title,
      state: 'created',
      processing_profile: 'default',
      reference_audio: { exists: false, path: null, size_bytes: null },
      chunks_total: 0,
      chunks_completed_narration: 0,
      chunks_completed_vc: 0,
      current_chunk: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    const list = partsByProject[projectId] ?? []
    partsByProject[projectId] = [...list, part]
    const project = projects.find((p) => p.project_id === projectId)
    if (project) {
      project.parts = [...project.parts, part.part_id]
    }
    return HttpResponse.json(part, { status: 201 })
  }),
  http.post(
    `${API}/projects/:projectId/parts/:partId/source`,
    async ({ params }) => {
      const key = partKey(String(params.projectId), String(params.partId))
      partSourceUploaded.add(key)
      return HttpResponse.json({
        filename: 'source.pdf',
        size_bytes: 2048,
        path: 'source/source.pdf',
      })
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/extract-text`,
    ({ params }) => {
      const key = partKey(String(params.projectId), String(params.partId))
      const text =
        partExtractedText[key] ??
        'این یک متن نمونه برای آزمایش استخراج است. '.repeat(20)
      partExtractedText[key] = text
      return HttpResponse.json({ text })
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunking`,
    async ({ params, request }) => {
      const body = (await request.json()) as { text: string; chunk_size: number }
      const count = Math.max(1, Math.ceil(body.text.length / body.chunk_size))
      const key = partKey(String(params.projectId), String(params.partId))
      partChunkCounts[key] = count
      const projectId = String(params.projectId)
      const partId = String(params.partId)
      const list = partsByProject[projectId] ?? []
      const idx = list.findIndex((p) => p.part_id === partId)
      if (idx >= 0) {
        list[idx] = { ...list[idx], chunks_total: count }
      }
      return HttpResponse.json({ chunks_created: count }, { status: 201 })
    },
  ),
  http.get(
    `${API}/projects/:projectId/parts/:partId/summary`,
    ({ params }) => {
      const projectId = String(params.projectId)
      const partId = String(params.partId)
      if (projectId === 'demo' && partId === 'part-3') {
        return HttpResponse.json({
          total_chunks: 7,
          narration_ready: 5,
          narration_approved: 5,
          vc_ready: 2,
          vc_approved: 0,
          vc_queued: 4,
          vc_processing: 1,
          failed: 0,
          interrupted: 0,
        })
      }
      const key = partKey(projectId, partId)
      const total = partChunkCounts[key] ?? 0
      return HttpResponse.json({
        total_chunks: total,
        narration_ready: 0,
        narration_approved: 0,
        vc_ready: 0,
        vc_approved: 0,
        vc_queued: 0,
        vc_processing: 0,
        failed: 0,
        interrupted: 0,
      })
    },
  ),
  http.get(`${API}/worker`, () => HttpResponse.json(workerStatus)),
  http.post(`${API}/worker/start`, () => {
    workerStatus = { ...workerStatus, running: true, state: 'IDLE' }
    return HttpResponse.json({ status: 'started' })
  }),
  http.post(`${API}/worker/stop`, () => {
    workerStatus = { ...workerStatus, running: false, state: 'STOPPED' }
    return HttpResponse.json({ status: 'stopped' })
  }),
  http.get('/agent/status/:deviceId', ({ params }) =>
    HttpResponse.json({
      device_id: String(params.deviceId),
      online: false,
      last_seen: null,
    }),
  ),
  ...queueMonitorHandlers,
  ...buildManagerHandlers,
  ...workspaceHandlers,
]
