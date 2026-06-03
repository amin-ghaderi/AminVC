import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { PartVcProgressPanel } from '@/components/progress/PartVcProgressPanel'
import type { PartVcProgressView } from '@/lib/partVcProgress'

const activeView: PartVcProgressView = {
  currentChunkId: 3,
  currentStep: 17,
  totalSteps: 30,
  completedChunks: 2,
  totalChunks: 7,
  currentChunkPosition: 3,
  currentChunkEtaSeconds: 240,
  overallEtaSeconds: 3060,
  progressPercent: 28,
  stepPercent: 57,
  hasActiveProgress: true,
  overallEtaAvailable: true,
}

describe('PartVcProgressPanel', () => {
  it('renders current chunk step and ETAs', () => {
    render(<PartVcProgressPanel progress={activeView} />)
    expect(screen.getByTestId('part-vc-chunk-position')).toHaveTextContent('Chunk 3 / 7')
    expect(screen.getByTestId('part-vc-step')).toHaveTextContent('Step 17 / 30')
    expect(screen.getByTestId('part-vc-step-percent')).toHaveTextContent('57%')
    expect(screen.getByTestId('part-vc-chunk-eta')).toHaveTextContent('4m')
    expect(screen.getByTestId('part-vc-completed')).toHaveTextContent('2 / 7 Completed')
    expect(screen.getByTestId('part-vc-overall-percent')).toHaveTextContent('28%')
    expect(screen.getByTestId('part-vc-overall-eta-value')).toHaveTextContent('51m')
  })

  it('renders learning state when overall ETA unavailable', () => {
    render(
      <PartVcProgressPanel
        progress={{
          ...activeView,
          overallEtaAvailable: false,
          overallEtaSeconds: null,
        }}
      />,
    )
    expect(screen.getByTestId('part-vc-overall-eta-learning')).toHaveTextContent(
      'Learning...',
    )
    expect(screen.getByTestId('part-vc-overall-eta-learning')).toHaveTextContent(
      'Need completed VC chunks',
    )
  })
})
