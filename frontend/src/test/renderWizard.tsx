import { render, type RenderOptions } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'

import { appRoutes } from '@/app/router/routes'
import { AppProviders } from '@/app/providers/AppProviders'

interface RenderWizardOptions extends Omit<RenderOptions, 'wrapper'> {
  initialPath?: string
}

export function renderWizard(options: RenderWizardOptions = {}) {
  const { initialPath = '/projects/demo/parts/new', ...renderOptions } = options
  const router = createMemoryRouter(appRoutes, { initialEntries: [initialPath] })
  return render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
    renderOptions,
  )
}
