import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import { appRoutes } from '@/app/router/routes'

export const browserRouter = createBrowserRouter(appRoutes)

export function AppRouter() {
  return <RouterProvider router={browserRouter} />
}
