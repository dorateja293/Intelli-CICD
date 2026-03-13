import { useAuth } from '../context/AuthContext'
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
}