# E8.0 — Frontend / UI Architecture

Architecture-only specification for the AminVC React client. **No components, styling, or WebSocket** in this phase.

**Backend contract:** E7 REST API (`/api/v1`).

**Product pipeline:**

```text
Project → Part → Chunk → Narration → Approval → VC → Approval → Build → Download
```

---

## 1. Route map

| Path | Screen | Purpose |
|------|--------|---------|
| `/` | — | Redirect → `/projects` |
| `/projects` | Screen 1 — Projects | Book / project list |
| `/projects/:projectId` | Screen 2 — Project dashboard | Parts grid |
| `/projects/:projectId/parts/new` | Screen 3 — Create part | PDF → text → chunk quality → save |
| `/projects/:projectId/parts/:partId` | Screen 4 — Part workspace | Chunk list + details (primary) |
| `/projects/:projectId/parts/:partId/builds` | Screen 5 — Build manager | Manual merge |
| `/queue` | Screen 6 — Queue monitor | Execution visibility |
| `/progress` | Screen 7 — Live progress | VC progress + current job |
| `/events` | Screen 8 — Events | Diagnostics |

**Sidebar highlights:** Projects, Queue, Events, Builds (contextual: last part builds when inside a part).

**Layout shell:** All authenticated routes render inside `AppShell` (Header + Sidebar + `<Outlet />`).

---

## 2. Screen hierarchy

```text
App
├── AppShell
│   ├── Header
│   │   └── WorkerQueueWidget (poll)
│   ├── Sidebar
│   └── Main
│       ├── ProjectsPage
│       ├── ProjectDashboardPage
│       ├── CreatePartWizardPage
│       ├── PartWorkspacePage
│       ├── BuildManagerPage
│       ├── QueueMonitorPage
│       ├── ProgressDashboardPage
│       └── EventsPage
```

**Navigation flow (happy path):**

```text
/projects
  → /projects/:projectId
    → /projects/:projectId/parts/new
    → /projects/:projectId/parts/:partId
      → /projects/:projectId/parts/:partId/builds
/queue | /progress | /events (global)
```

---

## 3. Component hierarchy

### Shared layout

```text
AppShell
├── HeaderBar
│   ├── BrandTitle
│   ├── CurrentProjectBreadcrumb (from route + query)
│   ├── WorkerStatusBadge
│   ├── QueueSummaryPills
│   └── ConnectionIndicator (API health)
├── SidebarNav
└── PageOutlet
```

### Screen 1 — Projects

```text
ProjectsPage
├── ProjectsToolbar (+ New Project)
└── ProjectCardGrid
    └── ProjectCard (×N)
```

### Screen 2 — Project dashboard

```text
ProjectDashboardPage
├── ProjectHeader (title, id, updated)
├── PartsToolbar (+ New Part)
└── PartCardGrid
    └── PartCard (×N)
```

### Screen 3 — Create part (wizard)

```text
CreatePartWizardPage
├── WizardStepper
├── StepUploadPdf
├── StepEditText (RichTextEditor)
├── StepChunkQuality (600–1000 selector)
└── StepReviewSave
```

### Screen 4 — Part workspace

```text
PartWorkspacePage
├── PartToolbar
├── SplitPane
│   ├── ChunkListPanel
│   │   ├── ChunkFilterBar
│   │   └── ChunkListRow (×N)
│   └── ChunkDetailPanel
│       ├── ChunkHeader (id, state, badges)
│       └── ChunkDetailTabs
│           ├── TextTab
│           ├── NarrationTab
│           ├── VCTab
│           └── HistoryTab
```

### Screen 5 — Build manager

```text
BuildManagerPage
├── BuildList
│   └── BuildCard (×N)
├── ChunkPicker (multi-select)
└── BuildActionsBar
```

### Screen 6 — Queue monitor

```text
QueueMonitorPage
├── QueueSectionRunning
├── QueueSectionQueued
├── QueueSectionFailed
└── QueueSectionCompleted
    └── JobRow (×N)
```

### Screen 7 — Progress dashboard

```text
ProgressDashboardPage
├── CurrentJobCard
├── VcProgressWidget
├── WorkerSlotGrid (future multi-worker; show 1 today)
└── LiveEventStrip (filtered vc.progress)
```

### Screen 8 — Events

```text
EventsPage
├── EventCategoryTabs
└── EventTable
```

---

## 4. State architecture

### Server state (TanStack Query only)

| Query key namespace | API | Notes |
|---------------------|-----|--------|
| `['health']` | `GET /health` | Connection gate |
| `['worker']` | `GET /worker` | Header + progress |
| `['queue','snapshot']` | `GET /queue` | Counts only today |
| `['projects']` | `GET /projects` | List |
| `['projects', id]` | `GET /projects/:id` | Detail |
| `['parts', projectId]` | `GET /projects/:id/parts` | List |
| `['parts', projectId, partId]` | `GET /projects/.../parts/:partId` | Detail |
| `['chunks', projectId, partId]` | `GET /projects/.../chunks` | Part workspace |
| `['chunks', projectId, partId, chunkId]` | `GET /projects/.../chunks/:id` | Detail panel |
| `['partText', projectId, partId]` | `GET /projects/.../text` | Create flow / optional |
| `['builds', projectId, partId]` | `GET /projects/.../builds` | Build manager |
| `['builds', projectId, partId, buildId]` | `GET /projects/.../builds/:id` | Card detail |
| `['events','recent']` | `GET /events/recent?limit=` | Events + history tab |
| `['resumePlan', projectId, partId]` | `GET /resume-plan` | Recovery UX |
| `['restartPlan', projectId, partId]` | `GET /restart-plan` | Recovery UX |

**Mutations** (invalidate related queries on success):

| Mutation | API |
|----------|-----|
| `createProject` | `POST /projects` |
| `createPart` | `POST /projects/:id/parts` |
| `uploadSource` | `POST .../source` (multipart) |
| `savePartText` | `PUT .../text` |
| `updateChunkText` | `PUT .../chunks/:id/text` |
| `approveNarration` | `POST .../approve-narration` |
| `approveVc` | `POST .../approve-vc` |
| `unapproveNarration` | `POST .../unapprove-narration` |
| `unapproveVc` | `POST .../unapprove-vc` |
| `rebuildNarration` | `POST .../rebuild-narration` |
| `rebuildVc` | `POST .../rebuild-vc` |
| `queueNarration` | `POST /queue/narration` |
| `queueVc` | `POST /queue/vc` |
| `queueResume` | `POST /queue/resume` |
| `cancelJob` | `POST /queue/cancel/:jobId` |
| `workerStart` | `POST /worker/start` |
| `workerStop` | `POST /worker/stop` |
| `createBuild` | `POST .../builds` |
| `queueBuild` | `POST .../builds/:id/queue` |

**Rule:** Never mirror `ChunkManifest.state`, queue counts, or approval flags in Zustand. After mutations, invalidate `chunks`, `parts`, `queue`, `worker`, `events`.

### Client-only state (Zustand)

```typescript
// uiStore — example shape
{
  selectedChunkId: number | null;
  chunkListFilter: 'all' | 'narration' | 'vc' | 'approved' | 'failed' | 'interrupted';
  chunkDetailTab: 'text' | 'narration' | 'vc' | 'history';
  splitPaneRatio: number;
  buildSelection: number[];  // chunk ids for build picker
  createPartDraft: { chunkQuality: 600 | 700 | 800 | 900 | 1000; editorDirty: boolean };
}
```

Persist only non-sensitive UI prefs (optional): `splitPaneRatio`, last filter.

---

## 5. Data-fetching strategy

### API client

- Base URL: `import.meta.env.VITE_API_BASE_URL` → `http://127.0.0.1:8080/api/v1`
- Thin `apiClient` wrapper: `fetch` + JSON + unified error parse `{ error: string }`
- Map HTTP status to user messages (see § Error UX)

### TanStack Query defaults

```text
staleTime: 0 for worker, queue, events, progress-related queries
staleTime: 30s for projects/parts/chunks (manual Refresh + post-mutation invalidation)
retry: 3 with exponential backoff when health check fails
refetchOnWindowFocus: true for projects/chunks
```

### Derived UI data (selectors, not stored)

Compute in components or `select` from query data:

- Part card **narration progress**: `chunks.filter(c => narration complete states).length / chunks.length`
- Part card **VC progress**: same for VC states
- **Approval badges**: `narration_approved`, `vc_approved` + `state`
- **Can queue VC**: `state === 'NarrationApproved' || narration_approved` (match backend `LifecycleService`)

### Audio URLs

- Narration: static file via future `GET /projects/.../chunks/:id/narration/download` **(E8.1)** or direct storage URL if API adds media routes
- VC: same pattern
- Build: `GET .../builds/:buildId/download` (exists in E7)

Until media routes exist, architecture assumes **E8.1** adds authenticated file endpoints; UI uses blob download for Play via `<audio src={blobUrl}>`.

### Create Part — API gaps (E8.1 backend)

E7 today does **not** expose:

1. PDF → extracted text (only `POST /source` stores PDF)
2. Text → chunk split at quality 600–1000
3. Bulk `POST /chunks` creation

**E8.0 UI design** keeps the wizard; **E8.1** should add either:

- `POST /projects/:id/parts/:partId/extract-text`
- `POST /projects/:id/parts/:partId/chunks/preview` + `POST .../chunks/batch`

or a single `POST /projects/:id/parts/:partId/initialize` accepting `{ text, chunk_max_chars }`.

Chunk quality selector reuses **narration-engine** `split_text` semantics (600–1000); no new chunking UI beyond the dropdown.

---

## 6. Polling strategy

No WebSocket in E8. Use `refetchInterval` on queries.

| Surface | Query keys | Interval | Active when |
|---------|------------|----------|-------------|
| Header worker widget | `worker` | 3s | always |
| Header queue summary | `queue` | 3s | always |
| Events page + History tab | `events` | 2s | route or tab visible |
| Progress dashboard | `worker`, `queue`, `events` | 1s | `/progress` |
| Part workspace chunks | `chunks` | 5s | workspace route + worker running |
| Projects/parts | — | on demand | no background poll |

**Pause polling** when `document.hidden` or API health fails (see offline).

**After mutations:** optimistic UI **not** used for chunk state (too risky); use loading toasts + invalidate queries.

---

## 7. Approval workflow UX

### Narration approval gate

```text
NarrationReady
  → user reviews narration tab (listen)
  → [Approve Narration] → NarrationApproved
  → [Queue VC] enabled
```

| UI control | API | Enabled when |
|------------|-----|----------------|
| Approve Narration | `POST approve-narration` | `state === NarrationReady` |
| Unapprove | `POST unapprove-narration` | `NarrationApproved` |
| Queue VC | `POST /queue/vc` | `NarrationApproved` or `narration_approved` |
| Approve VC | `POST approve-vc` | `VCReady` |
| Queue Narration | `POST /queue/narration` | `NarrationQueued` or rebuild requested |

**VC tab:** Disable **Queue VC** with tooltip: *"Approve narration before voice conversion."* On 409 from API, show same message (never raw JSON).

### Visual badges

```text
Narration: ✓ Approved | ○ Pending
VC:        ✓ Approved | ○ Pending
```

State chip colors deferred to E8.2 styling; architecture uses text + icon only.

### Batch actions (Part toolbar)

| Action | Client logic |
|--------|----------------|
| Queue All Narration | For each chunk in `NarrationQueued` or after rebuild → `POST /queue/narration` sequential or parallel with concurrency limit 3 |
| Queue Approved for VC | Filter `NarrationApproved` → `POST /queue/vc` |
| Generate Build | Navigate to builds route with selection pre-filled |

Confirm dialogs for batch > 10 chunks.

---

## 8. Rebuild workflow UX

### Narration rebuild

```text
User clicks [Rebuild Narration]
  → confirm: "Queues re-synthesis; existing WAV will be overwritten on next run."
  → POST rebuild-narration
  → state → NarrationQueued, narration_approved = false
  → user must [Queue Narration] (not auto-enqueued per E6.2)
```

### VC rebuild

```text
User clicks [Rebuild VC]
  → confirm
  → POST rebuild-vc
  → state → VCQueued, vc_approved = false
  → [Queue VC] when narration still approved
```

### Text edit invalidation

```text
Text tab [Save]
  → PUT chunk text
  → if downstream invalidated: toast "Narration and VC must be re-run"
  → chunk list shows NarrationQueued
  → approval badges cleared
```

Part-level editor (Create Part / future): `PUT part text` invalidates all chunks server-side.

---

## 9. Build workflow UX

### Screen 5 flow

```text
1. Load builds list (GET /builds)
2. User selects chunk checkboxes (approved VC preferred preset)
3. [Create Build] → POST /builds { name, chunks }
4. [Queue Build] → POST /builds/:id/queue
5. Poll chunk states / queue until complete
6. [Download] → GET /builds/:id/download (file save)
```

**Preset:** "All VC Approved" → select chunks where `state === VCApproved` or `vc_approved`.

**Rebuild build:** create new build id or re-queue same build job (E7 uses `job_id = build_id`).

### Status on Build card

Derive from queue snapshot + build `output_file` presence:

```text
Pending → no output, not running
Processing → build job running (infer from queue when jobs API exists)
Ready → output WAV exists
Failed → last failed job matches build_id (E8.1)
```

---

## 10. Future WebSocket integration points

Replace polling incrementally; event types already on bus:

| Today (poll) | Future (WS channel) | Event types |
|--------------|---------------------|-------------|
| Worker status | `worker.*` | `worker.started`, `worker.job_started`, `worker.job_completed`, `worker.job_failed` |
| Queue counts | `queue.*` | `queue.job_*`, `queue.snapshot_updated` |
| VC progress widget | `vc.progress` | `vc.progress` (step, ETA) |
| Chunk list refresh | `narration.*`, `vc.*` | `chunk_started`, `chunk_completed`, `chunk_failed` |
| Approval toasts | lifecycle | `narration.approved`, `vc.approved`, `*.rebuild_requested` |
| Recovery | `recovery.*` | `recovery.interrupted_detected`, `resume_plan_created` |

**Client design:**

```text
useEventStream() → dispatches to QueryClient.invalidateQueries(...)
```

Keep the same query keys; WebSocket only triggers invalidation or patch cache for `vc.progress`.

**Suggested endpoint (E9):** `GET /events/stream` (SSE) or `WS /api/v1/ws`.

---

## Error UX

| API | User message |
|-----|----------------|
| 404 | "Not found: {resource}" |
| 409 approval | "Narration must be approved before VC." |
| 409 state | "This action isn't allowed in the current step ({state})." |
| 400 | Show `error` field verbatim if human-readable |
| 501 | "Not supported yet." |
| Network | "Disconnected from backend. Retrying…" |

Use toast + inline field errors; never stack traces.

---

## Offline / recovery UX

```text
GET /health every 10s
  → failure: Header ConnectionIndicator red
  → pause fast polls; retry health with backoff
  → on restore: invalidate all active queries
```

**Interrupted chunks:** filter `Interrupted` in chunk list; banner with [View Resume Plan] → show `GET resume-plan` + [Queue Resume Narration/VC] → `POST /queue/resume`.

**Worker stopped:** banner on Part workspace: "Worker is stopped. Start worker to process queue." → `POST /worker/start`.

---

## Editor requirements (Create Part)

| Requirement | Approach |
|-------------|----------|
| Large documents | Virtualized doc or chunked load; TipTap recommended |
| Persian RTL | `dir="rtl"`, Persian font stack (E8.2) |
| Search / Replace | TipTap extension or CodeMirror overlay |
| Undo / Redo | Editor built-in history |

---

## E8.1 API dependencies (implementation phase)

| UI need | E7 status |
|---------|-----------|
| Queue job rows | **Gap:** only snapshot counts; need `GET /queue/jobs` |
| Chunk bulk create | **Gap:** need batch endpoint |
| PDF text extract | **Gap:** need extract endpoint or narration-engine proxy |
| Audio play URLs | **Gap:** optional media download routes for chunks |
| Project build count | **Derive** from parts/builds client-side |

---

## Folder structure (E8.1 implementation)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx          # QueryClient, Router
│   ├── api/
│   │   ├── client.ts
│   │   ├── types.ts               # mirrors Pydantic responses
│   │   └── hooks/                 # useProjects, useChunks, ...
│   ├── components/
│   │   ├── layout/
│   │   ├── projects/
│   │   ├── parts/
│   │   ├── chunks/
│   │   ├── queue/
│   │   └── shared/
│   ├── pages/                     # route targets
│   ├── stores/
│   │   └── uiStore.ts
│   └── lib/
│       ├── chunkState.ts          # labels, guards (pure functions)
│       └── errors.ts
├── index.html
├── vite.config.ts
└── package.json
```

---

## Multi-worker readiness (Screen 7)

Display `Worker #1` card bound to single `GET /worker` today. Schema reserves `worker_id` for future API without UI rewrite.

---

*E8.0 — architecture only. Implementation begins in E8.1 (scaffold + API client) and E8.2 (styling + components).*
