import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { PartVcProgressPanel } from '@/components/progress/PartVcProgressPanel'
import type { PartVcProgressView } from '@/lib/partVcProgress'

const activeView: PartVcProgressView = {
  currentChunkId: 3,
  narrationChunkPosition: 3,
  currentStep: 11,
  totalSteps: 30,
  segmentIndex: 3,
  segmentTotal: 8,
  completedChunks: 2,
  totalChunks: 7,
  segmentEtaSeconds: 24,
  chunkEtaSeconds: 197,
  chunkEtaLearning: false,
  overallEtaSeconds: 1601,
  progressPercent: 28,
  stepPercent: 37,
  hasActiveProgress: true,
  hasSegmentProgress: true,
  overallEtaAvailable: true,
}

describe('PartVcProgressPanel', () => {
  it('renders three-level hierarchy and clock ETAs', () => {
    render(<PartVcProgressPanel progress={activeView} />)
    expect(screen.getByTestId('part-vc-narration-position')).toHaveTextContent('3 / 7')
    expect(screen.getByTestId('part-vc-segment-position')).toHaveTextContent('3 / 8')
    expect(screen.getByTestId('part-vc-step')).toHaveTextContent('11 / 30')
    expect(screen.getByTestId('part-vc-segment-eta')).toHaveTextContent('00:24')
    expect(screen.getByTestId('part-vc-chunk-eta')).toHaveTextContent('03:17')
    expect(screen.getByTestId('part-vc-overall-eta-value')).toHaveTextContent('26:41')
  })

  it('hides segment block when segment data unavailable', () => {
    render(
      <PartVcProgressPanel
        progress={{
          ...activeView,
          hasSegmentProgress: false,
          segmentIndex: null,
          segmentTotal: null,
          chunkEtaLearning: true,
          chunkEtaSeconds: null,
        }}
      />,
    )
    expect(screen.queryByTestId('part-vc-segment')).not.toBeInTheDocument()
    expect(screen.getByTestId('part-vc-chunk-eta-learning')).toHaveTextContent('Learning...')
  })

  it('shows learning for part ETA when unavailable', () => {
    render(
      <PartVcProgressPanel
        progress={{
          ...activeView,
          overallEtaAvailable: false,
          overallEtaSeconds: null,
        }}
      />,
    )
    expect(screen.getByTestId('part-vc-overall-eta-learning')).toHaveTextContent('Learning...')
  })
})
