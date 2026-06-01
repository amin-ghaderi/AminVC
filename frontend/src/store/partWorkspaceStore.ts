import { create } from 'zustand'

import type { ChunkListFilter } from '@/types/api'

interface PartWorkspaceState {
  selectedChunkId: number | null
  filter: ChunkListFilter
  search: string
  activeTab: 'text' | 'narration' | 'vc' | 'history'
  setSelectedChunk: (chunkId: number | null) => void
  setFilter: (filter: ChunkListFilter) => void
  setSearch: (search: string) => void
  setActiveTab: (tab: PartWorkspaceState['activeTab']) => void
  reset: () => void
}

const initial = {
  selectedChunkId: null as number | null,
  filter: 'all' as ChunkListFilter,
  search: '',
  activeTab: 'text' as const,
}

export const usePartWorkspaceStore = create<PartWorkspaceState>((set) => ({
  ...initial,
  setSelectedChunk: (selectedChunkId) => set({ selectedChunkId }),
  setFilter: (filter) => set({ filter }),
  setSearch: (search) => set({ search }),
  setActiveTab: (activeTab) => set({ activeTab }),
  reset: () => set({ ...initial }),
}))
