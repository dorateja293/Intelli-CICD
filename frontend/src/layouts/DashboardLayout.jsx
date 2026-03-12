import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import TopBar from '../components/TopBar'
import { SidebarProvider } from '../context/SidebarContext'
import { useSidebar } from '../context/SidebarContext'

function LayoutInner() {
  const { open, setOpen } = useSidebar()
  return (
    <div className="flex min-h-screen bg-[#0d1117] text-[#c9d1d9]">
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/60 lg:hidden"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-5 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <LayoutInner />
    </SidebarProvider>
  )
}
