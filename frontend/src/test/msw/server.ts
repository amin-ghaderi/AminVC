import { setupServer } from 'msw/node'

import { handlers } from '@/test/msw/handlers'
import { resetQueueMonitorData } from '@/test/msw/queueMonitorHandlers'
import { resetWorkspaceData } from '@/test/msw/workspaceHandlers'

resetWorkspaceData()
resetQueueMonitorData()

export const server = setupServer(...handlers)
