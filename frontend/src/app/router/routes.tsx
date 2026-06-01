import { Navigate } from 'react-router-dom'
import type { RouteObject } from 'react-router-dom'

import { AppShell } from '@/app/layout/AppShell'
import { CreatePartWizardPage } from '@/pages/CreatePartWizardPage/CreatePartWizardPage'
import { ProjectDashboardPage } from '@/pages/ProjectDashboardPage/ProjectDashboardPage'
import { ProjectsPage } from '@/pages/ProjectsPage/ProjectsPage'

export const appRoutes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/projects" replace /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <ProjectDashboardPage /> },
      {
        path: 'projects/:projectId/parts/new',
        element: <CreatePartWizardPage />,
      },
    ],
  },
  { path: '*', element: <Navigate to="/projects" replace /> },
]
