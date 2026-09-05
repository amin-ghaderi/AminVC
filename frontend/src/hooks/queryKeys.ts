export const queryKeys = {
  projects: {
    all: ['projects'] as const,
    detail: (projectId: string) => ['projects', projectId] as const,
  },
  parts: {
    list: (projectId: string) => ['parts', projectId] as const,
  },
  worker: {
    status: ['worker'] as const,
    statusMonitor: ['worker-status'] as const,
  },
  agent: {
    status: (deviceId: string) => ['agent-status', deviceId] as const,
  },
  queue: {
    snapshot: ['queue', 'snapshot'] as const,
    jobs: ['queue-jobs'] as const,
  },
  eventsRecent: ['events-recent'] as const,
  vcProgress: ['vc-progress'] as const,
  builds: {
    all: ['builds'] as const,
    list: (projectId: string, partId: string) =>
      ['builds', projectId, partId] as const,
    detail: (projectId: string, partId: string, buildId: string) =>
      ['build', projectId, partId, buildId] as const,
    status: (buildId: string) => ['build-status', buildId] as const,
  },
  partSummary: (projectId: string, partId: string) =>
    ['part-summary', projectId, partId] as const,
  chunks: (projectId: string, partId: string) =>
    ['chunks', projectId, partId] as const,
  chunk: (projectId: string, partId: string, chunkId: number) =>
    ['chunk', projectId, partId, chunkId] as const,
  chunkAssets: (projectId: string, partId: string, chunkId: number) =>
    ['chunk-assets', projectId, partId, chunkId] as const,
  events: {
    recent: ['events', 'recent'] as const,
  },
}
