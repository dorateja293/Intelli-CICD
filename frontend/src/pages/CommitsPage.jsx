import { Search, Filter } from 'lucide-react'
import CommitTable from '../components/CommitTable'

export default function CommitsPage() {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 fade-in">
      {/* Header and Filter */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#c9d1d9] tracking-tight">Commit History</h1>
          <p className="text-[#8b949e] text-sm mt-1">Review AI decisions on historical pipeline runs</p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8b949e]" size={16} />
            <input 
              type="text" 
              placeholder="Search commits or branches..." 
              className="w-full bg-[#161b22] border border-[#30363d] text-[#c9d1d9] text-sm rounded-lg pl-9 pr-3 py-2 outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 bg-[#161b22] border border-[#30363d] text-[#c9d1d9] rounded-lg hover:bg-[#0d1117] transition-colors shadow-sm whitespace-nowrap">
            <Filter size={16} />
            <span className="text-sm">Filter</span>
          </button>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-1 shadow-xl">
        <CommitTable />
      </div>
    </div>
  )
}
