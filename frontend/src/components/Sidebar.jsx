import { useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderGit2,
  GitCommitHorizontal,
  BarChart3,
  User,
  LogOut,
  Cpu,
  Zap,
  Terminal,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useSidebar } from '../context/SidebarContext'
import Avatar from './Avatar'

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: FolderGit2, label: 'Projects' },
  { to: '/commits', icon: GitCommitHorizontal, label: 'Commits' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/predict', icon: Zap, label: 'Predict' },
  { to: '/logs', icon: Terminal, label: 'Logs' },
  { to: '/profile', icon: User, label: 'Profile' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { open, setOpen } = useSidebar()

  const closeDrawer = () => setOpen(false)

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1025) setOpen(false)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [setOpen])

  const content = (
    <>
      {/* Logo + close on mobile */}
      <div className="flex items-center justify-between h-16 px-4 border-b shrink-0 border-[var(--color-border)]">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-[rgba(46,160,67,0.14)]">
            <Cpu size={18} className="text-[#2ea043]" strokeWidth={1.5} />
          </div>
          <span className="font-bold text-sm tracking-tight text-[var(--color-text-primary)]">
            INTELLI<span className="text-[#2ea043]">CI</span>
          </span>
        </div>
        <button
          type="button"
          onClick={closeDrawer}
          className="lg:hidden p-2 -m-2 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-tertiary)] hover:text-[var(--color-text-primary)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={closeDrawer}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={17} strokeWidth={1.5} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User section */}
      <div className="px-3 pb-4 pt-3 border-t border-[var(--color-border)]">
        <div className="flex items-center gap-3 px-3 py-3 mb-2 rounded-lg bg-[#21262D]">
          <Avatar name={user?.name || 'User'} size={36} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate text-[var(--color-text-primary)]">
              {user?.name || 'User'}
            </p>
            <p className="text-xs truncate text-[var(--color-text-secondary)]">{user?.email || ''}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            logout()
            navigate('/login')
            closeDrawer()
          }}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-tertiary)] hover:text-[var(--color-text-primary)] transition-colors min-h-[44px] lg:min-h-0 lg:py-2"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </>
  )

  return (
    <>
      {/* Backdrop (mobile) */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}

      {/* Sidebar: drawer on mobile/tablet, fixed on desktop */}
      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-50 flex flex-col w-[var(--sidebar-width)] shrink-0
          bg-[var(--color-bg-secondary)] border-r border-[var(--color-border)]
          transform transition-transform duration-200 ease-out
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {content}
      </aside>
    </>
  )
}
