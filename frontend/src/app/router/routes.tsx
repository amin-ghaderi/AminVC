import { Navigate } from 'react-router-dom'
import type { RouteObject } from 'react-router-dom'

import { AppShell } from '@/app/layout/AppShell'
import { BuildManagerPage } from '@/pages/BuildManagerPage/BuildManagerPage'
import { CreatePartWizardPage } from '@/pages/CreatePartWizardPage/CreatePartWizardPage'
import { PartWorkspacePage } from '@/pages/PartWorkspacePage/PartWorkspacePage'
import { ProgressDashboardPage } from '@/pages/ProgressDashboardPage/ProgressDashboardPage'
import { ProjectDashboardPage } from '@/pages/ProjectDashboardPage/ProjectDashboardPage'
import { ProjectsPage } from '@/pages/ProjectsPage/ProjectsPage'
import { QueueMonitorPage } from '@/pages/QueueMonitorPage/QueueMonitorPage'

export const appRoutes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/projects" replace /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'queue', element: <QueueMonitorPage /> },
      { path: 'progress', element: <ProgressDashboardPage /> },
      { path: 'projects/:projectId', element: <ProjectDashboardPage /> },
      {
        path: 'projects/:projectId/parts/new',
        element: <CreatePartWizardPage />,
      },
      {
        path: 'projects/:projectId/parts/:partId',
        element: <PartWorkspacePage />,
      },
      {
        path: 'projects/:projectId/parts/:partId/builds',
        element: <BuildManagerPage />,
      },
    ],
  },
  { path: '*', element: <Navigate to="/projects" replace /> },
]
