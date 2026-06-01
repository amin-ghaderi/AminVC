import { create } from 'zustand'

interface BuildManagerState {
  selectedChunks: number[]
  expandedBuildId: string | null
  setSelectedChunks: (chunks: number[]) => void
  toggleChunk: (chunkId: number) => void
  clearSelection: () => void
  setExpandedBuild: (buildId: string | null) => void
}

export const useBuildManagerStore = create<BuildManagerState>((set, get) => ({
  selectedChunks: [],
  expandedBuildId: null,
  setSelectedChunks: (chunks) => set({ selectedChunks: chunks }),
  toggleChunk: (chunkId) => {
    const current = get().selectedChunks
    if (current.includes(chunkId)) {
      set({ selectedChunks: current.filter((id) => id !== chunkId) })
    } else {
      set({ selectedChunks: [...current, chunkId].sort((a, b) => a - b) })
    }
  },
  clearSelection: () => set({ selectedChunks: [] }),
  setExpandedBuild: (buildId) => set({ expandedBuildId: buildId }),
}))
