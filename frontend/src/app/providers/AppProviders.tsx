import { QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { createQueryClient } from '@/app/providers/queryClient'
import { ToastProvider } from '@/components/shared/ToastProvider'

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => createQueryClient())

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  )
}
