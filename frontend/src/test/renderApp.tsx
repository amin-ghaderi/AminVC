import { render, type RenderOptions } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'

import { appRoutes } from '@/app/router/routes'
import { AppProviders } from '@/app/providers/AppProviders'

interface RenderAppOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[]
}

export function renderApp(options: RenderAppOptions = {}) {
  const { initialEntries = ['/'], ...renderOptions } = options
  const router = createMemoryRouter(appRoutes, { initialEntries })
  return render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
    renderOptions,
  )
}
