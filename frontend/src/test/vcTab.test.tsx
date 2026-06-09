import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AppProviders } from '@/app/providers/AppProviders'
import { VcTab } from '@/components/part-workspace/tabs/VcTab'
import type { Chunk, ChunkAssets } from '@/types/api'

const emptyAssets: ChunkAssets = {
  narration_exists: true,
  vc_exists: false,
  narration_url: '/narration.wav',
  vc_url: '/vc.wav',
  narration_size: 1000,
  vc_size: null,
}

const vcAssets: ChunkAssets = {
  ...emptyAssets,
  vc_exists: true,
  vc_size: 800,
}

function makeChunk(overrides: Partial<Chunk> = {}): Chunk {
  return {
    chunk_id: 1,
    state: 'VCFailed',
    narration_approved: true,
    vc_approved: false,
    text: '',
    narration: { status: 'ready', file: 'narration/0001.wav', duration_seconds: null },
    vc: { status: '', file: null, duration_seconds: null },
    retry_count: 0,
    last_error: 'Speaker worker failed health check',
    updated_at: '2026-06-09T00:00:00Z',
    ...overrides,
  }
}

function renderVcTab(
  chunk: Chunk,
  assets: ChunkAssets | undefined = emptyAssets,
  referenceAudioReady = true,
) {
  return render(
    <AppProviders>
      <VcTab
        projectId="demo"
        partId="part-01"
        chunk={chunk}
        assets={assets}
        referenceAudioReady={referenceAudioReady}
      />
    </AppProviders>,
  )
}

describe('VcTab VCFailed visibility', () => {
  it('shows last_error when VCFailed with error message', () => {
    renderVcTab(makeChunk())
    expect(screen.getByTestId('vc-failed-heading')).toHaveTextContent(
      'VC Conversion Failed',
    )
    expect(screen.getByTestId('vc-last-error')).toHaveTextContent(
      'Speaker worker failed health check',
    )
  })

  it('shows failure header when VCFailed with null last_error', () => {
    renderVcTab(makeChunk({ last_error: null }))
    expect(screen.getByTestId('vc-failed-heading')).toHaveTextContent(
      'VC Conversion Failed',
    )
    expect(screen.queryByTestId('vc-last-error')).not.toBeInTheDocument()
  })

  it('still renders Queue VC for VCFailed chunks', () => {
    renderVcTab(makeChunk())
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeInTheDocument()
  })

  it('keeps Queue VC disabled when reference audio is missing', () => {
    renderVcTab(makeChunk(), emptyAssets, false)
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeDisabled()
  })

  it('keeps Queue VC disabled when narration is not approved', () => {
    renderVcTab(
      makeChunk({ narration_approved: false, state: 'NarrationReady' }),
      emptyAssets,
      true,
    )
    expect(screen.getByRole('button', { name: 'Queue VC' })).toBeDisabled()
  })

  it('does not show failure block for non-failed states', () => {
    renderVcTab(
      makeChunk({
        state: 'NarrationApproved',
        last_error: null,
      }),
    )
    expect(screen.queryByTestId('vc-failed-block')).not.toBeInTheDocument()
    expect(screen.getByText('No VC generated yet')).toBeInTheDocument()
  })

  it('shows failure block in has-VC branch when VCFailed', () => {
    renderVcTab(makeChunk(), vcAssets)
    expect(screen.getByTestId('vc-failed-block')).toBeInTheDocument()
    expect(screen.getByTestId('vc-last-error')).toBeInTheDocument()
    expect(screen.getByTestId('audio-player')).toBeInTheDocument()
  })
})
