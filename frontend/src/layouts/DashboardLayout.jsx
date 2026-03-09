import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { SidebarProvider } from '../context/SidebarContext'
import Sidebar from '../components/Sidebar'
import TopBar from '../components/TopBar'

export default function DashboardLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div
        className="flex h-screen w-full items-center justify-center bg-[var(--color-bg-primary)]"
        role="status"
        aria-label="Loading"
      >
        <div className="h-10 w-10 rounded-full border-2 border-t-transparent animate-spin border-[var(--color-accent)]" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />

  return (
    <SidebarProvider>
      <div className="flex h-screen overflow-hidden bg-[var(--color-bg-primary)]">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden min-w-0">
          <TopBar />
          <main className="flex-1 overflow-y-auto fade-in">
            <div className="max-w-7xl mx-auto px-6 py-6">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  )
}

