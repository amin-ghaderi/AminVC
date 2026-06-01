import { http, HttpResponse } from 'msw'

import type { Chunk, EventEnvelope, Part } from '@/types/api'

const API = '/api/v1'

let workspaceChunks: Chunk[] = []
let workspaceEvents: EventEnvelope[] = []

const emptySlot = { status: '', file: null, duration_seconds: null }

export function getWorkspaceEventsForMock() {
  return workspaceEvents
}

export function resetWorkspaceData() {
  workspaceChunks = [
    makeChunk(1, 'NarrationReady', 'Alpha text chunk', false, false, true, false),
    makeChunk(2, 'NarrationApproved', 'Beta approved', true, false, true, false),
    makeChunk(3, 'VCReady', 'Gamma vc ready', true, true, false, true),
    makeChunk(4, 'VCApproved', 'Delta done', true, true, false, true),
    makeChunk(5, 'NarrationFailed', 'Epsilon failed', false, false, false, false),
    makeChunk(6, 'TextSaved', 'No audio yet', false, false, false, false),
  ]
  workspaceEvents = [
    {
      event_id: 'e1',
      event_type: 'narration.approved',
      timestamp: '2026-01-02T10:00:00Z',
      project_id: 'demo',
      part_id: 'part-ws',
      chunk_id: 2,
      payload: { message: 'Narration approved' },
    },
    {
      event_id: 'e2',
      event_type: 'queue.job_queued',
      timestamp: '2026-01-02T11:00:00Z',
      project_id: 'demo',
      part_id: 'part-ws',
      chunk_id: 1,
      payload: { job_type: 'narration' },
    },
    {
      event_id: 'e3',
      event_type: 'other.event',
      timestamp: '2026-01-02T12:00:00Z',
      project_id: 'other',
      part_id: 'other',
      chunk_id: 99,
      payload: {},
    },
  ]
}

function makeChunk(
  id: number,
  state: string,
  text: string,
  narrationApproved: boolean,
  vcApproved: boolean,
  narrationExists: boolean,
  vcExists: boolean,
): Chunk {
  return {
    chunk_id: id,
    state,
    narration_approved: narrationApproved,
    vc_approved: vcApproved,
    text,
    narration: narrationExists
      ? { status: 'ready', file: 'narration.wav', duration_seconds: 1.2 }
      : emptySlot,
    vc: vcExists
      ? { status: 'ready', file: 'vc.wav', duration_seconds: 1.0 }
      : emptySlot,
    retry_count: 0,
    last_error: null,
    updated_at: new Date().toISOString(),
  }
}

export function getWorkspaceChunks() {
  return workspaceChunks
}

export function setWorkspaceChunk(chunk: Chunk) {
  workspaceChunks = workspaceChunks.map((c) =>
    c.chunk_id === chunk.chunk_id ? chunk : c,
  )
}

export const workspaceHandlers = [
  http.get(`${API}/projects/:projectId/parts/:partId`, ({ params }) => {
    const part: Part = {
      part_id: String(params.partId),
      project_id: String(params.projectId),
      title: 'Workspace Part',
      state: 'TextSaved',
      processing_profile: 'default',
      chunks_total: workspaceChunks.length,
      chunks_completed_narration: 0,
      chunks_completed_vc: 0,
      current_chunk: null,
      created_at: '',
      updated_at: '',
    }
    return HttpResponse.json(part)
  }),
  http.get(`${API}/projects/:projectId/parts/:partId/summary`, () =>
    HttpResponse.json({
      total_chunks: workspaceChunks.length,
      narration_ready: workspaceChunks.filter((c) => c.state === 'NarrationReady')
        .length,
      narration_approved: workspaceChunks.filter((c) => c.narration_approved).length,
      vc_ready: workspaceChunks.filter((c) => c.state === 'VCReady').length,
      vc_approved: workspaceChunks.filter((c) => c.vc_approved).length,
      failed: workspaceChunks.filter(
        (c) => c.state === 'NarrationFailed' || c.state === 'VCFailed',
      ).length,
      interrupted: workspaceChunks.filter((c) => c.state === 'Interrupted').length,
    }),
  ),
  http.get(`${API}/projects/:projectId/parts/:partId/chunks`, () =>
    HttpResponse.json(workspaceChunks),
  ),
  http.get(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId`,
    ({ params }) => {
      const chunk = workspaceChunks.find(
        (c) => c.chunk_id === Number(params.chunkId),
      )
      if (!chunk) {
        return HttpResponse.json({ error: 'Chunk not found' }, { status: 404 })
      }
      return HttpResponse.json(chunk)
    },
  ),
  http.put(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/text`,
    async ({ params, request }) => {
      const body = (await request.json()) as { text: string }
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)
      if (!chunk) {
        return HttpResponse.json({ error: 'not found' }, { status: 404 })
      }
      const updated = { ...chunk, text: body.text, state: 'TextSaved' }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/approve-narration`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = {
        ...chunk,
        state: 'NarrationApproved',
        narration_approved: true,
      }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/unapprove-narration`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = {
        ...chunk,
        state: 'NarrationReady',
        narration_approved: false,
      }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/approve-vc`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = { ...chunk, state: 'VCApproved', vc_approved: true }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/unapprove-vc`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = { ...chunk, state: 'VCReady', vc_approved: false }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/rebuild-narration`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = {
        ...chunk,
        state: 'NarrationQueued',
        narration: emptySlot,
        vc: emptySlot,
        vc_approved: false,
        narration_approved: false,
      }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.post(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/rebuild-vc`,
    ({ params }) => {
      const id = Number(params.chunkId)
      const chunk = workspaceChunks.find((c) => c.chunk_id === id)!
      const updated = { ...chunk, state: 'VCQueued', vc: emptySlot, vc_approved: false }
      setWorkspaceChunk(updated)
      return HttpResponse.json(updated)
    },
  ),
  http.get(
    `${API}/projects/:projectId/parts/:partId/chunks/:chunkId/assets`,
    ({ params }) => {
      const chunk = workspaceChunks.find(
        (c) => c.chunk_id === Number(params.chunkId),
      )!
      const pid = String(params.projectId)
      const partId = String(params.partId)
      const cid = chunk.chunk_id
      const base = `/api/v1/projects/${pid}/parts/${partId}/chunks/${cid}`
      return HttpResponse.json({
        narration_exists: Boolean(chunk.narration.file),
        vc_exists: Boolean(chunk.vc.file),
        narration_url: `${base}/audio/narration`,
        vc_url: `${base}/audio/vc`,
        narration_size: chunk.narration.file ? 12000 : null,
        vc_size: chunk.vc.file ? 15000 : null,
      })
    },
  ),
  http.post(`${API}/queue/narration`, () =>
    HttpResponse.json({ job_id: 'j1', status: 'queued' }),
  ),
  http.post(`${API}/queue/vc`, async ({ request }) => {
    const body = (await request.json()) as {
      project_id: string
      part_id: string
      chunk_id: number
    }
    const chunk = workspaceChunks.find((c) => c.chunk_id === body.chunk_id)
    if (!chunk?.narration_approved && chunk?.state !== 'NarrationApproved') {
      return HttpResponse.json(
        { error: 'Narration approval required before VC can be queued' },
        { status: 409 },
      )
    }
    return HttpResponse.json({ job_id: 'j2', status: 'queued' })
  }),
]
