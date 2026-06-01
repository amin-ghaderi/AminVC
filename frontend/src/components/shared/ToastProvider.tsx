import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { cn } from '@/lib/utils'

export type ToastVariant = 'default' | 'error'

export interface ToastMessage {
  id: string
  title: string
  description?: string
  variant?: ToastVariant
}

interface ToastContextValue {
  toast: (message: Omit<ToastMessage, 'id'>) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  const toast = useCallback((message: Omit<ToastMessage, 'id'>) => {
    const id = crypto.randomUUID()
    setMessages((prev) => [...prev, { ...message, id }])
    window.setTimeout(() => {
      setMessages((prev) => prev.filter((item) => item.id !== id))
    }, 5000)
  }, [])

  const value = useMemo(() => ({ toast }), [toast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-4 right-4 z-[100] flex max-w-sm flex-col gap-2"
        aria-live="polite"
      >
        {messages.map((item) => (
          <div
            key={item.id}
            className={cn(
              'pointer-events-auto rounded-lg border px-4 py-3 shadow-lg',
              item.variant === 'error'
                ? 'border-red-500/50 bg-red-950 text-red-100'
                : 'border-[var(--color-border)] bg-[var(--color-card)]',
            )}
          >
            <p className="text-sm font-medium">{item.title}</p>
            {item.description ? (
              <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
                {item.description}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}
