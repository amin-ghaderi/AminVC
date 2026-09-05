import { useQuery } from '@tanstack/react-query'

import { getAgentStatus } from '@/api/agent'
import { AGENT_STATUS_POLL_MS } from '@/hooks/pollingConstants'
import { queryKeys } from '@/hooks/queryKeys'

export function useAgentStatus(deviceId: string) {
  return useQuery({
    queryKey: queryKeys.agent.status(deviceId),
    queryFn: () => getAgentStatus(deviceId),
    enabled: deviceId.length > 0,
    refetchInterval: AGENT_STATUS_POLL_MS,
    retry: false,
  })
}
