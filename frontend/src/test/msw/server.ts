import { setupServer } from 'msw/node'

import { handlers } from '@/test/msw/handlers'
import { resetBuildManagerData } from '@/test/msw/buildManagerHandlers'
import { resetQueueMonitorData } from '@/test/msw/queueMonitorHandlers'
import { resetWorkspaceData } from '@/test/msw/workspaceHandlers'

resetWorkspaceData()
resetQueueMonitorData()
resetBuildManagerData()

export const server = setupServer(...handlers)
