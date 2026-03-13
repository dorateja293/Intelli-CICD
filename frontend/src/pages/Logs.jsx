import Button from '../components/Button'
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
}