import os

BASE_DIR = r"d:\intelli-ci\frontend"
SRC_DIR = os.path.join(BASE_DIR, "src")

dirs = ["components", "pages", "services", "layout", "context"]
for d in dirs:
    os.makedirs(os.path.join(SRC_DIR, d), exist_ok=True)

files = {}

files["package.json"] = """{
  "name": "intelli-ci-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "lucide-react": "^0.300.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.34.1",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.6",
    "tailwindcss": "^4.0.0",
    "vite": "^5.2.0"
  }
}"""

files["vite.config.js"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})"""

files["src/index.css"] = """@import "tailwindcss";
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --color-bg-base: #000000;
  --color-bg-app: #050505;
  --color-glass: rgba(255, 255, 255, 0.03);
  --color-glass-hover: rgba(255, 255, 255, 0.06);
  --color-glass-border: rgba(255, 255, 255, 0.08);
  
  --color-text-primary: #ededed;
  --color-text-secondary: #a1a1aa;
  --color-text-muted: #71717a;
  
  --color-accent-blue: #3b82f6;
  --color-accent-indigo: #6366f1;
  --color-accent-purple: #8b5cf6;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;
}

body {
  background-color: var(--color-bg-base);
  color: var(--color-text-primary);
  font-family: 'Inter', sans-serif;
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
    radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.12) 0%, transparent 50%);
  background-attachment: fixed;
}

* {
  box-sizing: border-box;
}

.glass-panel {
  background: var(--color-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-glass-border);
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-panel:hover {
  background: var(--color-glass-hover);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
}

.page-title {
  font-size: 2.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(to right, #ffffff, #a1a1aa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-sub {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-top: 0.5rem;
  font-weight: 400;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
"""

files["src/main.jsx"] = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)"""

files["src/context/AuthContext.jsx"] = """import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState({ name: 'Pro Developer', role: 'Admin' })
  
  const login = (userData, token) => setUser(userData)
  const logout = () => setUser(null)

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
"""

files["src/context/SidebarContext.jsx"] = """import { createContext, useContext, useState } from 'react'
const SidebarContext = createContext()
export const SidebarProvider = ({ children }) => {
  const [open, setOpen] = useState(false)
  return <SidebarContext.Provider value={{ open, setOpen }}>{children}</SidebarContext.Provider>
}
export const useSidebar = () => useContext(SidebarContext)
"""

files["src/App.jsx"] = """import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layout/DashboardLayout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import Commits from './pages/Commits'
import Analytics from './pages/Analytics'
import Predict from './pages/Predict'
import Logs from './pages/Logs'
import Profile from './pages/Profile'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/commits" element={<Commits />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/predict" element={<Predict />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}"""

files["src/layout/DashboardLayout.jsx"] = """import { Outlet } from 'react-router-dom'
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
}"""

files["src/components/Sidebar.jsx"] = """import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FolderRoot, GitCommit, LineChart, Cpu, TerminalSquare, UserCircle, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { to: '/projects', icon: FolderRoot, label: 'Repositories' },
  { to: '/commits', icon: GitCommit, label: 'Commits & PRs' },
  { to: '/analytics', icon: LineChart, label: 'Insights' },
  { to: '/predict', icon: Cpu, label: 'AI Predict' },
  { to: '/logs', icon: TerminalSquare, label: 'Log Analysis' },
  { to: '/profile', icon: UserCircle, label: 'Settings' },
]

export default function Sidebar() {
  const { logout } = useAuth()
  return (
    <aside className="w-[260px] bg-black/40 backdrop-blur-xl border-r border-[#ffffff0f] flex flex-col h-full shrink-0 z-20">
      <div className="h-20 flex items-center px-8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.5)]">
            <Cpu size={18} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">Intelli-CI</span>
        </div>
      </div>
      <div className="px-6 mb-4 mt-2 text-xs font-semibold text-[#71717a] uppercase tracking-wider">Platform</div>
      <nav className="flex-1 px-4 flex flex-col gap-1.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => 
              `flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 font-medium text-sm ` + 
              (isActive 
                ? 'bg-white/10 text-white shadow-sm border border-white/5' 
                : 'text-[#a1a1aa] hover:bg-white/5 hover:text-white')
            }
          >
            <item.icon size={18} className={({isActive}) => isActive ? "text-indigo-400" : "opacity-80"} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="p-4 mt-auto">
        <div className="glass-panel p-4 mb-4 bg-gradient-to-b from-indigo-500/10 to-transparent">
          <p className="text-xs font-medium text-white mb-1">Pro Plan</p>
          <p className="text-[10px] text-[#a1a1aa] mb-3">12,450 / 50k commits used</p>
          <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-500 w-1/4 h-full rounded-full"></div>
          </div>
        </div>
        <button onClick={logout} className="flex items-center gap-3 px-4 py-2 w-full text-sm font-medium text-[#a1a1aa] hover:text-white hover:bg-white/5 rounded-xl transition-colors">
          <LogOut size={18} /> Sign Out
        </button>
      </div>
    </aside>
  )
}"""

files["src/components/Navbar.jsx"] = """import { useAuth } from '../context/AuthContext'
import { Bell, Search } from 'lucide-react'

export default function Navbar() {
  const { user } = useAuth()
  return (
    <header className="h-20 border-b border-[#ffffff0a] flex items-center justify-between px-6 md:px-10 bg-transparent shrink-0">
      <div className="flex-1 max-w-md">
        <div className="relative group">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#71717a] group-focus-within:text-indigo-400 transition-colors" />
          <input 
            type="text" 
            placeholder="Search commits, branches, or projects... (Cmd+K)" 
            className="w-full bg-white/5 border border-white/10 text-white placeholder-[#71717a] text-sm rounded-full py-2.5 pl-10 pr-4 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all font-medium"
          />
        </div>
      </div>
      <div className="flex items-center gap-5">
        <button className="relative p-2 text-[#a1a1aa] hover:text-white transition-colors">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full border border-black"></span>
        </button>
        <div className="h-6 w-px bg-white/10"></div>
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="text-right hidden md:block">
            <div className="text-sm font-semibold text-white group-hover:text-indigo-200 transition-colors">{user?.name}</div>
            <div className="text-[11px] text-[#a1a1aa]">{user?.role}</div>
          </div>
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=6366f1" alt="Avatar" className="w-9 h-9 rounded-full border border-white/20 shadow-sm" />
        </div>
      </div>
    </header>
  )
}"""

files["src/components/StatCard.jsx"] = """export default function StatCard({ title, value, subValue, trend, icon: Icon, colorClass, gradientClass }) {
  const isPositive = trend > 0;
  return (
    <div className="glass-panel p-6 relative overflow-hidden group">
      <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-500 ${gradientClass}`}></div>
      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-[#a1a1aa] text-sm font-medium mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
            {subValue && <span className="text-sm font-medium text-[#71717a]">{subValue}</span>}
          </div>
          {trend && (
            <p className={`text-xs font-semibold mt-2 flex items-center gap-1 ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isPositive ? '↑' : '↓'} {Math.abs(trend)}% from last week
            </p>
          )}
        </div>
        <div className={`p-3 rounded-2xl ${colorClass} bg-opacity-10 backdrop-blur-sm border border-white/5`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </div>
  )
}"""

files["src/components/ProjectCard.jsx"] = """import { Github, Play, SkipForward, AlertCircle } from 'lucide-react'
export default function ProjectCard({ name, repo, commits, skipRate, status }) {
  return (
    <div className="glass-panel flex flex-col h-full group">
      <div className="p-6 border-b border-white/5">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-indigo-500/30 transition-colors">
              <Github size={20} className="text-[#ededed]" />
            </div>
            <div>
              <h3 className="text-white font-bold text-base tracking-tight">{name}</h3>
              <p className="text-[#a1a1aa] text-xs font-medium font-mono mt-0.5">{repo}</p>
            </div>
          </div>
          <div className={`px-2.5 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5
            ${status === 'healthy' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${status === 'healthy' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
            {status}
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="bg-black/20 rounded-xl p-3 border border-white/5">
            <p className="text-[#71717a] text-[10px] font-bold uppercase tracking-wider mb-1">Compute Saved</p>
            <p className="text-indigo-400 font-bold text-lg">{skipRate}</p>
          </div>
          <div className="bg-black/20 rounded-xl p-3 border border-white/5">
            <p className="text-[#71717a] text-[10px] font-bold uppercase tracking-wider mb-1">Total Runs</p>
            <p className="text-white font-bold text-lg">{commits}</p>
          </div>
        </div>
      </div>
      <div className="p-4 mt-auto flex gap-3">
        <button className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white py-2 rounded-xl text-xs font-semibold transition-all">View Analytics</button>
        <button className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white py-2 rounded-xl text-xs font-semibold shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all">Configure</button>
      </div>
    </div>
  )
}"""

files["src/components/CommitTable.jsx"] = """import { Activity, GitMerge, FileCode2 } from 'lucide-react'

export default function CommitTable() {
  const commits = [
    { sha: 'a1b2c3d', msg: 'feat: apply new dashboard styles', author: 'johndoe', project: 'frontend-web', files: 12, churn: 145, prob: '1.2%', dec: 'SKIP_TESTS', time: '10 mins ago' },
    { sha: 'e4f5g6h', msg: 'fix: concurrent db connections', author: 'alice', project: 'core-backend', files: 3, churn: 420, prob: '94.5%', dec: 'RUN_TESTS', time: '1 hour ago' },
    { sha: 'i7j8k9l', msg: 'chore: update dependency graph', author: 'bob', project: 'ml-engine', files: 45, churn: 89, prob: '45.0%', dec: 'PARTIAL_TESTS', time: '3 hours ago' },
    { sha: 'x9y8z7w', msg: 'docs: update architecture diagram', author: 'charlie', project: 'frontend-web', files: 1, churn: 5, prob: '0.1%', dec: 'SKIP_TESTS', time: '5 hours ago' },
  ]
  const decColor = {
    'SKIP_TESTS': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    'RUN_TESTS': 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.2)]',
    'PARTIAL_TESTS': 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  }
  return (
    <div className="glass-panel overflow-hidden border border-white/10">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-black/40 border-b border-white/10 text-[#71717a] text-[10px] font-bold uppercase tracking-wider">
              <th className="p-4 pl-6 font-medium">Commit</th>
              <th className="p-4 font-medium">Project</th>
              <th className="p-4 font-medium">Impact</th>
              <th className="p-4 font-medium">AI Risk</th>
              <th className="p-4 font-medium">Decision</th>
              <th className="p-4 pr-6 font-medium text-right">Time</th>
            </tr>
          </thead>
          <tbody className="text-[#ededed] text-sm divide-y divide-white/5 bg-black/20">
            {commits.map((c, i) => (
              <tr key={c.sha} className="hover:bg-white/5 transition-colors group cursor-pointer">
                <td className="p-4 pl-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-white/5 border border-white/10 group-hover:border-indigo-500/30 transition-colors">
                      <GitMerge size={16} className="text-[#a1a1aa] group-hover:text-indigo-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white truncate max-w-[200px]">{c.msg}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="font-mono text-[11px] text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">{c.sha}</span>
                        <span className="text-xs text-[#71717a]">{c.author}</span>
                      </div>
                    </div>
                  </div>
                </td>
                <td className="p-4 text-[#a1a1aa] font-medium">{c.project}</td>
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 text-xs text-[#a1a1aa]">
                      <FileCode2 size={14}/> {c.files}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-[#a1a1aa]">
                      <Activity size={14} className={c.churn > 200 ? "text-amber-400" : ""}/> {c.churn}
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  <span className={`font-mono text-xs font-medium px-2 py-1 rounded-md bg-black/50 border ${parseFloat(c.prob) > 50 ? 'text-rose-400 border-rose-500/20' : parseFloat(c.prob) > 10 ? 'text-amber-400 border-amber-500/20' : 'text-emerald-400 border-emerald-500/20'}`}>
                    {c.prob}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider inline-flex items-center gap-1 border ${decColor[c.dec]}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${c.dec === 'RUN_TESTS' ? 'bg-rose-400 animate-pulse' : c.dec === 'SKIP_TESTS' ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
                    {c.dec.replace('_', ' ')}
                  </span>
                </td>
                <td className="p-4 pr-6 text-right text-xs text-[#71717a] font-medium">{c.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}"""

files["src/components/ChartCard.jsx"] = """export default function ChartCard({ title, subtitle, children }) {
  return (
    <div className="glass-panel p-6 md:p-8 min-h-[360px] flex flex-col relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      <div className="mb-8 relative z-10">
        <h3 className="section-title text-white">{title}</h3>
        {subtitle && <p className="text-xs text-[#a1a1aa] mt-1">{subtitle}</p>}
      </div>
      <div className="flex-1 w-full relative z-10">
        {children}
      </div>
    </div>
  )
}"""

files["src/components/FormInput.jsx"] = """export default function FormInput({ label, id, ...props }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-xs font-semibold uppercase tracking-wider text-[#a1a1aa] ml-1">{label}</label>
      <input
        id={id}
        {...props}
        className="w-full bg-black/40 border border-white/10 text-white p-3.5 rounded-xl text-sm
        focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 focus:bg-white/5
        placeholder:text-[#71717a] transition-all shadow-inner"
      />
    </div>
  )
}"""

files["src/components/Button.jsx"] = """export default function Button({ children, variant = 'primary', size = 'default', ...props }) {
  const baseStyle = "inline-flex items-center justify-center font-semibold transition-all duration-300 w-full rounded-xl"
  
  const sizes = {
    default: "px-6 py-3.5 text-sm",
    lg: "px-8 py-4 text-base",
    sm: "px-4 py-2 text-xs"
  }
  
  const styles = {
    primary: "bg-white text-black hover:bg-gray-200 shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:shadow-[0_0_25px_rgba(255,255,255,0.25)] hover:-translate-y-0.5",
    indigo: "bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] hover:-translate-y-0.5 border border-indigo-400/50",
    secondary: "bg-white/5 border border-white/10 text-white hover:bg-white/10 backdrop-blur-sm",
    ghost: "bg-transparent text-[#a1a1aa] hover:text-white hover:bg-white/5"
  }
  
  return (
    <button className={`${baseStyle} ${sizes[size]} ${styles[variant]}`} {...props}>
      {children}
    </button>
  )
}"""

files["src/pages/Landing.jsx"] = """import { Link } from 'react-router-dom'
import { Cpu, Zap, Shield, GitBranch, ArrowRight, Activity, Terminal } from 'lucide-react'

export default function Landing() {
  const features = [
    { icon: Cpu, title: 'AI Deterministic Engine', desc: 'Analyzes AST and churn rate to predict exactly which tests will fail with 99.2% accuracy.', glow: 'from-blue-500 to-cyan-400' },
    { icon: Zap, title: 'Smart Skip Technology', desc: 'Securely skip up to 70% of unnecessary CI runs, saving massive compute resources.', glow: 'from-amber-400 to-orange-500' },
    { icon: Shield, title: 'Risk Boundaries', desc: 'Set custom confidence thresholds. If the AI is unsure, it defaults to running the tests.', glow: 'from-emerald-400 to-teal-500' },
    { icon: Activity, title: 'Log Diagnostics', desc: 'Paste a 5000-line failing log and our LLM engine pinpoints the exact line causing the crash.', glow: 'from-purple-500 to-pink-500' },
  ]
  return (
    <div className="min-h-screen bg-black text-[#ededed] overflow-hidden relative selection:bg-indigo-500/30">
      {/* Background Effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      
      <nav className="border-b border-white/10 px-6 md:px-12 h-20 flex items-center justify-between max-w-[1400px] mx-auto relative z-10 backdrop-blur-md bg-black/50 sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-white text-black flex items-center justify-center font-bold">IC</div>
          <span className="font-bold text-xl tracking-tight">Intelli-CI</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="text-sm font-semibold text-[#a1a1aa] hover:text-white transition-colors hidden sm:block">Sign In</Link>
          <Link to="/signup" className="bg-white text-black px-5 py-2.5 rounded-lg text-sm font-bold shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:scale-105 transition-transform">Get Started</Link>
        </div>
      </nav>
      
      <main className="max-w-[1200px] mx-auto px-6 pt-32 pb-24 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-sm">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
          <span className="text-xs font-semibold text-indigo-300 uppercase tracking-widest">Intelli-CI v2.0 Live</span>
        </div>
        
        <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-8 leading-[1.1]">
          Stop running <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            useless tests.
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-[#a1a1aa] mb-12 max-w-2xl mx-auto font-medium leading-relaxed">
          The first AI-native CI/CD optimization layer. We analyze your commits in milliseconds to determine exactly what needs testing, cutting pipeline costs by up to 75%.
        </p>
        
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-32">
          <Link to="/signup" className="group relative inline-flex items-center justify-center gap-2 bg-white text-black px-8 py-4 rounded-xl font-bold text-base hover:shadow-[0_0_30px_rgba(255,255,255,0.3)] transition-all overflow-hidden w-full sm:w-auto">
            <span className="relative z-10 flex items-center gap-2">Start Optimizing <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform"/></span>
          </Link>
          <Link to="/dashboard" className="inline-flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white px-8 py-4 rounded-xl font-bold text-base hover:bg-white/10 backdrop-blur-md transition-all w-full sm:w-auto">
            <Terminal size={18} /> View Live Demo
          </Link>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-purple-600/10 rounded-full blur-[100px] pointer-events-none"></div>
          {features.map(f => (
            <div key={f.title} className="glass-panel p-8 md:p-10 text-left relative overflow-hidden group">
              <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${f.glow} opacity-50 group-hover:opacity-100 transition-opacity`}></div>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.glow} p-[1px] mb-6`}>
                <div className="w-full h-full bg-black rounded-xl flex items-center justify-center">
                  <f.icon className="text-white" size={24} />
                </div>
              </div>
              <h3 className="text-xl font-bold mb-3 text-white tracking-tight">{f.title}</h3>
              <p className="text-[#a1a1aa] font-medium leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}"""

files["src/pages/Login.jsx"] = """import { Link, useNavigate } from 'react-router-dom'
import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Login() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      
      <div className="max-w-[420px] w-full glass-panel p-10 relative z-10 border border-white/10 shadow-2xl backdrop-blur-2xl bg-black/60">
        <div className="w-12 h-12 bg-white rounded-xl text-black flex items-center justify-center font-bold text-xl mb-8 shadow-[0_0_20px_rgba(255,255,255,0.2)]">IC</div>
        
        <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Welcome back</h1>
        <p className="text-[#a1a1aa] text-sm mb-8 font-medium">Enter your credentials to access your dashboard.</p>
        
        <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); navigate('/dashboard') }}>
          <FormInput id="email" label="Email Address" type="email" placeholder="name@company.com" required />
          <FormInput id="password" label="Password" type="password" placeholder="••••••••" required />
          
          <div className="pt-4">
            <Button type="submit" variant="indigo">Sign In</Button>
          </div>
        </form>
        
        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <p className="text-[#71717a] text-sm font-medium">
            New to Intelli-CI? <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 font-bold transition-colors">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}"""

files["src/pages/Signup.jsx"] = """import { Link, useNavigate } from 'react-router-dom'
import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Signup() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      
      <div className="max-w-[420px] w-full glass-panel p-10 relative z-10 border border-white/10 shadow-2xl backdrop-blur-2xl bg-black/60">
        <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Start Optimizing</h1>
        <p className="text-[#a1a1aa] text-sm mb-8 font-medium">Create your account to get 14 days of free Pro access.</p>
        
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); navigate('/dashboard') }}>
          <FormInput id="name" label="Full Name" type="text" placeholder="Jane Doe" required />
          <FormInput id="email" label="Work Email" type="email" placeholder="jane@company.com" required />
          <FormInput id="password" label="Password" type="password" placeholder="••••••••" required />
          
          <div className="pt-6">
            <Button type="submit" variant="primary">Create Account</Button>
          </div>
        </form>
        
        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <p className="text-[#71717a] text-sm font-medium">
            Already have an account? <Link to="/login" className="text-white hover:text-gray-300 font-bold transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}"""

files["src/pages/Dashboard.jsx"] = """import StatCard from '../components/StatCard'
import CommitTable from '../components/CommitTable'
import ChartCard from '../components/ChartCard'
import { GitCommitHorizontal, FastForward, Clock, Crosshair, Zap } from 'lucide-react'
import { AreaChart, Area, PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const pieData = [
    { name: 'Run Tests', value: 400, color: '#f43f5e' },
    { name: 'Skip Tests', value: 300, color: '#10b981' },
    { name: 'Partial', value: 100, color: '#f59e0b' }
  ]
  const barData = [
    { name: 'Mon', commits: 12 }, { name: 'Tue', commits: 19 },
    { name: 'Wed', commits: 15 }, { name: 'Thu', commits: 25 }, { name: 'Fri', commits: 22 }
  ]
  
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/80 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-xl">
          <p className="text-white font-bold text-sm">{`${payload[0].name || ''} : ${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-sub">Your infrastructure savings and AI performance.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium text-white transition-colors">Download Report</button>
          <button className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 border border-indigo-400/50 rounded-lg text-sm font-medium text-white shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all flex items-center gap-2">
            <Zap size={16}/> Connect Repo
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
        <StatCard title="Analyzed Commits" value="1,248" subValue="/ 7 days" trend={12} icon={GitCommitHorizontal} colorClass="bg-blue-500" gradientClass="bg-blue-500/30" />
        <StatCard title="Tests Skipped" value="342" trend={24} icon={FastForward} colorClass="bg-emerald-500" gradientClass="bg-emerald-500/30" />
        <StatCard title="Compute Saved" value="142" subValue="hrs" trend={18} icon={Clock} colorClass="bg-purple-500" gradientClass="bg-purple-500/30" />
        <StatCard title="AI Accuracy" value="99.2%" icon={Crosshair} colorClass="bg-indigo-500" gradientClass="bg-indigo-500/30" />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="Commit Flow Timeline" subtitle="Daily commit volume tracked across all connected repositories.">
            <ResponsiveContainer width="100%" height="80%">
              <AreaChart data={barData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCommits" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dx={-10} />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, fill: 'transparent' }} />
                <Area type="monotone" dataKey="commits" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorCommits)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
        <div>
          <ChartCard title="AI Decisions" subtitle="Distribution of predictive actions taken by the engine.">
            <ResponsiveContainer width="100%" height="80%">
              <PieChart>
                <Pie data={pieData} innerRadius={70} outerRadius={100} paddingAngle={2} dataKey="value" stroke="rgba(255,255,255,0.05)" strokeWidth={2}>
                  {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pt-16 mt-4 pointer-events-none">
                <span className="text-3xl font-bold text-white tracking-tight">800</span>
                <span className="text-[10px] text-[#71717a] font-bold uppercase tracking-widest mt-1">Total</span>
            </div>
          </ChartCard>
        </div>
      </div>
      
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title text-white">Latest Analysis</h2>
          <button className="text-sm font-semibold text-indigo-400 hover:text-indigo-300">View All →</button>
        </div>
        <CommitTable />
      </div>
    </div>
  )
}"""

files["src/pages/Projects.jsx"] = """import ProjectCard from '../components/ProjectCard'
import Button from '../components/Button'
import { Plus } from 'lucide-react'

export default function Projects() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Repositories</h1>
          <p className="page-sub">Manage connected GitHub repositories and webhooks</p>
        </div>
        <div className="w-full sm:w-48">
          <Button variant="primary" size="sm"><span className="flex items-center gap-2"><Plus size={16}/> Add Repository</span></Button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProjectCard name="core-service" repo="acme-corp/core-service" commits={'2.4k'} skipRate="42%" status="healthy" />
        <ProjectCard name="frontend-web" repo="acme-corp/frontend-web" commits={'1.2k'} skipRate="68%" status="healthy" />
        <ProjectCard name="payment-gateway" repo="acme-corp/payment-gateway" commits={'850'} skipRate="12%" status="failing" />
      </div>
    </div>
  )
}"""

files["src/pages/Commits.jsx"] = """import CommitTable from '../components/CommitTable'
import { Search, Filter } from 'lucide-react'

export default function Commits() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Commit History</h1>
        <p className="page-sub">Detailed breakdown of AI predictions per commit</p>
      </div>
      
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#71717a]" />
          <input type="text" placeholder="Search by SHA, message, or author..." className="w-full bg-black/40 border border-white/10 text-white placeholder-[#71717a] text-sm rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all font-medium" />
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2.5 bg-black/40 border border-white/10 rounded-xl text-sm font-medium text-white hover:bg-white/5 transition-colors flex items-center gap-2">
            <Filter size={16}/> Filter
          </button>
        </div>
      </div>
      
      <CommitTable />
    </div>
  )
}"""

files["src/pages/Analytics.jsx"] = """import ChartCard from '../components/ChartCard'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Analytics() {
  const data = [
    { name: 'Week 1', rate: 20 },
    { name: 'Week 2', rate: 25 },
    { name: 'Week 3', rate: 35 },
    { name: 'Week 4', rate: 42 },
    { name: 'Week 5', rate: 58 },
    { name: 'Week 6', rate: 65 },
  ]
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Insights</h1>
        <p className="page-sub">Analyze your CI savings and AI performance metrics</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="Overall Skip Rate Over Time" subtitle="Percentage of total tests skipped securely by the AI.">
            <ResponsiveContainer width="100%" height="85%" className="mt-4">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dx={-10} tickFormatter={(val) => `${val}%`} />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }} itemStyle={{ color: '#10b981', fontWeight: 'bold' }} />
                <Area type="monotone" dataKey="rate" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorRate)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </div>
    </div>
  )
}"""

files["src/pages/Predict.jsx"] = """import FormInput from '../components/FormInput'
import Button from '../components/Button'
import { Sparkles, BrainCircuit } from 'lucide-react'

export default function Predict() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">AI Sandbox</h1>
        <p className="page-sub">Manually simulate the prediction engine with custom parameters</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-2 glass-panel p-8 border border-white/10">
          <div className="flex items-center gap-2 mb-6 text-white pb-4 border-b border-white/5">
            <BrainCircuit size={20} className="text-indigo-400"/>
            <h3 className="font-bold">Input Variables</h3>
          </div>
          <form className="space-y-5">
            <FormInput id="files" label="Files Changed" type="number" placeholder="e.g. 5" />
            <div className="grid grid-cols-2 gap-4">
              <FormInput id="added" label="Lines Added" type="number" placeholder="120" />
              <FormInput id="deleted" label="Lines Deleted" type="number" placeholder="45" />
            </div>
            <FormInput id="failRate" label="Hist. Failure Rate (%)" type="number" placeholder="12.5" />
            <div className="pt-4 mt-8 border-t border-white/5">
              <Button type="button" variant="indigo"><span className="flex items-center gap-2"><Sparkles size={16}/> Generate Prediction</span></Button>
            </div>
          </form>
        </div>
        
        <div className="lg:col-span-3 glass-panel p-8 bg-black/40 border border-white/5 flex flex-col items-center justify-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-indigo-500/20 transition-all duration-700"></div>
          
          <div className="text-center relative z-10">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 mx-auto flex items-center justify-center mb-6">
              <Sparkles size={24} className="text-[#71717a]" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Awaiting Parameters</h3>
            <p className="text-[#a1a1aa] text-sm max-w-sm mx-auto">Fill out the variables on the left and hit generate to see how the AI weights the risk of failure.</p>
          </div>
        </div>
      </div>
    </div>
  )
}"""

files["src/pages/Logs.jsx"] = """import Button from '../components/Button'
import { TerminalSquare, BugPlay } from 'lucide-react'

export default function Logs() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Log Diagnostics</h1>
        <p className="page-sub">Paste unstructured failing CI logs and let the LLM find the needle in the haystack</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[700px]">
        <div className="glass-panel p-0 flex flex-col overflow-hidden border border-white/10">
          <div className="p-4 border-b border-white/5 bg-white/5 flex items-center gap-2 text-white">
             <TerminalSquare size={18} className="text-[#a1a1aa]"/>
             <span className="font-bold text-sm">Input Hash/Logs</span>
          </div>
          <textarea 
            className="flex-1 w-full bg-black/60 text-[#a1a1aa] p-6 font-mono text-sm resize-none focus:outline-none focus:text-white transition-colors"
            placeholder="[10:24:32] ERROR: ModuleNotFound..."
            spellCheck="false"
          />
          <div className="p-4 bg-black/40 border-t border-white/5">
            <Button variant="primary"><span className="flex items-center gap-2"><BugPlay size={16}/> Analyze Trace</span></Button>
          </div>
        </div>
        <div className="glass-panel p-8 bg-black/40 border-dashed border-2 border-white/10 flex items-center justify-center">
          <div className="text-center">
            <p className="text-[#71717a] font-medium">Diagnostic report will render here.</p>
          </div>
        </div>
      </div>
    </div>
  )
}"""

files["src/pages/Profile.jsx"] = """import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Profile() {
  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-sub">Manage your personal profile and preferences</p>
      </div>
      
      <div className="glass-panel p-8 border border-white/10 flex items-center gap-8 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px]"></div>
        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=6366f1" alt="Avatar" className="w-24 h-24 rounded-2xl border border-white/20 shadow-xl relative z-10" />
        <div className="relative z-10">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-1">Pro Developer</h2>
          <p className="text-indigo-400 font-medium mb-3">pro@company.com</p>
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-white/10 border border-white/10 text-white">Administrator</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-panel p-8 border border-white/10 space-y-6">
          <div className="mb-6 pb-4 border-b border-white/5">
            <h3 className="text-lg font-bold text-white">Personal Info</h3>
          </div>
          <FormInput id="name" label="Display Name" defaultValue="Pro Developer" />
          <FormInput id="email" label="Email Address" defaultValue="pro@company.com" />
          <div className="pt-4">
            <Button variant="secondary">Save Changes</Button>
          </div>
        </div>

        <div className="glass-panel p-8 border border-white/10 space-y-6">
           <div className="mb-6 pb-4 border-b border-white/5">
            <h3 className="text-lg font-bold text-white">Security</h3>
          </div>
          <FormInput type="password" id="cur" label="Current Password" placeholder="••••••••" />
          <FormInput type="password" id="new" label="New Password" placeholder="••••••••" />
          <div className="pt-4">
             <Button variant="indigo">Update Password</Button>
          </div>
        </div>
      </div>
    </div>
  )
}"""

for rel_path, content in files.items():
    file_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Premium UI Scaffold Complete!")
