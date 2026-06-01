import { create } from 'zustand'

import type { QueueMonitorFilter } from '@/types/api'

interface QueueMonitorState {
  filter: QueueMonitorFilter
  search: string
  setFilter: (filter: QueueMonitorFilter) => void
  setSearch: (search: string) => void
}

export const useQueueMonitorStore = create<QueueMonitorState>((set) => ({
  filter: 'all',
  search: '',
  setFilter: (filter) => set({ filter }),
  setSearch: (search) => set({ search }),
}))
