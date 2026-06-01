import { useMemo } from 'react'

import { ChunkSelectionTable } from '@/components/build-manager/ChunkSelectionTable'
import { CreateBuildForm } from '@/components/build-manager/CreateBuildForm'
import { filterVcApprovedChunks } from '@/lib/buildChunks'
import type { Chunk } from '@/types/api'

interface BuildCreationPanelProps {
  allChunks: Chunk[] | undefined
  selectedChunks: number[]
  onToggle: (chunkId: number) => void
  onSelectAll: () => void
  onClear: () => void
  onSelectVcApproved: () => void
  onCreate: (name: string) => void
  creating: boolean
}

export function BuildCreationPanel({
  allChunks,
  selectedChunks,
  onToggle,
  onSelectAll,
  onClear,
  onSelectVcApproved,
  onCreate,
  creating,
}: BuildCreationPanelProps) {
  const eligible = useMemo(
    () => filterVcApprovedChunks(allChunks ?? []),
    [allChunks],
  )

  return (
    <section
      className="space-y-4 rounded-lg border border-[var(--color-border)] p-4"
      data-testid="build-creation-panel"
    >
      <h2 className="text-lg font-semibold">Create Build</h2>
      {eligible.length === 0 ? (
        <p
          className="text-sm text-[var(--color-muted-foreground)]"
          data-testid="no-vc-approved-empty"
        >
          No VC-approved chunks available for build creation.
        </p>
      ) : (
        <>
          <ChunkSelectionTable
            chunks={eligible}
            selectedChunks={selectedChunks}
            onToggle={onToggle}
            onSelectAll={onSelectAll}
            onClear={onClear}
            onSelectVcApproved={onSelectVcApproved}
          />
          <CreateBuildForm
            selectedCount={selectedChunks.length}
            onSubmit={onCreate}
            submitting={creating}
          />
        </>
      )}
    </section>
  )
}
