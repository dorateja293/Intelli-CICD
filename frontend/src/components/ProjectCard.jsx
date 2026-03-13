import { Github, Play, SkipForward, AlertCircle } from 'lucide-react'
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
}