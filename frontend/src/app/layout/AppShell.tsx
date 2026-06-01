import { Outlet } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
