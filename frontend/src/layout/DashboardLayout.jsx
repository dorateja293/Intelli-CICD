import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Navbar from '../components/Navbar'
import { SidebarProvider } from '../context/SidebarContext'

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <div className="flex h-screen bg-transparent">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
          <Navbar />
          <main className="flex-1 overflow-y-auto p-6 md:p-10">
            <div className="max-w-7xl mx-auto">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  )
}