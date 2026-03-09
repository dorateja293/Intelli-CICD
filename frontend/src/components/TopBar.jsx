import { Menu, Bell, Search } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLocation } from 'react-router-dom'
import { useSidebar } from '../context/SidebarContext'
import Avatar from './Avatar'

const PAGE_META = {
  '/dashboard': { title: 'Dashboard', sub: 'CI prediction overview' },
  '/projects': { title: 'Projects', sub: 'Manage repositories and CI settings' },
  '/commits': { title: 'Commits', sub: 'Browse and filter analyzed commits' },
  '/analytics': { title: 'Analytics', sub: 'Trends and performance metrics' },
  '/predict': { title: 'Prediction', sub: 'Manual commit risk prediction' },
  '/logs': { title: 'Logs', sub: 'Analyze CI logs and get fix suggestions' },
  '/profile': { title: 'Profile', sub: 'Account settings' },
}

export default function TopBar() {
  const { user } = useAuth()
  const { pathname } = useLocation()
  const { setOpen } = useSidebar()
  const meta = PAGE_META[pathname] || { title: 'Intelli-CI', sub: '' }

  return (
    <header className="flex items-center justify-between h-14 sm:h-16 px-4 sm:px-5 lg:px-6 border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)] shrink-0">
      {/* Left: hamburger (mobile/tablet) + page title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="lg:hidden p-2 -m-2 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-tertiary)] hover:text-[var(--color-text-primary)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center shrink-0"
          aria-label="Open menu"
        >
          <Menu size={20} strokeWidth={1.5} />
        </button>
        <div className="min-w-0">
          <h1 className="text-base font-semibold truncate text-[var(--color-text-primary)] leading-tight">
            {meta.title}
          </h1>
          {meta.sub && (
            <p className="text-xs truncate text-[var(--color-text-secondary)] hidden sm:block leading-tight">
              {meta.sub}
            </p>
          )}
        </div>
      </div>

      {/* Right: search, notifications, avatar */}
      <div className="flex items-center gap-1 sm:gap-2 shrink-0">
        <div
          className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] text-xs text-[var(--color-text-secondary)] cursor-text select-none min-w-[180px] lg:min-w-[220px]"
        >
          <Search size={14} />
          <span className="flex-1 truncate">Search commits...</span>
          <kbd className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[var(--color-bg-tertiary)] border border-[var(--color-border)]">
            ⌘K
          </kbd>
        </div>

        <button
          type="button"
          className="p-2 rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-tertiary)] hover:text-[var(--color-text-primary)] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center relative"
          aria-label="Notifications"
        >
          <Bell size={18} strokeWidth={1.5} />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#f0883e]" />
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-[var(--color-border)]">
          <Avatar name={user?.name || 'User'} size={32} />
          <span className="text-sm font-medium text-[var(--color-text-primary)] hidden md:block truncate max-w-[120px]">
            {user?.name?.split(' ')[0] || 'User'}
          </span>
        </div>
      </div>
    </header>
  )
}
