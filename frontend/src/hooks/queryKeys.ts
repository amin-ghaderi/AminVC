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
  },
  queue: {
    snapshot: ['queue', 'snapshot'] as const,
  },
}
