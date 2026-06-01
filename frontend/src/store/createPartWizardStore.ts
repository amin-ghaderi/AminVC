import { create } from 'zustand'

import type { ChunkQuality } from '@/types/api'

export interface CreatePartWizardState {
  step: number
  partId: string
  title: string
  uploadedFile?: File
  pdfUploaded: boolean
  extractedText: string
  editedText: string
  textDirty: boolean
  chunkSize: ChunkQuality
  chunksCreated: number | null
  setStep: (step: number) => void
  setPartInfo: (partId: string, title: string) => void
  setUploadedFile: (file: File | undefined) => void
  setPdfUploaded: (uploaded: boolean) => void
  setExtractedText: (text: string) => void
  setEditedText: (text: string, dirty?: boolean) => void
  setTextDirty: (dirty: boolean) => void
  setChunkSize: (size: ChunkQuality) => void
  setChunksCreated: (count: number | null) => void
  reset: () => void
}

const initialState = {
  step: 1,
  partId: '',
  title: '',
  uploadedFile: undefined as File | undefined,
  pdfUploaded: false,
  extractedText: '',
  editedText: '',
  textDirty: false,
  chunkSize: 800 as ChunkQuality,
  chunksCreated: null as number | null,
}

export const useCreatePartWizardStore = create<CreatePartWizardState>((set) => ({
  ...initialState,
  setStep: (step) => set({ step }),
  setPartInfo: (partId, title) => set({ partId, title }),
  setUploadedFile: (uploadedFile) => set({ uploadedFile, pdfUploaded: false }),
  setPdfUploaded: (pdfUploaded) => set({ pdfUploaded }),
  setExtractedText: (extractedText) =>
    set({ extractedText, editedText: extractedText }),
  setEditedText: (editedText, dirty = true) =>
    set({ editedText, textDirty: dirty }),
  setTextDirty: (textDirty) => set({ textDirty }),
  setChunkSize: (chunkSize) => set({ chunkSize }),
  setChunksCreated: (chunksCreated) => set({ chunksCreated }),
  reset: () => set({ ...initialState }),
}))
