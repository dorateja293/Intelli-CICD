import CommitTable from '../components/CommitTable'
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
}