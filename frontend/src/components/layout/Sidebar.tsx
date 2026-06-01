import { NavLink } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const items = [
  { to: '/projects', label: 'Projects', enabled: true },
  { to: '/queue', label: 'Queue', enabled: false },
  { to: '/progress', label: 'Progress', enabled: false },
  { to: '/events', label: 'Events', enabled: false },
  { to: '/builds', label: 'Builds', enabled: false },
] as const

export function Sidebar() {
  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-card)] p-4">
      <nav className="flex flex-col gap-1">
        {items.map((item) =>
          item.enabled ? (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[var(--color-primary)] text-[var(--color-primary-foreground)]'
                    : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)]',
                )
              }
            >
              {item.label}
            </NavLink>
          ) : (
            <div
              key={item.to}
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-[var(--color-muted-foreground)] opacity-60"
            >
              <span>{item.label}</span>
              <Badge variant="outline">Coming Soon</Badge>
            </div>
          ),
        )}
      </nav>
    </aside>
  )
}
