import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Cpu, Menu, X, LayoutDashboard, BarChart3, GitCommitHorizontal, User, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

function NavItem({ to, icon: Icon, children }) {
  return (
    <Link to={to} className="nav-item">
      {Icon && <Icon size={13} strokeWidth={1.5} />}
      {children}
    </Link>
  )
}

function MobileLink({ to, onClick, children }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block px-3 py-2 text-sm rounded-md transition-colors hover:bg-[#21262D]"
      style={{ color: '#E6EDF3' }}
    >
      {children}
    </Link>
  )
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
    setMenuOpen(false)
  }

  return (
    <nav
      className="sticky top-0 z-50 border-b backdrop-blur-md"
      style={{ background: 'rgba(13,17,23,0.92)', borderColor: '#30363D' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 no-underline">
          <div className="p-1.5 rounded-lg" style={{ background: '#1a3a1e' }}>
            <Cpu size={18} style={{ color: '#3fb950' }} strokeWidth={1.5} />
          </div>
          <span className="font-bold text-sm tracking-tight" style={{ color: '#E6EDF3' }}>
            INTELLI<span style={{ color: '#3fb950' }}>CI</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {user ? (
            <>
              <NavItem to="/dashboard" icon={LayoutDashboard}>Dashboard</NavItem>
              <NavItem to="/commits" icon={GitCommitHorizontal}>Commits</NavItem>
              <NavItem to="/analytics" icon={BarChart3}>Analytics</NavItem>
              <NavItem to="/profile" icon={User}>Profile</NavItem>
              <div className="w-px h-5 mx-2" style={{ background: '#30363D' }} />
              <button onClick={handleLogout} className="nav-item">
                <LogOut size={13} strokeWidth={1.5} /> Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="px-3 py-1.5 text-sm rounded-md transition-colors hover:bg-[#21262D]"
                style={{ color: '#8B949E' }}
              >
                Log in
              </Link>
              <Link
                to="/signup"
                className="px-4 py-1.5 text-sm rounded-md font-semibold transition-all duration-150 hover:opacity-90"
                style={{ background: '#238636', color: '#fff' }}
              >
                Sign up
              </Link>
            </>
          )}
        </div>

        {/* Mobile toggle — touch-friendly */}
        <button
          type="button"
          className="md:hidden p-2 -m-2 rounded-lg transition-colors hover:bg-[var(--color-bg-tertiary)] min-w-[44px] min-h-[44px] flex items-center justify-center"
          style={{ color: 'var(--color-text-secondary)' }}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-expanded={menuOpen}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
        >
          {menuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div
          className="md:hidden border-t px-4 py-3 space-y-0.5"
          style={{ borderColor: '#30363D', background: '#0D1117' }}
        >
          {user ? (
            <>
              <MobileLink to="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</MobileLink>
              <MobileLink to="/commits"   onClick={() => setMenuOpen(false)}>Commit Analysis</MobileLink>
              <MobileLink to="/analytics" onClick={() => setMenuOpen(false)}>CI Analytics</MobileLink>
              <MobileLink to="/profile"   onClick={() => setMenuOpen(false)}>Profile</MobileLink>
              <button
                onClick={handleLogout}
                className="w-full text-left px-3 py-2 text-sm rounded-md transition-colors hover:bg-[#21262D]"
                style={{ color: '#f85149' }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <MobileLink to="/login"  onClick={() => setMenuOpen(false)}>Log in</MobileLink>
              <MobileLink to="/signup" onClick={() => setMenuOpen(false)}>Sign up</MobileLink>
            </>
          )}
        </div>
      )}
    </nav>
  )
}
