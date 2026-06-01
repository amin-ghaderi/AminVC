import { create } from 'zustand'

interface UiState {
  sidebarCollapsed: boolean
  currentProjectId: string | null
  currentProjectTitle: string | null
  setSidebarCollapsed: (collapsed: boolean) => void
  setCurrentProject: (projectId: string | null, title?: string | null) => void
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  currentProjectId: null,
  currentProjectTitle: null,
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  setCurrentProject: (currentProjectId, currentProjectTitle = null) =>
    set({ currentProjectId, currentProjectTitle }),
}))
